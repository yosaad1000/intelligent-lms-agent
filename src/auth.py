import json
import os
import boto3
import hashlib
import hmac
import base64
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Authentication handler for user registration, login, and token validation
    """
    
    # Handle different HTTP methods
    http_method = event.get('httpMethod', 'POST')
    
    if http_method == 'GET':
        # Handle token validation
        return handle_token_validation(event)
    elif http_method == 'POST':
        # Handle registration and login
        return handle_auth_actions(event)
    else:
        return error_response(405, 'Method not allowed')

def handle_auth_actions(event):
    """Handle POST requests for registration and login"""
    # Parse the request
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        email = body.get('email')
        password = body.get('password')
        role = body.get('role', 'student')  # Default to student
        
        if not action:
            return error_response(400, 'Missing required field: action')
        
        if action in ['register', 'login'] and (not email or not password):
            return error_response(400, 'Missing required fields: email, password')
            
    except json.JSONDecodeError:
        return error_response(400, 'Invalid JSON in request body')
    
    # Get environment variables
    user_pool_id = os.environ.get('USER_POOL_ID')
    client_id = os.environ.get('USER_POOL_CLIENT_ID')
    
    if not user_pool_id or not client_id:
        return error_response(500, 'Missing Cognito configuration')
    
    cognito = boto3.client('cognito-idp')
    
    try:
        if action == 'register':
            return handle_registration(cognito, user_pool_id, email, password, role)
        elif action == 'login':
            return handle_login(cognito, client_id, email, password)
        elif action == 'validate':
            return handle_token_validation(event)
        else:
            return error_response(400, 'Invalid action. Use "register", "login", or "validate"')
            
    except Exception as e:
        return error_response(500, f'Authentication error: {str(e)}')

def handle_token_validation(event):
    """Handle token validation requests"""
    try:
        # Get token from Authorization header
        headers = event.get('headers', {})
        # API Gateway can lowercase headers, so check both cases
        auth_header = (headers.get('Authorization') or 
                      headers.get('authorization') or 
                      headers.get('AUTHORIZATION'))
        
        if not auth_header:
            return error_response(401, 'Missing Authorization header')
        
        if not auth_header.startswith('Bearer '):
            return error_response(401, 'Invalid Authorization header format')
        
        token = auth_header.replace('Bearer ', '')
        
        # Validate token with Cognito
        cognito = boto3.client('cognito-idp')
        
        try:
            response = cognito.get_user(AccessToken=token)
            
            # Extract user information
            user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            return success_response({
                'valid': True,
                'user': {
                    'username': response['Username'],
                    'email': user_attributes.get('email'),
                    'email_verified': user_attributes.get('email_verified') == 'true',
                    'role': user_attributes.get('custom:role', 'student')
                }
            })
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
                return error_response(401, 'Invalid or expired token')
            else:
                return error_response(400, f'Token validation failed: {e.response["Error"]["Message"]}')
                
    except Exception as e:
        return error_response(500, f'Token validation error: {str(e)}')

def handle_registration(cognito, user_pool_id, email, password, role):
    """Handle user registration"""
    try:
        # Create user in Cognito (without custom role attribute for now)
        response = cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'  # Don't send welcome email for demo
        )
        
        # Set permanent password
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
        
        return success_response({
            'message': 'User registered successfully',
            'user_id': response['User']['Username'],
            'email': email,
            'role': role
        })
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            return error_response(409, 'User already exists')
        else:
            return error_response(400, f'Registration failed: {e.response["Error"]["Message"]}')

def handle_login(cognito, client_id, email, password):
    """Handle user login"""
    try:
        # Authenticate user
        response = cognito.admin_initiate_auth(
            UserPoolId=os.environ.get('USER_POOL_ID'),
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password
            }
        )
        
        # Extract tokens
        auth_result = response['AuthenticationResult']
        access_token = auth_result['AccessToken']
        id_token = auth_result['IdToken']
        refresh_token = auth_result['RefreshToken']
        
        # Get user attributes
        user_info = cognito.admin_get_user(
            UserPoolId=os.environ.get('USER_POOL_ID'),
            Username=email
        )
        
        # Set default role (custom attributes not configured yet)
        role = 'student'  # default role for all users
        
        return success_response({
            'message': 'Login successful',
            'tokens': {
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token
            },
            'user': {
                'email': email,
                'role': role,
                'user_id': user_info['Username']
            }
        })
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
            return error_response(401, 'Invalid email or password')
        else:
            return error_response(400, f'Login failed: {e.response["Error"]["Message"]}')

def success_response(data):
    """Return a successful response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data)
    }

def error_response(status_code, message):
    """Return an error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({'error': message})
    }
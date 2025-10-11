#!/usr/bin/env python3
"""
Update API Gateway to add token validation endpoint
"""

import boto3
import json
from botocore.exceptions import ClientError

def get_api_config():
    """Load API configuration"""
    try:
        with open('api-config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ api-config.json not found. Run create_api_gateway.py first.")
        return None

def get_resource_by_path(api_id, path):
    """Get resource ID by path"""
    apigateway = boto3.client('apigateway')
    
    try:
        resources = apigateway.get_resources(restApiId=api_id)
        
        for resource in resources['items']:
            if resource['path'] == path:
                return resource['id']
        
        return None
        
    except ClientError as e:
        print(f"❌ Failed to get resources: {e}")
        return None

def create_resource(api_id, parent_id, path_part):
    """Create a new resource"""
    print(f"📁 Creating resource: /{path_part}")
    
    apigateway = boto3.client('apigateway')
    
    try:
        resource_response = apigateway.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        
        resource_id = resource_response['id']
        print(f"✅ Resource created: {resource_id}")
        return resource_id
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            print(f"ℹ️ Resource /{path_part} already exists")
            # Get existing resource ID
            resources = apigateway.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == path_part:
                    return resource['id']
        else:
            print(f"❌ Resource creation failed: {e}")
        return None

def create_method(api_id, resource_id, http_method, lambda_function_name):
    """Create a method for a resource"""
    print(f"🔧 Creating {http_method} method...")
    
    apigateway = boto3.client('apigateway')
    lambda_client = boto3.client('lambda')
    
    # Get Lambda function ARN
    try:
        lambda_response = lambda_client.get_function(FunctionName=lambda_function_name)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
    except ClientError as e:
        print(f"❌ Failed to get Lambda function: {e}")
        return False
    
    # Create method
    try:
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType='NONE'
        )
        print(f"✅ {http_method} method created")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            print(f"ℹ️ {http_method} method already exists")
        else:
            print(f"❌ Method creation failed: {e}")
            return False
    
    # Create integration
    try:
        region = 'us-east-1'
        integration_uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri
        )
        print(f"✅ Integration created")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            print(f"ℹ️ Integration already exists")
        else:
            print(f"❌ Integration creation failed: {e}")
            return False
    
    # Add Lambda permission for API Gateway
    try:
        account_id = '145023137830'
        statement_id = f"apigateway-{api_id}-{resource_id}-{http_method}"
        source_arn = f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*/{http_method}/*"
        
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=source_arn
        )
        print(f"✅ Lambda permission added")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"ℹ️ Lambda permission already exists")
        else:
            print(f"❌ Lambda permission failed: {e}")
            return False
    
    return True

def enable_cors(api_id, resource_id):
    """Enable CORS for a resource"""
    print("🌍 Enabling CORS...")
    
    apigateway = boto3.client('apigateway')
    
    try:
        # Create OPTIONS method for CORS
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # Create mock integration for OPTIONS
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # Create method response for OPTIONS
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False
            }
        )
        
        # Create integration response for OPTIONS
        apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
        
        print("✅ CORS enabled")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            print("ℹ️ CORS already enabled")
            return True
        else:
            print(f"❌ CORS setup failed: {e}")
            return False

def deploy_api(api_id, stage_name='dev'):
    """Deploy the API to a stage"""
    print(f"🚀 Deploying API to {stage_name} stage...")
    
    apigateway = boto3.client('apigateway')
    
    try:
        deployment_response = apigateway.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description=f'Updated deployment with token validation endpoint'
        )
        
        deployment_id = deployment_response['id']
        print(f"✅ API deployed: {deployment_id}")
        
        return True
        
    except ClientError as e:
        print(f"❌ API deployment failed: {e}")
        return False

def main():
    print("🔄 Updating API Gateway with token validation endpoint")
    print("=" * 50)
    
    # Load existing API configuration
    api_config = get_api_config()
    if not api_config:
        return False
    
    api_id = api_config['api_id']
    print(f"📋 Using API ID: {api_id}")
    
    try:
        # Get auth resource ID
        auth_resource_id = get_resource_by_path(api_id, '/auth')
        if not auth_resource_id:
            print("❌ /auth resource not found")
            return False
        
        print(f"📋 Auth resource ID: {auth_resource_id}")
        
        # Create /auth/validate resource
        validate_resource_id = create_resource(api_id, auth_resource_id, 'validate')
        if not validate_resource_id:
            return False
        
        # Create GET method for /auth/validate
        if not create_method(api_id, validate_resource_id, 'GET', 'lms-auth'):
            return False
        
        # Enable CORS for /auth/validate
        enable_cors(api_id, validate_resource_id)
        
        # Deploy API
        if not deploy_api(api_id):
            return False
        
        # Update API configuration
        api_config['validate_endpoint'] = f"{api_config['api_url']}/auth/validate"
        
        with open('api-config.json', 'w') as f:
            json.dump(api_config, f, indent=2)
        
        print("\n" + "=" * 50)
        print("🎉 API Gateway updated successfully!")
        print(f"✅ Token validation endpoint: {api_config['validate_endpoint']}")
        print("✅ Configuration updated in api-config.json")
        print("\n📋 Ready for testing!")
        
        return True
        
    except Exception as e:
        print(f"❌ API Gateway update failed: {e}")
        return False

if __name__ == "__main__":
    main()
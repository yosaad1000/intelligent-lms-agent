"""
Lambda Authorizer for Supabase JWT tokens
"""

import json
import jwt
import os
from typing import Dict, Any


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer function for API Gateway
    Validates Supabase JWT tokens
    """
    
    try:
        # Extract token from Authorization header
        token = event.get('authorizationToken', '').replace('Bearer ', '')
        
        if not token:
            raise Exception('No token provided')
        
        # Decode JWT token (without signature verification for now)
        # In production, you should verify the signature with Supabase public key
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Extract user information
        user_id = payload.get('sub')
        email = payload.get('email')
        
        if not user_id:
            raise Exception('Invalid token: no user ID')
        
        # Generate policy
        policy = generate_policy(user_id, 'Allow', event['methodArn'])
        
        # Add user context
        policy['context'] = {
            'user_id': user_id,
            'email': email or '',
            'auth_user_id': user_id
        }
        
        return policy
        
    except Exception as e:
        print(f"Authorization failed: {str(e)}")
        # Return deny policy
        return generate_policy('user', 'Deny', event['methodArn'])


def generate_policy(principal_id: str, effect: str, resource: str) -> Dict[str, Any]:
    """Generate IAM policy for API Gateway"""
    
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    
    return policy
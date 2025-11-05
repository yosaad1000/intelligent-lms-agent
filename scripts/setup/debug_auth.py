#!/usr/bin/env python3
"""
Debug Cognito authentication
"""

import boto3
import json
from botocore.exceptions import ClientError

def debug_cognito():
    print("🔍 Debugging Cognito Authentication")
    print("=" * 40)
    
    # Configuration
    user_pool_id = "us-east-1_ux07rphza"
    client_id = "2vk3cuqvnl1bncnivl80dof4h1"
    test_email = "teststudent@example.com"
    test_password = "TestPass123"
    
    cognito = boto3.client('cognito-idp')
    
    # Check user status first
    print("👤 Checking user status...")
    try:
        user_info = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=test_email
        )
        
        print(f"✅ User found:")
        print(f"   Username: {user_info['Username']}")
        print(f"   Status: {user_info['UserStatus']}")
        print(f"   Enabled: {user_info['Enabled']}")
        
        print("   Attributes:")
        for attr in user_info['UserAttributes']:
            print(f"     - {attr['Name']}: {attr['Value']}")
            
    except ClientError as e:
        print(f"❌ User check failed: {e}")
        return
    
    # Try authentication
    print("\n🔑 Attempting authentication...")
    try:
        response = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': test_email,
                'PASSWORD': test_password
            }
        )
        
        print("✅ Authentication response received:")
        print(f"Response keys: {list(response.keys())}")
        
        if 'AuthenticationResult' in response:
            tokens = response['AuthenticationResult']
            print("✅ Tokens received successfully!")
            print(f"   Access token: {tokens['AccessToken'][:50]}...")
        elif 'ChallengeName' in response:
            print(f"⚠️ Challenge required: {response['ChallengeName']}")
            print(f"Challenge parameters: {response.get('ChallengeParameters', {})}")
        else:
            print("❓ Unexpected response structure:")
            print(json.dumps(response, indent=2, default=str))
        
    except ClientError as e:
        print(f"❌ Authentication failed: {e}")
        print(f"Error code: {e.response['Error']['Code']}")
        print(f"Error message: {e.response['Error']['Message']}")

if __name__ == "__main__":
    debug_cognito()
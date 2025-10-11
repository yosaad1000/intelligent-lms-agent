#!/usr/bin/env python3
"""
Test Cognito authentication functionality
"""

import boto3
import json
from botocore.exceptions import ClientError

def test_cognito_auth():
    print("🔐 Testing Cognito Authentication")
    print("=" * 40)
    
    # Configuration
    user_pool_id = "us-east-1_ux07rphza"
    client_id = "2vk3cuqvnl1bncnivl80dof4h1"
    test_email = "test@example.com"
    test_password = "TestPass123"
    
    cognito = boto3.client('cognito-idp')
    
    # Test 1: Create a test user
    print("📝 Creating test user...")
    try:
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=test_email,
            UserAttributes=[
                {'Name': 'email', 'Value': test_email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'custom:role', 'Value': 'student'}
            ],
            TemporaryPassword=test_password,
            MessageAction='SUPPRESS'
        )
        
        # Set permanent password
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=test_email,
            Password=test_password,
            Permanent=True
        )
        
        print("✅ Test user created successfully")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            print("ℹ️ Test user already exists, proceeding...")
        else:
            print(f"❌ User creation failed: {e}")
            return False
    
    # Test 2: Login with the test user
    print("\n🔑 Testing login...")
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
        
        tokens = response['AuthenticationResult']
        access_token = tokens['AccessToken']
        id_token = tokens['IdToken']
        
        print("✅ Login successful!")
        print(f"   Access token (first 50 chars): {access_token[:50]}...")
        print(f"   ID token (first 50 chars): {id_token[:50]}...")
        
        # Test 3: Get user info using access token
        print("\n👤 Getting user information...")
        user_info = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=test_email
        )
        
        print("✅ User info retrieved:")
        print(f"   Username: {user_info['Username']}")
        print(f"   Status: {user_info['UserStatus']}")
        
        # Extract custom attributes
        for attr in user_info['UserAttributes']:
            if attr['Name'] == 'custom:role':
                print(f"   Role: {attr['Value']}")
            elif attr['Name'] == 'email':
                print(f"   Email: {attr['Value']}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    print("🎓 Intelligent LMS - Authentication Test")
    print("=" * 50)
    
    success = test_cognito_auth()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Authentication system is working correctly!")
        print("✅ Ready for API Gateway integration")
    else:
        print("⚠️ Authentication system needs attention")

if __name__ == "__main__":
    main()
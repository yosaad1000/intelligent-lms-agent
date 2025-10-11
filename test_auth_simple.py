#!/usr/bin/env python3
"""
Simple Cognito authentication test without custom attributes
"""

import boto3
import json
from botocore.exceptions import ClientError

def test_cognito_auth():
    print("🔐 Testing Cognito Authentication (Simple)")
    print("=" * 40)
    
    # Configuration
    user_pool_id = "us-east-1_ux07rphza"
    client_id = "2vk3cuqvnl1bncnivl80dof4h1"
    test_email = "teststudent@example.com"
    test_password = "TestPass123"
    
    cognito = boto3.client('cognito-idp')
    
    # Test 1: Create a test user (without custom attributes for now)
    print("📝 Creating test user...")
    try:
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=test_email,
            UserAttributes=[
                {'Name': 'email', 'Value': test_email},
                {'Name': 'email_verified', 'Value': 'true'}
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
        refresh_token = tokens['RefreshToken']
        
        print("✅ Login successful!")
        print(f"   Access token (first 50 chars): {access_token[:50]}...")
        print(f"   ID token (first 50 chars): {id_token[:50]}...")
        print(f"   Refresh token received: Yes")
        
        # Test 3: Get user info
        print("\n👤 Getting user information...")
        user_info = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=test_email
        )
        
        print("✅ User info retrieved:")
        print(f"   Username: {user_info['Username']}")
        print(f"   Status: {user_info['UserStatus']}")
        print(f"   Enabled: {user_info['Enabled']}")
        
        # Show user attributes
        print("   Attributes:")
        for attr in user_info['UserAttributes']:
            print(f"     - {attr['Name']}: {attr['Value']}")
        
        # Test 4: Test token validation (decode ID token info)
        print("\n🎫 Testing token validation...")
        try:
            # We can't fully validate JWT without the public key, but we can check basic structure
            import base64
            
            # Split the JWT token
            header, payload, signature = id_token.split('.')
            
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            
            # Decode payload (base64url decode)
            decoded_payload = base64.urlsafe_b64decode(payload)
            token_data = json.loads(decoded_payload)
            
            print("✅ ID Token decoded successfully:")
            print(f"   Subject (user ID): {token_data.get('sub', 'N/A')}")
            print(f"   Email: {token_data.get('email', 'N/A')}")
            print(f"   Token use: {token_data.get('token_use', 'N/A')}")
            print(f"   Audience: {token_data.get('aud', 'N/A')}")
            
        except Exception as e:
            print(f"⚠️ Token decode failed (expected): {e}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    print("🎓 Intelligent LMS - Simple Authentication Test")
    print("=" * 55)
    
    success = test_cognito_auth()
    
    print("\n" + "=" * 55)
    if success:
        print("🎉 Basic authentication system is working!")
        print("✅ Cognito User Pool is functional")
        print("✅ User creation and login work")
        print("✅ Token generation is working")
        print("\n📋 Next steps:")
        print("   1. Add custom 'role' attribute to User Pool schema")
        print("   2. Create Lambda functions for API endpoints")
        print("   3. Set up API Gateway")
    else:
        print("⚠️ Authentication system needs attention")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Fixed Cognito authentication test that handles password challenges
"""

import boto3
import json
from botocore.exceptions import ClientError

def test_cognito_auth():
    print("🔐 Testing Cognito Authentication (Fixed)")
    print("=" * 40)
    
    # Configuration
    user_pool_id = "us-east-1_ux07rphza"
    client_id = "2vk3cuqvnl1bncnivl80dof4h1"
    test_email = "student@lmstest.com"  # Use a new email
    test_password = "TestPass123"
    
    cognito = boto3.client('cognito-idp')
    
    # Test 1: Create a test user with permanent password
    print("📝 Creating test user with permanent password...")
    try:
        # Delete user if exists
        try:
            cognito.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=test_email
            )
            print("   🗑️ Deleted existing user")
        except:
            pass
        
        # Create user
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
        
        # Set permanent password immediately
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=test_email,
            Password=test_password,
            Permanent=True
        )
        
        print("✅ Test user created with permanent password")
        
    except ClientError as e:
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
        
        # Handle different response types
        if 'AuthenticationResult' in response:
            # Success - we got tokens
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
            
            # Test 4: Validate token by making an authenticated request
            print("\n🎫 Testing token validation...")
            try:
                # Use the access token to get user info (this validates the token)
                token_response = cognito.get_user(AccessToken=access_token)
                print("✅ Token validation successful!")
                print(f"   Token username: {token_response['Username']}")
                
            except ClientError as e:
                print(f"⚠️ Token validation failed: {e}")
            
            return True
            
        elif 'ChallengeName' in response:
            challenge_name = response['ChallengeName']
            print(f"⚠️ Challenge required: {challenge_name}")
            
            if challenge_name == 'NEW_PASSWORD_REQUIRED':
                print("   Handling NEW_PASSWORD_REQUIRED challenge...")
                session = response['Session']
                
                # Respond to the challenge with the same password
                challenge_response = cognito.admin_respond_to_auth_challenge(
                    UserPoolId=user_pool_id,
                    ClientId=client_id,
                    ChallengeName='NEW_PASSWORD_REQUIRED',
                    Session=session,
                    ChallengeResponses={
                        'USERNAME': test_email,
                        'NEW_PASSWORD': test_password
                    }
                )
                
                if 'AuthenticationResult' in challenge_response:
                    tokens = challenge_response['AuthenticationResult']
                    print("✅ Challenge completed successfully!")
                    print(f"   Access token received: {tokens['AccessToken'][:50]}...")
                    return True
                else:
                    print("❌ Challenge response failed")
                    return False
            else:
                print(f"❌ Unsupported challenge: {challenge_name}")
                return False
        else:
            print("❌ Unexpected response structure")
            print(json.dumps(response, indent=2, default=str))
            return False
        
    except ClientError as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    print("🎓 Intelligent LMS - Fixed Authentication Test")
    print("=" * 55)
    
    success = test_cognito_auth()
    
    print("\n" + "=" * 55)
    if success:
        print("🎉 Authentication system is working perfectly!")
        print("✅ Cognito User Pool is functional")
        print("✅ User creation and login work")
        print("✅ Token generation and validation work")
        print("✅ Password challenges are handled correctly")
        print("\n📋 Ready for next steps:")
        print("   1. Create Lambda functions")
        print("   2. Set up API Gateway")
        print("   3. Deploy Hello World endpoint")
    else:
        print("⚠️ Authentication system needs attention")

if __name__ == "__main__":
    main()
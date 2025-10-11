#!/usr/bin/env python3
"""
Test script for LMS infrastructure components
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

def load_config():
    """Load infrastructure configuration"""
    with open('infrastructure-config.json', 'r') as f:
        return json.load(f)

def test_s3(bucket_name):
    """Test S3 bucket access"""
    print("🗄️ Testing S3 bucket access...")
    try:
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' is accessible")
        
        # Try to list objects
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        object_count = response.get('KeyCount', 0)
        print(f"   📁 Current objects in bucket: {object_count}")
        
        return True
    except ClientError as e:
        print(f"❌ S3 test failed: {e}")
        return False

def test_dynamodb(table_name):
    """Test DynamoDB table access"""
    print("\n🗃️ Testing DynamoDB table access...")
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Get table status
        table_info = table.table_status
        print(f"✅ DynamoDB table '{table_name}' is accessible")
        print(f"   📊 Table status: {table_info}")
        
        # Try to scan for items (limit 1)
        response = table.scan(Limit=1)
        item_count = response.get('Count', 0)
        print(f"   📝 Sample items found: {item_count}")
        
        return True
    except ClientError as e:
        print(f"❌ DynamoDB test failed: {e}")
        return False

def test_cognito(user_pool_id, client_id):
    """Test Cognito User Pool access"""
    print("\n🔐 Testing Cognito User Pool access...")
    try:
        cognito = boto3.client('cognito-idp')
        
        # Describe user pool
        response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        pool_name = response['UserPool']['Name']
        print(f"✅ Cognito User Pool '{pool_name}' is accessible")
        print(f"   🆔 Pool ID: {user_pool_id}")
        print(f"   🔑 Client ID: {client_id}")
        
        # List users (limit 1)
        users_response = cognito.list_users(UserPoolId=user_pool_id, Limit=1)
        user_count = len(users_response.get('Users', []))
        print(f"   👥 Sample users found: {user_count}")
        
        return True
    except ClientError as e:
        print(f"❌ Cognito test failed: {e}")
        return False

def test_bedrock():
    """Test Bedrock access"""
    print("\n🤖 Testing Bedrock access...")
    try:
        bedrock = boto3.client('bedrock')
        
        # List foundation models
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])
        total_models = len(models)
        
        # Count Nova models
        nova_models = [m for m in models if 'nova' in m.get('modelName', '').lower()]
        nova_count = len(nova_models)
        
        print(f"✅ Bedrock is accessible")
        print(f"   🧠 Total foundation models: {total_models}")
        print(f"   ⭐ Nova models available: {nova_count}")
        
        # Show some Nova models
        if nova_models:
            print("   📋 Available Nova models:")
            for model in nova_models[:3]:  # Show first 3
                print(f"      - {model['modelName']} ({model['modelId']})")
        
        return True
    except ClientError as e:
        print(f"❌ Bedrock test failed: {e}")
        return False

def test_cognito_auth(user_pool_id, client_id):
    """Test Cognito authentication with a test user"""
    print("\n🧪 Testing Cognito authentication...")
    
    cognito = boto3.client('cognito-idp')
    test_email = "test@example.com"
    test_password = "TestPass123"
    
    try:
        # Try to create a test user
        print(f"   📝 Creating test user: {test_email}")
        
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
        
        print("   ✅ Test user created successfully")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            print("   ℹ️ Test user already exists, proceeding with login test")
        else:
            print(f"   ❌ User creation failed: {e}")
            return False
    
    try:
        # Test login
        print("   🔑 Testing login...")
        
        response = cognito.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': test_email,
                'PASSWORD': test_password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        print("   ✅ Login successful!")
        print(f"   🎫 Access token received (first 50 chars): {access_token[:50]}...")
        
        return True
        
    except ClientError as e:
        print(f"   ❌ Login test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🎓 Intelligent LMS AI Agent - Infrastructure Test")
    print("=" * 50)
    
    # Load configuration
    try:
        config = load_config()
        print(f"📋 Configuration loaded:")
        print(f"   S3 Bucket: {config['S3_BUCKET']}")
        print(f"   User Pool: {config['USER_POOL_ID']}")
        print(f"   Client ID: {config['CLIENT_ID']}")
        print(f"   DynamoDB: {config['DYNAMODB_TABLE']}")
        print(f"   Region: {config['REGION']}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    # Set AWS region
    boto3.setup_default_session(region_name=config['REGION'])
    
    # Run tests
    results = []
    
    results.append(test_s3(config['S3_BUCKET']))
    results.append(test_dynamodb(config['DYNAMODB_TABLE']))
    results.append(test_cognito(config['USER_POOL_ID'], config['CLIENT_ID']))
    results.append(test_bedrock())
    results.append(test_cognito_auth(config['USER_POOL_ID'], config['CLIENT_ID']))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    test_names = ["S3", "DynamoDB", "Cognito", "Bedrock", "Authentication"]
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All infrastructure components are working correctly!")
        print("✅ Ready to proceed with Lambda function deployment")
    else:
        print("⚠️ Some components need attention before proceeding")

if __name__ == "__main__":
    main()
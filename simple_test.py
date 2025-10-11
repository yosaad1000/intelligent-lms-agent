#!/usr/bin/env python3
"""
Simple test script for AWS infrastructure
"""

import boto3
import json
import os

def main():
    print("🎓 Simple Infrastructure Test")
    print("=" * 40)
    
    # Test basic AWS connectivity
    try:
        # Test STS (Security Token Service) - basic AWS connectivity
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS Connection successful!")
        print(f"   Account: {identity['Account']}")
        print(f"   User: {identity['Arn']}")
    except Exception as e:
        print(f"❌ AWS Connection failed: {e}")
        return
    
    # Test S3
    try:
        s3 = boto3.client('s3')
        bucket_name = "lms-files-145023137830-us-east-1"
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' accessible")
    except Exception as e:
        print(f"❌ S3 test failed: {e}")
    
    # Test DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-data')
        table_status = table.table_status
        print(f"✅ DynamoDB table 'lms-data' accessible (Status: {table_status})")
    except Exception as e:
        print(f"❌ DynamoDB test failed: {e}")
    
    # Test Cognito
    try:
        cognito = boto3.client('cognito-idp')
        user_pool_id = "us-east-1_ux07rphza"
        response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        pool_name = response['UserPool']['Name']
        print(f"✅ Cognito User Pool '{pool_name}' accessible")
    except Exception as e:
        print(f"❌ Cognito test failed: {e}")
    
    # Test Bedrock
    try:
        bedrock = boto3.client('bedrock')
        models = bedrock.list_foundation_models()
        model_count = len(models['modelSummaries'])
        print(f"✅ Bedrock accessible ({model_count} models available)")
    except Exception as e:
        print(f"❌ Bedrock test failed: {e}")
    
    print("\n🎯 Basic infrastructure test completed!")

if __name__ == "__main__":
    main()
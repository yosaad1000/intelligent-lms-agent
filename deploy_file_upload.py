#!/usr/bin/env python3
"""
Deploy file upload Lambda function directly
"""

import boto3
import json
import zipfile
import os
from io import BytesIO

def create_lambda_zip():
    """Create a ZIP file with the Lambda function code"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the file upload Lambda function
        zip_file.write('src/file_upload.py', 'file_upload.py')
    
    zip_buffer.seek(0)
    return zip_buffer.read()

def deploy_lambda_function():
    """Deploy the file upload Lambda function"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Function configuration
    function_name = 'lms-file-upload'
    
    # Create ZIP package
    zip_content = create_lambda_zip()
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"Updated existing Lambda function: {function_name}")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function if it doesn't exist
        print(f"Creating new Lambda function: {function_name}")
        
        # Get IAM role ARN (assuming it exists from previous deployment)
        iam_client = boto3.client('iam', region_name='us-east-1')
        
        try:
            role_response = iam_client.get_role(RoleName='lms-stack-LambdaExecutionRole-*')
            role_arn = role_response['Role']['Arn']
        except:
            # Create a basic execution role
            role_arn = create_lambda_execution_role()
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
            Handler='file_upload.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='File upload handler for LMS',
            Timeout=30,
            Environment={
                'Variables': {
                    'S3_BUCKET': 'lms-files-145023137830-us-east-1',
                    'DYNAMODB_TABLE': 'lms-data',
                    'USER_POOL_ID': get_user_pool_id(),
                    'USER_POOL_CLIENT_ID': get_user_pool_client_id()
                }
            }
        )
    
    return response

def create_lambda_execution_role():
    """Create a basic Lambda execution role"""
    iam_client = boto3.client('iam', region_name='us-east-1')
    
    role_name = 'lms-lambda-execution-role'
    
    # Trust policy for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Create role
    try:
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Execution role for LMS Lambda functions'
        )
        
        # Attach basic execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Create custom policy for S3 and DynamoDB access
        custom_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "arn:aws:s3:::lms-files-145023137830-us-east-1",
                        "arn:aws:s3:::lms-files-145023137830-us-east-1/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem"
                    ],
                    "Resource": "arn:aws:dynamodb:us-east-1:145023137830:table/lms-data"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "cognito-idp:GetUser"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='LMSLambdaPolicy',
            PolicyDocument=json.dumps(custom_policy)
        )
        
        return role_response['Role']['Arn']
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        # Role already exists, get its ARN
        role_response = iam_client.get_role(RoleName=role_name)
        return role_response['Role']['Arn']

def get_user_pool_id():
    """Get Cognito User Pool ID"""
    cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        response = cognito_client.list_user_pools(MaxResults=50)
        for pool in response['UserPools']:
            if 'lms' in pool['Name'].lower():
                return pool['Id']
    except:
        pass
    
    return 'us-east-1_PLACEHOLDER'  # Placeholder if not found

def get_user_pool_client_id():
    """Get Cognito User Pool Client ID"""
    # This would need the User Pool ID first
    return 'PLACEHOLDER_CLIENT_ID'

def create_s3_bucket():
    """Create S3 bucket if it doesn't exist"""
    s3_client = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'lms-files-145023137830-us-east-1'
    
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"Created S3 bucket: {bucket_name}")
        
        # Enable server-side encryption
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }
                ]
            }
        )
        
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"S3 bucket already exists: {bucket_name}")
    except Exception as e:
        print(f"Error creating S3 bucket: {e}")

def create_dynamodb_table():
    """Create DynamoDB table if it doesn't exist"""
    dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
    table_name = 'lms-data'
    
    try:
        response = dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Created DynamoDB table: {table_name}")
        
    except dynamodb_client.exceptions.ResourceInUseException:
        print(f"DynamoDB table already exists: {table_name}")
    except Exception as e:
        print(f"Error creating DynamoDB table: {e}")

if __name__ == '__main__':
    print("Deploying file upload functionality...")
    
    # Create required resources
    create_s3_bucket()
    create_dynamodb_table()
    
    # Deploy Lambda function
    response = deploy_lambda_function()
    print(f"Lambda function deployed successfully!")
    print(f"Function ARN: {response.get('FunctionArn', 'N/A')}")
    
    print("\nNext steps:")
    print("1. Add API Gateway integration for /files endpoint")
    print("2. Test file upload functionality")
    print("3. Verify S3 and DynamoDB integration")
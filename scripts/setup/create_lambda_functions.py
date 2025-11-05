#!/usr/bin/env python3
"""
Create Lambda functions for the LMS API
"""

import boto3
import json
import zipfile
import os
from botocore.exceptions import ClientError

def create_lambda_execution_role():
    """Create IAM role for Lambda execution"""
    print("🔐 Creating Lambda execution role...")
    
    iam = boto3.client('iam')
    
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
    
    # Lambda policy for our services
    lambda_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": "arn:aws:s3:::lms-files-145023137830-us-east-1/*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:UpdateItem",
                    "dynamodb:Scan"
                ],
                "Resource": "arn:aws:dynamodb:us-east-1:145023137830:table/lms-data"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminSetUserPassword",
                    "cognito-idp:AdminInitiateAuth",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminRespondToAuthChallenge",
                    "cognito-idp:GetUser"
                ],
                "Resource": "arn:aws:cognito-idp:us-east-1:145023137830:userpool/us-east-1_ux07rphza"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeAgent",
                    "bedrock:ListFoundationModels"
                ],
                "Resource": "*"
            }
        ]
    }
    
    role_name = "LMSLambdaExecutionRole"
    
    try:
        # Try to get existing role
        role_response = iam.get_role(RoleName=role_name)
        role_arn = role_response['Role']['Arn']
        print(f"✅ Using existing role: {role_arn}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            # Create the role
            role_response = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Execution role for LMS Lambda functions'
            )
            role_arn = role_response['Role']['Arn']
            print(f"✅ Created new role: {role_arn}")
            
            # Attach basic execution policy
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Create and attach custom policy
            policy_name = "LMSLambdaCustomPolicy"
            try:
                iam.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(lambda_policy),
                    Description='Custom policy for LMS Lambda functions'
                )
                
                iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=f'arn:aws:iam::145023137830:policy/{policy_name}'
                )
                print("✅ Custom policy attached")
                
            except ClientError as policy_error:
                if policy_error.response['Error']['Code'] == 'EntityAlreadyExists':
                    # Policy exists, just attach it
                    iam.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=f'arn:aws:iam::145023137830:policy/{policy_name}'
                    )
                    print("✅ Existing custom policy attached")
                else:
                    print(f"⚠️ Policy creation failed: {policy_error}")
            
        else:
            raise e
    
    return role_arn

def create_deployment_package():
    """Create deployment package for Lambda functions"""
    print("📦 Creating deployment package...")
    
    # Create a temporary directory for the package
    package_dir = "lambda_package"
    if os.path.exists(package_dir):
        import shutil
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy source files
    import shutil
    shutil.copy("src/hello_world.py", package_dir)
    shutil.copy("src/auth.py", package_dir)
    
    # Create zip file
    zip_file = "lambda_deployment.zip"
    if os.path.exists(zip_file):
        os.remove(zip_file)
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    # Clean up
    shutil.rmtree(package_dir)
    
    print(f"✅ Deployment package created: {zip_file}")
    return zip_file

def create_lambda_function(function_name, handler, role_arn, zip_file, description):
    """Create a Lambda function"""
    print(f"🚀 Creating Lambda function: {function_name}")
    
    lambda_client = boto3.client('lambda')
    
    # Environment variables
    environment = {
        'Variables': {
            'USER_POOL_ID': 'us-east-1_ux07rphza',
            'USER_POOL_CLIENT_ID': '2vk3cuqvnl1bncnivl80dof4h1',
            'S3_BUCKET': 'lms-files-145023137830-us-east-1',
            'DYNAMODB_TABLE': 'lms-data',
            'REGION': 'us-east-1'
        }
    }
    
    try:
        # Try to get existing function
        lambda_client.get_function(FunctionName=function_name)
        
        # Update existing function
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Role=role_arn,
            Handler=handler,
            Runtime='python3.9',
            Timeout=30,
            Environment=environment
        )
        
        print(f"✅ Updated existing function: {function_name}")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create new function
            with open(zip_file, 'rb') as f:
                zip_content = f.read()
            
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler=handler,
                Code={'ZipFile': zip_content},
                Description=description,
                Timeout=30,
                Environment=environment
            )
            
            print(f"✅ Created new function: {function_name}")
            print(f"   ARN: {response['FunctionArn']}")
        else:
            raise e

def main():
    print("🎓 Creating Lambda Functions for LMS")
    print("=" * 45)
    
    try:
        # Step 1: Create IAM role
        role_arn = create_lambda_execution_role()
        
        # Wait a moment for role to propagate
        print("⏳ Waiting for role to propagate...")
        import time
        time.sleep(10)
        
        # Step 2: Create deployment package
        zip_file = create_deployment_package()
        
        # Step 3: Create Lambda functions
        create_lambda_function(
            function_name="lms-hello-world",
            handler="hello_world.lambda_handler",
            role_arn=role_arn,
            zip_file=zip_file,
            description="Hello World function for LMS API testing"
        )
        
        create_lambda_function(
            function_name="lms-auth",
            handler="auth.lambda_handler",
            role_arn=role_arn,
            zip_file=zip_file,
            description="Authentication function for LMS API"
        )
        
        # Clean up
        os.remove(zip_file)
        
        print("\n" + "=" * 45)
        print("🎉 Lambda functions created successfully!")
        print("✅ lms-hello-world function ready")
        print("✅ lms-auth function ready")
        print("✅ IAM role configured with proper permissions")
        print("\n📋 Next step: Create API Gateway")
        
    except Exception as e:
        print(f"❌ Lambda creation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
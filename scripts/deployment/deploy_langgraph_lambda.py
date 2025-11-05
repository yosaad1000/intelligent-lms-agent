#!/usr/bin/env python3
"""
Deploy LangGraph Lambda Function
Deploys the LangChain + LangGraph agent Lambda function with dependencies
"""

import os
import sys
import json
import boto3
import zipfile
import tempfile
import shutil
import subprocess
from pathlib import Path

# Configuration
LAMBDA_FUNCTION_NAME = "lms-langgraph-chat"
LAMBDA_RUNTIME = "python3.9"
LAMBDA_TIMEOUT = 300  # 5 minutes
LAMBDA_MEMORY = 1024  # MB
LAMBDA_HANDLER = "langgraph_chat_handler.lambda_handler"

# Environment variables for Lambda
LAMBDA_ENV_VARS = {
    'AWS_DEFAULT_REGION': 'us-east-1',
    'BEDROCK_MODEL_ID': 'amazon.nova-micro-v1:0',
    'BEDROCK_EMBEDDING_MODEL_ID': 'amazon.titan-embed-text-v1',
    'BEDROCK_MAX_RETRIES': '3',
    'BEDROCK_RETRY_DELAY': '1.0',
    'BEDROCK_TIMEOUT_SECONDS': '30',
    'DYNAMODB_TABLE_PREFIX': 'lms',
    'CHAT_HISTORY_TABLE': 'lms-chat-memory',
    'DEBUG': 'True',
    'LOG_LEVEL': 'INFO'
}

def create_deployment_package():
    """Create Lambda deployment package with LangChain dependencies"""
    
    print("🚀 Creating LangGraph Lambda deployment package...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "package"
        package_dir.mkdir()
        
        # Install dependencies
        print("📦 Installing LangChain + LangGraph dependencies...")
        
        # Create requirements file for Lambda
        lambda_requirements = """
langchain>=0.1.0
langchain-aws>=0.1.0
langchain-community>=0.0.20
langgraph>=0.0.40
langsmith>=0.0.80
boto3>=1.40.0
botocore>=1.40.0
pinecone>=5.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
"""
        
        requirements_file = package_dir / "requirements.txt"
        requirements_file.write_text(lambda_requirements.strip())
        
        # Install packages
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", str(requirements_file),
            "-t", str(package_dir),
            "--no-deps"  # Avoid conflicts
        ], check=True)
        
        # Copy source code
        print("📁 Copying source code...")
        
        # Copy shared modules
        shared_src = Path("src/shared")
        shared_dst = package_dir / "shared"
        if shared_src.exists():
            shutil.copytree(shared_src, shared_dst)
        
        # Copy chat modules
        chat_src = Path("src/chat")
        chat_dst = package_dir / "chat"
        if chat_src.exists():
            shutil.copytree(chat_src, chat_dst)
        
        # Copy file processing modules
        file_processing_src = Path("src/file_processing")
        file_processing_dst = package_dir / "file_processing"
        if file_processing_src.exists():
            shutil.copytree(file_processing_src, file_processing_dst)
        
        # Copy the main handler
        handler_src = Path("src/chat/langgraph_chat_handler.py")
        handler_dst = package_dir / "langgraph_chat_handler.py"
        if handler_src.exists():
            shutil.copy2(handler_src, handler_dst)
        
        # Create deployment zip
        print("🗜️ Creating deployment ZIP...")
        zip_path = Path("langgraph-lambda-deployment.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(package_dir)
                    zipf.write(file_path, arc_name)
        
        print(f"✅ Deployment package created: {zip_path}")
        return zip_path

def deploy_lambda_function(zip_path):
    """Deploy Lambda function to AWS"""
    
    print("☁️ Deploying to AWS Lambda...")
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda')
    iam_client = boto3.client('iam')
    
    # Create IAM role for Lambda
    role_name = f"{LAMBDA_FUNCTION_NAME}-role"
    
    try:
        # Check if role exists
        iam_client.get_role(RoleName=role_name)
        print(f"✅ IAM role {role_name} already exists")
    except iam_client.exceptions.NoSuchEntityException:
        print(f"🔐 Creating IAM role {role_name}...")
        
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
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"IAM role for {LAMBDA_FUNCTION_NAME} Lambda function"
        )
        
        # Attach policies
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
            "arn:aws:iam::aws:policy/ComprehendReadOnly",
            "arn:aws:iam::aws:policy/TranslateReadOnly"
        ]
        
        for policy_arn in policies:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        
        print(f"✅ IAM role {role_name} created with policies")
    
    # Get role ARN
    role_response = iam_client.get_role(RoleName=role_name)
    role_arn = role_response['Role']['Arn']
    
    # Read deployment package
    with open(zip_path, 'rb') as zip_file:
        zip_content = zip_file.read()
    
    try:
        # Check if function exists
        lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        
        print(f"🔄 Updating existing Lambda function {LAMBDA_FUNCTION_NAME}...")
        
        # Update function code
        lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_content
        )
        
        # Update function configuration
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=LAMBDA_RUNTIME,
            Handler=LAMBDA_HANDLER,
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={
                'Variables': LAMBDA_ENV_VARS
            }
        )
        
        print(f"✅ Lambda function {LAMBDA_FUNCTION_NAME} updated")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"🆕 Creating new Lambda function {LAMBDA_FUNCTION_NAME}...")
        
        # Create function
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=LAMBDA_RUNTIME,
            Role=role_arn,
            Handler=LAMBDA_HANDLER,
            Code={'ZipFile': zip_content},
            Description="LangChain + LangGraph AI agent for LMS chat",
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={
                'Variables': LAMBDA_ENV_VARS
            },
            Tags={
                'Project': 'LMS-Backend',
                'Component': 'LangGraph-Agent',
                'Environment': 'Development'
            }
        )
        
        print(f"✅ Lambda function {LAMBDA_FUNCTION_NAME} created")
        print(f"📍 Function ARN: {response['FunctionArn']}")
    
    return True

def create_api_gateway_integration():
    """Create API Gateway integration for Lambda function"""
    
    print("🌐 Setting up API Gateway integration...")
    
    # This would create API Gateway endpoints
    # For now, we'll just print the instructions
    
    print("""
    📋 Manual API Gateway Setup Instructions:
    
    1. Go to AWS API Gateway Console
    2. Create new REST API or use existing
    3. Create resources and methods:
       - POST /api/chat/langgraph
       - GET /api/chat/workflow
       - POST /api/chat/toggle
       - GET /api/chat/history
    
    4. Set Lambda integration:
       - Integration type: Lambda Function
       - Lambda Function: {LAMBDA_FUNCTION_NAME}
       - Use Lambda Proxy integration: Yes
    
    5. Enable CORS for all methods
    6. Deploy API to stage (e.g., 'dev')
    7. Update test_langgraph_workflow.html with API Gateway URL
    """.format(LAMBDA_FUNCTION_NAME=LAMBDA_FUNCTION_NAME))

def test_lambda_function():
    """Test the deployed Lambda function"""
    
    print("🧪 Testing Lambda function...")
    
    lambda_client = boto3.client('lambda')
    
    # Test event
    test_event = {
        "httpMethod": "POST",
        "path": "/api/chat/langgraph",
        "body": json.dumps({
            "user_id": "test-user-123",
            "message": "Hello, test the LangGraph workflow!"
        }),
        "headers": {
            "Content-Type": "application/json"
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Lambda function test successful!")
            print(f"📄 Response: {json.dumps(payload, indent=2)}")
        else:
            print(f"❌ Lambda function test failed: {payload}")
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {str(e)}")

def main():
    """Main deployment function"""
    
    print("🚀 Starting LangGraph Lambda Deployment")
    print("=" * 50)
    
    try:
        # Create deployment package
        zip_path = create_deployment_package()
        
        # Deploy to AWS
        deploy_lambda_function(zip_path)
        
        # Setup API Gateway (manual for now)
        create_api_gateway_integration()
        
        # Test function
        test_lambda_function()
        
        print("\n" + "=" * 50)
        print("✅ LangGraph Lambda deployment completed!")
        print("\n📋 Next Steps:")
        print("1. Set up API Gateway endpoints (see instructions above)")
        print("2. Update test_langgraph_workflow.html with your API Gateway URL")
        print("3. Test the workflow using the HTML interface")
        print("4. Monitor CloudWatch logs for debugging")
        
        # Cleanup
        if zip_path.exists():
            zip_path.unlink()
            print(f"🗑️ Cleaned up deployment package: {zip_path}")
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
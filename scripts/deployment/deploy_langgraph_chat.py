#!/usr/bin/env python3
"""
Deploy LangGraph AI Agent Chat Lambda Function
Enhanced deployment with LangGraph workflow orchestration
"""

import boto3
import json
import zipfile
import os
import time
import subprocess
import sys
from datetime import datetime

# Configuration
LAMBDA_FUNCTION_NAME = "lms-langgraph-chat"
LAMBDA_ROLE_NAME = "lms-langgraph-chat-role"
API_GATEWAY_NAME = "lms-langgraph-api"
REGION = "us-east-1"
PYTHON_VERSION = "python3.9"

# AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam', region_name=REGION)
apigateway_client = boto3.client('apigateway', region_name=REGION)
logs_client = boto3.client('logs', region_name=REGION)

def print_status(message):
    """Print status message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_iam_role():
    """Create IAM role for LangGraph Lambda function with enhanced permissions"""
    
    print_status("Creating IAM role for LangGraph Lambda...")
    
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
    
    # Enhanced policy for LangGraph with AWS services
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
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    "arn:aws:dynamodb:*:*:table/lms-chat-*",
                    "arn:aws:dynamodb:*:*:table/lms-user-files",
                    "arn:aws:dynamodb:*:*:table/lms-chat-*/index/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": [
                    "arn:aws:s3:::lms-documents-*/*",
                    "arn:aws:s3:::lms-chat-*/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeAgent",
                    "bedrock:GetKnowledgeBase",
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "comprehend:DetectEntities",
                    "comprehend:DetectKeyPhrases",
                    "comprehend:DetectSentiment",
                    "comprehend:DetectDominantLanguage",
                    "comprehend:DetectSyntax"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "textract:DetectDocumentText",
                    "textract:AnalyzeDocument",
                    "textract:StartDocumentTextDetection",
                    "textract:GetDocumentTextDetection"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "translate:TranslateText",
                    "translate:DetectDominantLanguage"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue"
                ],
                "Resource": [
                    "arn:aws:secretsmanager:*:*:secret:lms/*",
                    "arn:aws:secretsmanager:*:*:secret:pinecone/*"
                ]
            }
        ]
    }
    
    try:
        # Create role
        role_response = iam_client.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for LMS LangGraph Chat Lambda function"
        )
        
        role_arn = role_response['Role']['Arn']
        print_status(f"Created IAM role: {role_arn}")
        
        # Attach inline policy
        iam_client.put_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyName="LangGraphChatLambdaPolicy",
            PolicyDocument=json.dumps(lambda_policy)
        )
        
        print_status("Attached inline policy to role")
        
        # Wait for role to be available
        print_status("Waiting for IAM role to be available...")
        time.sleep(10)
        
        return role_arn
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print_status("IAM role already exists, getting ARN...")
        role_response = iam_client.get_role(RoleName=LAMBDA_ROLE_NAME)
        return role_response['Role']['Arn']
    except Exception as e:
        print_status(f"Error creating IAM role: {str(e)}")
        raise

def create_lambda_package():
    """Create Lambda deployment package with LangGraph dependencies"""
    
    print_status("Creating Lambda deployment package...")
    
    # Create temporary directory for package
    package_dir = "temp_langgraph_package"
    if os.path.exists(package_dir):
        import shutil
        try:
            shutil.rmtree(package_dir)
        except PermissionError:
            # Windows permission issue - try to remove files individually
            import stat
            def handle_remove_readonly(func, path, exc):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(package_dir, onerror=handle_remove_readonly)
    
    os.makedirs(package_dir)
    
    try:
        # Install dependencies
        print_status("Installing LangGraph dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", "src/chat/requirements.txt",
            "-t", package_dir,
            "--no-deps"  # Install only specified packages
        ], check=True)
        
        # Install core dependencies manually
        core_deps = [
            "langchain==0.1.0",
            "langgraph==0.0.26", 
            "langchain-aws==0.1.0",
            "boto3==1.34.0",
            "pydantic==2.5.0",
            "aiohttp==3.9.0"
        ]
        
        for dep in core_deps:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install",
                    dep, "-t", package_dir
                ], check=True)
                print_status(f"Installed {dep}")
            except subprocess.CalledProcessError as e:
                print_status(f"Warning: Could not install {dep}: {e}")
        
        # Copy Lambda function code
        import shutil
        
        # Copy main handler
        shutil.copy2("src/chat/langgraph_chat_handler.py", 
                    os.path.join(package_dir, "lambda_function.py"))
        
        # Copy shared modules
        shared_dir = os.path.join(package_dir, "shared")
        os.makedirs(shared_dir, exist_ok=True)
        
        if os.path.exists("src/shared"):
            for file in os.listdir("src/shared"):
                if file.endswith('.py'):
                    shutil.copy2(os.path.join("src/shared", file), 
                               os.path.join(shared_dir, file))
        
        # Copy file processing modules
        file_processing_dir = os.path.join(package_dir, "file_processing")
        os.makedirs(file_processing_dir, exist_ok=True)
        
        if os.path.exists("src/file_processing"):
            for file in os.listdir("src/file_processing"):
                if file.endswith('.py'):
                    shutil.copy2(os.path.join("src/file_processing", file), 
                               os.path.join(file_processing_dir, file))
        
        # Create ZIP package
        zip_filename = "langgraph-chat.zip"
        print_status(f"Creating ZIP package: {zip_filename}")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arc_name)
        
        # Clean up temporary directory
        try:
            shutil.rmtree(package_dir)
        except PermissionError:
            # Windows permission issue - try to remove files individually
            import stat
            def handle_remove_readonly(func, path, exc):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(package_dir, onerror=handle_remove_readonly)
        
        print_status(f"Lambda package created: {zip_filename}")
        return zip_filename
        
    except Exception as e:
        print_status(f"Error creating Lambda package: {str(e)}")
        # Clean up on error
        if os.path.exists(package_dir):
            import shutil
            try:
                shutil.rmtree(package_dir)
            except PermissionError:
                # Windows permission issue - try to remove files individually
                import stat
                def handle_remove_readonly(func, path, exc):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(package_dir, onerror=handle_remove_readonly)
        raise

def deploy_lambda_function(role_arn, zip_filename):
    """Deploy or update Lambda function"""
    
    print_status("Deploying Lambda function...")
    
    # Read ZIP file
    with open(zip_filename, 'rb') as f:
        zip_content = f.read()
    
    # Environment variables for LangGraph
    environment_vars = {
        'DOCUMENTS_BUCKET': f'lms-documents-{boto3.Session().region_name}',
        'DYNAMODB_TABLE': 'lms-user-files',
        'CHAT_CONVERSATIONS_TABLE': 'lms-chat-conversations',
        'CHAT_MESSAGES_TABLE': 'lms-chat-messages',
        'BEDROCK_REGION': REGION,
        'LANGCHAIN_TRACING_V2': 'false',  # Disable tracing for now
        'LANGCHAIN_API_KEY': '',  # Not needed for basic usage
        'PYTHONPATH': '/var/runtime:/opt/python'
    }
    
    try:
        # Try to update existing function
        lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_content
        )
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=PYTHON_VERSION,
            Handler="lambda_function.lambda_handler",
            Role=role_arn,
            Timeout=300,  # 5 minutes for LangGraph processing
            MemorySize=1024,  # More memory for LangGraph
            Environment={'Variables': environment_vars}
        )
        
        print_status("Updated existing Lambda function")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=PYTHON_VERSION,
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={'ZipFile': zip_content},
            Description="LMS LangGraph AI Agent Chat Handler",
            Timeout=300,  # 5 minutes
            MemorySize=1024,  # More memory for LangGraph
            Environment={'Variables': environment_vars},
            Tags={
                'Project': 'LMS',
                'Component': 'LangGraphChat',
                'Environment': 'development'
            }
        )
        
        print_status("Created new Lambda function")
    
    # Wait for function to be ready
    print_status("Waiting for Lambda function to be ready...")
    waiter = lambda_client.get_waiter('function_active')
    waiter.wait(FunctionName=LAMBDA_FUNCTION_NAME)
    
    # Get function info
    function_info = lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
    function_arn = function_info['Configuration']['FunctionArn']
    
    print_status(f"Lambda function ready: {function_arn}")
    return function_arn

def create_api_gateway(lambda_arn):
    """Create API Gateway for LangGraph chat"""
    
    print_status("Setting up API Gateway...")
    
    try:
        # Create REST API
        api_response = apigateway_client.create_rest_api(
            name=API_GATEWAY_NAME,
            description="LMS LangGraph Chat API",
            endpointConfiguration={'types': ['REGIONAL']}
        )
        
        api_id = api_response['id']
        print_status(f"Created API Gateway: {api_id}")
        
        # Get root resource
        resources = apigateway_client.get_resources(restApiId=api_id)
        root_resource_id = None
        for resource in resources['items']:
            if resource['path'] == '/':
                root_resource_id = resource['id']
                break
        
        # Create /chat resource
        chat_resource = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='chat'
        )
        chat_resource_id = chat_resource['id']
        
        # Create /chat/history resource
        history_resource = apigateway_client.create_resource(
            restApiId=api_id,
            parentId=chat_resource_id,
            pathPart='history'
        )
        history_resource_id = history_resource['id']
        
        # Create POST method for /chat
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=chat_resource_id,
            httpMethod='POST',
            authorizationType='NONE'
        )
        
        # Create GET method for /chat/history
        apigateway_client.put_method(
            restApiId=api_id,
            resourceId=history_resource_id,
            httpMethod='GET',
            authorizationType='NONE'
        )
        
        # Set up Lambda integration for POST /chat
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=chat_resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )
        
        # Set up Lambda integration for GET /chat/history
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=history_resource_id,
            httpMethod='GET',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        )
        
        # Enable CORS
        for resource_id in [chat_resource_id, history_resource_id]:
            # OPTIONS method
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Mock integration for OPTIONS
            apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            # OPTIONS response
            apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': False,
                    'method.response.header.Access-Control-Allow-Methods': False,
                    'method.response.header.Access-Control-Allow-Headers': False
                }
            )
            
            apigateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization'"
                }
            )
        
        # Deploy API
        deployment = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='dev',
            description='LangGraph Chat API deployment'
        )
        
        # Add Lambda permission for API Gateway
        try:
            lambda_client.add_permission(
                FunctionName=LAMBDA_FUNCTION_NAME,
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{REGION}:*:{api_id}/*/*'
            )
        except lambda_client.exceptions.ResourceConflictException:
            print_status("Lambda permission already exists")
        
        api_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/dev"
        print_status(f"API Gateway deployed: {api_url}")
        
        return api_id, api_url
        
    except Exception as e:
        print_status(f"Error setting up API Gateway: {str(e)}")
        raise

def create_dynamodb_tables():
    """Create DynamoDB tables for chat if they don't exist"""
    
    print_status("Checking DynamoDB tables...")
    
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    
    # Chat conversations table
    try:
        conversations_table = dynamodb.create_table(
            TableName='lms-chat-conversations',
            KeySchema=[
                {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user-id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print_status("Created lms-chat-conversations table")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print_status("lms-chat-conversations table already exists")
    except Exception as e:
        print_status(f"Error creating conversations table: {str(e)}")
        # Try without GSI
        try:
            conversations_table = dynamodb.create_table(
                TableName='lms-chat-conversations',
                KeySchema=[
                    {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'conversation_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            print_status("Created lms-chat-conversations table (without GSI)")
        except dynamodb.meta.client.exceptions.ResourceInUseException:
            print_status("lms-chat-conversations table already exists")
    
    # Chat messages table
    try:
        messages_table = dynamodb.create_table(
            TableName='lms-chat-messages',
            KeySchema=[
                {'AttributeName': 'conversation_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print_status("Created lms-chat-messages table")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print_status("lms-chat-messages table already exists")
    except Exception as e:
        print_status(f"Error creating messages table: {str(e)}")

def test_deployment(api_url):
    """Test the deployed LangGraph chat function"""
    
    print_status("Testing LangGraph deployment...")
    
    import requests
    
    # Test chat endpoint
    test_message = {
        "user_id": "test-user-123",
        "message": "Hello! Can you summarize my documents?",
        "subject_id": "test-subject"
    }
    
    try:
        response = requests.post(
            f"{api_url}/chat",
            json=test_message,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_status("✅ Chat endpoint test successful!")
            print_status(f"Response: {result.get('response', 'No response')[:100]}...")
            print_status(f"LangGraph workflow: {result.get('langgraph_workflow', False)}")
            print_status(f"Intent detected: {result.get('intent_detected', 'None')}")
            print_status(f"Tools used: {result.get('tools_used', [])}")
        else:
            print_status(f"❌ Chat endpoint test failed: {response.status_code}")
            print_status(f"Response: {response.text}")
    
    except Exception as e:
        print_status(f"❌ Test request failed: {str(e)}")
    
    # Test history endpoint
    try:
        response = requests.get(
            f"{api_url}/chat/history?user_id=test-user-123",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print_status("✅ History endpoint test successful!")
            print_status(f"Conversations found: {len(result.get('conversations', []))}")
        else:
            print_status(f"❌ History endpoint test failed: {response.status_code}")
    
    except Exception as e:
        print_status(f"❌ History test failed: {str(e)}")

def main():
    """Main deployment function"""
    
    print_status("🚀 Starting LangGraph AI Agent Chat deployment...")
    
    try:
        # Create DynamoDB tables
        create_dynamodb_tables()
        
        # Create IAM role
        role_arn = create_iam_role()
        
        # Create Lambda package
        zip_filename = create_lambda_package()
        
        # Deploy Lambda function
        lambda_arn = deploy_lambda_function(role_arn, zip_filename)
        
        # Create API Gateway
        api_id, api_url = create_api_gateway(lambda_arn)
        
        # Test deployment
        time.sleep(5)  # Wait for everything to be ready
        test_deployment(api_url)
        
        # Clean up ZIP file
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
        
        print_status("🎉 LangGraph AI Agent Chat deployment completed!")
        print_status(f"📡 API URL: {api_url}")
        print_status(f"🔧 Lambda Function: {LAMBDA_FUNCTION_NAME}")
        print_status(f"📊 API Gateway: {api_id}")
        
        print_status("\n📋 Test Commands:")
        print_status(f"curl -X POST {api_url}/chat \\")
        print_status('  -H "Content-Type: application/json" \\')
        print_status('  -d \'{"user_id": "test-user", "message": "summarize my notes"}\'')
        
        print_status(f"\ncurl {api_url}/chat/history?user_id=test-user")
        
        return {
            'api_url': api_url,
            'lambda_arn': lambda_arn,
            'api_id': api_id
        }
        
    except Exception as e:
        print_status(f"❌ Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
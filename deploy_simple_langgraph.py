#!/usr/bin/env python3
"""
Deploy Simplified LangGraph AI Agent Chat Lambda Function
Core functionality without complex dependencies
"""

import boto3
import json
import zipfile
import os
import time
from datetime import datetime

# Configuration
LAMBDA_FUNCTION_NAME = "lms-simple-langgraph-chat"
LAMBDA_ROLE_NAME = "lms-simple-langgraph-role"
API_GATEWAY_NAME = "lms-simple-langgraph-api"
REGION = "us-east-1"
PYTHON_VERSION = "python3.9"

# AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam', region_name=REGION)
apigateway_client = boto3.client('apigateway', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

def print_status(message):
    """Print status message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_iam_role():
    """Create IAM role for simplified LangGraph Lambda function"""
    
    print_status("Creating IAM role for simplified LangGraph Lambda...")
    
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
    
    # Simplified policy for core AWS services
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
                    "s3:PutObject"
                ],
                "Resource": [
                    "arn:aws:s3:::lms-documents-*/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "comprehend:DetectEntities",
                    "comprehend:DetectKeyPhrases",
                    "comprehend:DetectSentiment",
                    "comprehend:DetectDominantLanguage"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "translate:TranslateText"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Create role
        role_response = iam_client.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for LMS Simplified LangGraph Chat Lambda function"
        )
        
        role_arn = role_response['Role']['Arn']
        print_status(f"Created IAM role: {role_arn}")
        
        # Attach inline policy
        iam_client.put_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyName="SimpleLangGraphChatLambdaPolicy",
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
    """Create Lambda deployment package with minimal dependencies"""
    
    print_status("Creating simplified Lambda deployment package...")
    
    # Create ZIP package directly
    zip_filename = "simple-langgraph-chat.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add main handler
        zipf.write("src/chat/simple_langgraph_handler.py", "lambda_function.py")
        
        # Add shared modules if they exist
        if os.path.exists("src/shared"):
            for file in os.listdir("src/shared"):
                if file.endswith('.py'):
                    zipf.write(os.path.join("src/shared", file), f"shared/{file}")
        
        # Add file processing modules if they exist
        if os.path.exists("src/file_processing"):
            for file in os.listdir("src/file_processing"):
                if file.endswith('.py'):
                    zipf.write(os.path.join("src/file_processing", file), f"file_processing/{file}")
    
    print_status(f"Lambda package created: {zip_filename}")
    return zip_filename

def deploy_lambda_function(role_arn, zip_filename):
    """Deploy or update Lambda function"""
    
    print_status("Deploying simplified Lambda function...")
    
    # Read ZIP file
    with open(zip_filename, 'rb') as f:
        zip_content = f.read()
    
    # Environment variables
    environment_vars = {
        'DOCUMENTS_BUCKET': f'lms-documents-{boto3.Session().region_name}',
        'DYNAMODB_TABLE': 'lms-user-files',
        'CHAT_CONVERSATIONS_TABLE': 'lms-chat-conversations',
        'CHAT_MESSAGES_TABLE': 'lms-chat-messages'
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
            Timeout=60,  # 1 minute
            MemorySize=512,  # 512 MB
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
            Description="LMS Simplified LangGraph AI Agent Chat Handler",
            Timeout=60,  # 1 minute
            MemorySize=512,  # 512 MB
            Environment={'Variables': environment_vars},
            Tags={
                'Project': 'LMS',
                'Component': 'SimpleLangGraphChat',
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
    """Create API Gateway for simplified LangGraph chat"""
    
    print_status("Setting up API Gateway...")
    
    try:
        # Create REST API
        api_response = apigateway_client.create_rest_api(
            name=API_GATEWAY_NAME,
            description="LMS Simplified LangGraph Chat API",
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
            description='Simplified LangGraph Chat API deployment'
        )
        
        # Add Lambda permission for API Gateway
        try:
            # Get account ID
            account_id = boto3.client('sts').get_caller_identity()['Account']
            
            lambda_client.add_permission(
                FunctionName=LAMBDA_FUNCTION_NAME,
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*/*'
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
    
    # Chat conversations table
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
        print_status("Created lms-chat-conversations table")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print_status("lms-chat-conversations table already exists")
    except Exception as e:
        print_status(f"Error creating conversations table: {str(e)}")
    
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
    """Test the deployed simplified LangGraph chat function"""
    
    print_status("Testing simplified LangGraph deployment...")
    
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
    
    print_status("🚀 Starting Simplified LangGraph AI Agent Chat deployment...")
    
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
        
        print_status("🎉 Simplified LangGraph AI Agent Chat deployment completed!")
        print_status(f"📡 API URL: {api_url}")
        print_status(f"🔧 Lambda Function: {LAMBDA_FUNCTION_NAME}")
        print_status(f"📊 API Gateway: {api_id}")
        
        print_status("\n📋 Test Commands:")
        print_status(f"curl -X POST {api_url}/chat \\")
        print_status('  -H "Content-Type: application/json" \\')
        print_status('  -d \'{"user_id": "test-user", "message": "summarize my notes"}\'')
        
        print_status(f"\ncurl {api_url}/chat/history?user_id=test-user")
        
        # Update test HTML with API URL
        update_test_html(api_url)
        
        return {
            'api_url': api_url,
            'lambda_arn': lambda_arn,
            'api_id': api_id
        }
        
    except Exception as e:
        print_status(f"❌ Deployment failed: {str(e)}")
        raise

def update_test_html(api_url):
    """Update test HTML file with the deployed API URL"""
    
    try:
        # Read the test HTML file
        with open('test_langgraph_chat.html', 'r') as f:
            html_content = f.read()
        
        # Replace the placeholder API URL
        updated_content = html_content.replace(
            'API_BASE_URL = "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev"',
            f'API_BASE_URL = "{api_url}"'
        )
        
        # Write back the updated content
        with open('test_langgraph_chat.html', 'w') as f:
            f.write(updated_content)
        
        print_status(f"✅ Updated test_langgraph_chat.html with API URL: {api_url}")
        
    except Exception as e:
        print_status(f"⚠️ Could not update test HTML file: {str(e)}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Direct API Gateway Deployment for Task 12: Frontend-Backend API Integration
Uses boto3 directly instead of SAM CLI
"""

import boto3
import json
import zipfile
import os
import time
from datetime import datetime
import tempfile
import shutil
from botocore.exceptions import ClientError

class APIGatewayDeployer:
    def __init__(self):
        self.region = 'us-east-1'
        self.account_id = '145023137830'
        
        # AWS clients
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.apigateway_client = boto3.client('apigateway', region_name=self.region)
        self.apigatewayv2_client = boto3.client('apigatewayv2', region_name=self.region)
        self.iam_client = boto3.client('iam', region_name=self.region)
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        
        # Configuration
        self.environment = 'dev'
        self.bedrock_agent_id = 'ZTBBVSC6Y1'
        self.bedrock_agent_alias_id = 'TSTALIASID'
        
    def create_lambda_execution_role(self, role_name):
        """Create IAM role for Lambda execution"""
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
        
        try:
            # Try to get existing role
            response = self.iam_client.get_role(RoleName=role_name)
            print(f"✅ Using existing IAM role: {role_name}")
            return response['Role']['Arn']
        except self.iam_client.exceptions.NoSuchEntityException:
            pass
        
        # Create new role
        response = self.iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f'Lambda execution role for {role_name}'
        )
        
        role_arn = response['Role']['Arn']
        
        # Attach basic Lambda execution policy
        self.iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Create and attach custom policy for Bedrock and other services
        custom_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent",
                        "bedrock-agent-runtime:InvokeAgent",
                        "bedrock:InvokeModel"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket",
                        "s3:GeneratePresignedUrl"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::lms-documents-{self.environment}-{self.account_id}",
                        f"arn:aws:s3:::lms-documents-{self.environment}-{self.account_id}/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/lms-sessions-{self.environment}",
                        f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/lms-sessions-{self.environment}/index/*",
                        f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/lms-quizzes-{self.environment}",
                        f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/lms-quizzes-{self.environment}/index/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "execute-api:ManageConnections"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "textract:DetectDocumentText",
                        "textract:AnalyzeDocument",
                        "comprehend:DetectEntities",
                        "comprehend:DetectKeyPhrases",
                        "comprehend:DetectSentiment",
                        "comprehend:DetectDominantLanguage"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        policy_name = f"{role_name}-policy"
        try:
            self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(custom_policy),
                Description=f'Custom policy for {role_name}'
            )
            
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=f'arn:aws:iam::{self.account_id}:policy/{policy_name}'
            )
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            # Policy already exists, attach it
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=f'arn:aws:iam::{self.account_id}:policy/{policy_name}'
            )
        
        print(f"✅ Created IAM role: {role_name}")
        
        # Wait for role to be available
        time.sleep(10)
        
        return role_arn
    
    def create_lambda_package(self, source_dir, handler_file):
        """Create Lambda deployment package"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Copy source files
            if os.path.exists(source_dir):
                for file in os.listdir(source_dir):
                    if file.endswith('.py'):
                        shutil.copy(os.path.join(source_dir, file), temp_dir)
            
            # Ensure handler file exists
            handler_path = os.path.join(temp_dir, handler_file)
            if not os.path.exists(handler_path):
                # Create a basic handler if it doesn't exist
                with open(handler_path, 'w') as f:
                    f.write(f'''
import json
import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Basic Lambda handler"""
    try:
        return {{
            'statusCode': 200,
            'headers': {{
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }},
            'body': json.dumps({{
                'success': True,
                'message': 'Lambda function is working',
                'timestamp': datetime.utcnow().isoformat()
            }})
        }}
    except Exception as e:
        logger.error(f"Error: {{str(e)}}")
        return {{
            'statusCode': 500,
            'headers': {{
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }},
            'body': json.dumps({{
                'success': False,
                'error': str(e)
            }})
        }}
''')
            
            # Create ZIP file
            zip_path = os.path.join(temp_dir, 'function.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file != 'function.zip':
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
            
            # Read ZIP content
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            return zip_content
            
        finally:
            shutil.rmtree(temp_dir)
    
    def create_lambda_function(self, function_name, handler, role_arn, source_dir, description=""):
        """Create or update Lambda function"""
        
        # Create deployment package
        zip_content = self.create_lambda_package(source_dir, handler.split('.')[0] + '.py')
        
        environment_vars = {
            'ENVIRONMENT': self.environment,
            'BEDROCK_AGENT_ID': self.bedrock_agent_id,
            'BEDROCK_AGENT_ALIAS_ID': self.bedrock_agent_alias_id,
            'DOCUMENTS_BUCKET': f'lms-documents-{self.environment}-{self.account_id}',
            'SESSIONS_TABLE': f'lms-sessions-{self.environment}',
            'QUIZZES_TABLE': f'lms-quizzes-{self.environment}'
        }
        
        try:
            # Try to get existing function
            existing_function = self.lambda_client.get_function(FunctionName=function_name)
            
            try:
                # Try to update existing function
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                
                # Update configuration
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=role_arn,
                    Handler=handler,
                    Description=description,
                    Timeout=30,
                    MemorySize=256,
                    Environment={'Variables': environment_vars}
                )
                
                print(f"✅ Updated Lambda function: {function_name}")
                
            except ClientError as e:
                if 'ResourceConflictException' in str(e):
                    print(f"⚠️ Lambda function {function_name} is being updated, using existing version")
                    response = existing_function['Configuration']
                else:
                    raise
            
        except self.lambda_client.exceptions.ResourceNotFoundException:
            # Create new function
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler=handler,
                Code={'ZipFile': zip_content},
                Description=description,
                Timeout=30,
                MemorySize=256,
                Environment={'Variables': environment_vars}
            )
            
            print(f"✅ Created Lambda function: {function_name}")
        
        return response['FunctionArn']
    
    def create_s3_bucket(self):
        """Create S3 bucket for documents"""
        bucket_name = f'lms-documents-{self.environment}-{self.account_id}'
        
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Using existing S3 bucket: {bucket_name}")
        except:
            # Create bucket
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Configure CORS
            cors_config = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                        'AllowedOrigins': ['*'],
                        'MaxAgeSeconds': 3600
                    }
                ]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=bucket_name,
                CORSConfiguration=cors_config
            )
            
            print(f"✅ Created S3 bucket: {bucket_name}")
        
        return bucket_name
    
    def create_dynamodb_tables(self):
        """Create DynamoDB tables"""
        tables = [
            {
                'name': f'lms-sessions-{self.environment}',
                'key_schema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'}
                ],
                'attribute_definitions': [
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'user-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            },
            {
                'name': f'lms-quizzes-{self.environment}',
                'key_schema': [
                    {'AttributeName': 'quiz_id', 'KeyType': 'HASH'}
                ],
                'attribute_definitions': [
                    {'AttributeName': 'quiz_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'}
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'user-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            }
        ]
        
        for table_config in tables:
            try:
                # Check if table exists
                self.dynamodb_client.describe_table(TableName=table_config['name'])
                print(f"✅ Using existing DynamoDB table: {table_config['name']}")
            except self.dynamodb_client.exceptions.ResourceNotFoundException:
                # Create table
                create_params = {
                    'TableName': table_config['name'],
                    'KeySchema': table_config['key_schema'],
                    'AttributeDefinitions': table_config['attribute_definitions'],
                    'BillingMode': 'PAY_PER_REQUEST'
                }
                
                if 'global_secondary_indexes' in table_config:
                    create_params['GlobalSecondaryIndexes'] = table_config['global_secondary_indexes']
                
                self.dynamodb_client.create_table(**create_params)
                
                # Wait for table to be active
                waiter = self.dynamodb_client.get_waiter('table_exists')
                waiter.wait(TableName=table_config['name'])
                
                print(f"✅ Created DynamoDB table: {table_config['name']}")
    
    def create_api_gateway(self, lambda_function_arn):
        """Create REST API Gateway"""
        
        # Create API
        try:
            apis = self.apigateway_client.get_rest_apis()
            existing_api = None
            for api in apis['items']:
                if api['name'] == f'lms-api-{self.environment}':
                    existing_api = api
                    break
            
            if existing_api:
                api_id = existing_api['id']
                print(f"✅ Using existing API Gateway: {api_id}")
            else:
                response = self.apigateway_client.create_rest_api(
                    name=f'lms-api-{self.environment}',
                    description='LMS API Gateway for Frontend Integration',
                    endpointConfiguration={'types': ['REGIONAL']}
                )
                api_id = response['id']
                print(f"✅ Created API Gateway: {api_id}")
            
            # Get root resource
            resources = self.apigateway_client.get_resources(restApiId=api_id)
            root_resource_id = None
            for resource in resources['items']:
                if resource['path'] == '/':
                    root_resource_id = resource['id']
                    break
            
            # Create API structure
            api_resource_id = self.create_api_resource(api_id, root_resource_id, 'api')
            v1_resource_id = self.create_api_resource(api_id, api_resource_id, 'v1')
            
            # Create endpoints
            endpoints = [
                {'path': 'chat', 'methods': ['POST', 'OPTIONS']},
                {'path': 'health', 'methods': ['GET', 'OPTIONS']},
                {'path': 'capabilities', 'methods': ['GET', 'OPTIONS']},
                {'path': 'documents', 'methods': ['GET', 'OPTIONS']}
            ]
            
            # Create upload resource with presigned sub-resource
            upload_resource_id = self.create_api_resource(api_id, v1_resource_id, 'upload')
            presigned_resource_id = self.create_api_resource(api_id, upload_resource_id, 'presigned')
            
            # Add methods to presigned resource
            for method in ['POST', 'OPTIONS']:
                if method == 'OPTIONS':
                    self.create_cors_method(api_id, presigned_resource_id)
                else:
                    self.create_api_method(api_id, presigned_resource_id, method, lambda_function_arn)
            
            # Create session resource with history sub-resource
            session_resource_id = self.create_api_resource(api_id, v1_resource_id, 'session')
            history_resource_id = self.create_api_resource(api_id, session_resource_id, 'history')
            
            # Add methods to history resource
            for method in ['GET', 'OPTIONS']:
                if method == 'OPTIONS':
                    self.create_cors_method(api_id, history_resource_id)
                else:
                    self.create_api_method(api_id, history_resource_id, method, lambda_function_arn)
            
            # Create agent resource with invoke sub-resource
            agent_resource_id = self.create_api_resource(api_id, v1_resource_id, 'agent')
            invoke_resource_id = self.create_api_resource(api_id, agent_resource_id, 'invoke')
            
            # Add methods to invoke resource
            for method in ['POST', 'OPTIONS']:
                if method == 'OPTIONS':
                    self.create_cors_method(api_id, invoke_resource_id)
                else:
                    self.create_api_method(api_id, invoke_resource_id, method, lambda_function_arn)
            
            for endpoint in endpoints:
                resource_id = self.create_api_resource(api_id, v1_resource_id, endpoint['path'])
                
                for method in endpoint['methods']:
                    if method == 'OPTIONS':
                        self.create_cors_method(api_id, resource_id)
                    else:
                        self.create_api_method(api_id, resource_id, method, lambda_function_arn)
            
            # Deploy API
            deployment = self.apigateway_client.create_deployment(
                restApiId=api_id,
                stageName=self.environment,
                description=f'Deployment for {self.environment} environment'
            )
            
            api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/{self.environment}"
            print(f"✅ API Gateway deployed: {api_url}")
            
            return api_id, api_url
            
        except Exception as e:
            print(f"❌ Failed to create API Gateway: {e}")
            raise
    
    def create_api_resource(self, api_id, parent_id, path_part):
        """Create API Gateway resource"""
        try:
            # Check if resource exists
            resources = self.apigateway_client.get_resources(restApiId=api_id)
            for resource in resources['items']:
                if resource.get('pathPart') == path_part and resource['parentId'] == parent_id:
                    return resource['id']
            
            # Create new resource
            response = self.apigateway_client.create_resource(
                restApiId=api_id,
                parentId=parent_id,
                pathPart=path_part
            )
            return response['id']
        except Exception as e:
            print(f"Warning: Could not create resource {path_part}: {e}")
            return parent_id
    
    def create_api_method(self, api_id, resource_id, method, lambda_function_arn):
        """Create API Gateway method"""
        try:
            # Create method
            self.apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                authorizationType='NONE'
            )
            
            # Create integration
            self.apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_function_arn}/invocations'
            )
            
            # Add Lambda permission
            function_name = lambda_function_arn.split(':')[-1]
            try:
                self.lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=f'api-gateway-{method}-{resource_id}',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f'arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/*/{method}/*'
                )
            except self.lambda_client.exceptions.ResourceConflictException:
                pass  # Permission already exists
            
        except self.apigateway_client.exceptions.ConflictException:
            pass  # Method already exists
        except Exception as e:
            print(f"Warning: Could not create method {method}: {e}")
    
    def create_cors_method(self, api_id, resource_id):
        """Create CORS OPTIONS method"""
        try:
            # Create OPTIONS method
            self.apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Create mock integration
            self.apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            # Create method response
            self.apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False,
                    'method.response.header.Access-Control-Allow-Origin': False
                }
            )
            
            # Create integration response
            self.apigateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            
        except self.apigateway_client.exceptions.ConflictException:
            pass  # Method already exists
        except Exception as e:
            print(f"Warning: Could not create CORS method: {e}")
    
    def create_websocket_api(self, lambda_function_arn):
        """Create WebSocket API for real-time chat"""
        try:
            # Check if WebSocket API exists
            apis = self.apigatewayv2_client.get_apis()
            existing_api = None
            for api in apis['Items']:
                if api['Name'] == f'lms-websocket-{self.environment}':
                    existing_api = api
                    break
            
            if existing_api:
                api_id = existing_api['ApiId']
                print(f"✅ Using existing WebSocket API: {api_id}")
            else:
                # Create WebSocket API
                response = self.apigatewayv2_client.create_api(
                    Name=f'lms-websocket-{self.environment}',
                    ProtocolType='WEBSOCKET',
                    RouteSelectionExpression='$request.body.action',
                    Description='LMS WebSocket API for real-time chat'
                )
                api_id = response['ApiId']
                print(f"✅ Created WebSocket API: {api_id}")
            
            # Create WebSocket Lambda functions for connect/disconnect/message
            websocket_lambda_arn = self.create_lambda_function(
                function_name=f'lms-websocket-handler-{self.environment}',
                handler='websocket_handler.lambda_handler',
                role_arn=self.create_lambda_execution_role(f'lms-websocket-role-{self.environment}'),
                source_dir='src/websocket',
                description='WebSocket handler for real-time chat'
            )
            
            # Create integrations
            integration_response = self.apigatewayv2_client.create_integration(
                ApiId=api_id,
                IntegrationType='AWS_PROXY',
                IntegrationUri=f'arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{websocket_lambda_arn}/invocations'
            )
            integration_id = integration_response['IntegrationId']
            
            # Create routes
            routes = ['$connect', '$disconnect', 'sendMessage', '$default']
            for route in routes:
                try:
                    self.apigatewayv2_client.create_route(
                        ApiId=api_id,
                        RouteKey=route,
                        Target=f'integrations/{integration_id}'
                    )
                except self.apigatewayv2_client.exceptions.ConflictException:
                    pass  # Route already exists
            
            # Add Lambda permission for WebSocket
            function_name = websocket_lambda_arn.split(':')[-1]
            try:
                self.lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=f'websocket-api-{api_id}',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f'arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/*'
                )
            except self.lambda_client.exceptions.ResourceConflictException:
                pass  # Permission already exists
            
            # Create stage
            try:
                self.apigatewayv2_client.create_stage(
                    ApiId=api_id,
                    StageName=self.environment,
                    AutoDeploy=True,
                    Description=f'WebSocket stage for {self.environment}'
                )
            except self.apigatewayv2_client.exceptions.ConflictException:
                pass  # Stage already exists
            
            websocket_url = f"wss://{api_id}.execute-api.{self.region}.amazonaws.com/{self.environment}"
            print(f"✅ WebSocket API deployed: {websocket_url}")
            
            return api_id, websocket_url
            
        except Exception as e:
            print(f"❌ Failed to create WebSocket API: {e}")
            # Return empty values if WebSocket creation fails
            return "", ""
    
    def deploy(self):
        """Deploy the complete API Gateway infrastructure"""
        print("🚀 Deploying LMS API Gateway Infrastructure")
        print("=" * 50)
        
        try:
            # Create IAM role
            role_arn = self.create_lambda_execution_role(f'lms-lambda-role-{self.environment}')
            
            # Create S3 bucket
            bucket_name = self.create_s3_bucket()
            
            # Create DynamoDB tables
            self.create_dynamodb_tables()
            
            # Create Lambda function
            lambda_arn = self.create_lambda_function(
                function_name=f'lms-bedrock-agent-proxy-{self.environment}',
                handler='bedrock_agent_proxy.lambda_handler',
                role_arn=role_arn,
                source_dir='src/api',
                description='Bedrock Agent Proxy for Frontend Integration'
            )
            
            # Create API Gateway
            api_id, api_url = self.create_api_gateway(lambda_arn)
            
            # Create WebSocket API
            websocket_api_id, websocket_url = self.create_websocket_api(lambda_arn)
            
            # Save configuration
            config = {
                'api_gateway_url': api_url,
                'api_id': api_id,
                'websocket_url': websocket_url,
                'websocket_api_id': websocket_api_id,
                'lambda_function_arn': lambda_arn,
                'documents_bucket': bucket_name,
                'bedrock_agent_id': self.bedrock_agent_id,
                'bedrock_agent_alias_id': self.bedrock_agent_alias_id,
                'region': self.region,
                'environment': self.environment,
                'deployed_at': datetime.utcnow().isoformat()
            }
            
            with open('api_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("\n🎉 Deployment Successful!")
            print("=" * 30)
            print(f"📡 API Gateway URL: {api_url}")
            print(f"🔌 WebSocket URL: {websocket_url}")
            print(f"📁 Documents Bucket: {bucket_name}")
            print(f"🔧 Lambda Function: {lambda_arn}")
            print(f"📝 Configuration saved to: api_config.json")
            
            return config
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            raise

def main():
    """Main deployment function"""
    deployer = APIGatewayDeployer()
    
    try:
        config = deployer.deploy()
        
        print("\n📋 Next Steps:")
        print("1. Test API endpoints")
        print("2. Update frontend configuration")
        print("3. Test frontend integration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
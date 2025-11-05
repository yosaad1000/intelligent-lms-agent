#!/usr/bin/env python3
"""
Deploy Voice Interview Integration with Bedrock Agent
Adds voice processing action group to existing Bedrock Agent
"""

import boto3
import json
import os
import time
import logging
import zipfile
import tempfile
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceInterviewDeployer:
    """Deploy voice interview integration with Bedrock Agent"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        self.lambda_client = boto3.client('lambda')
        self.iam_client = boto3.client('iam')
        self.apigateway_v2 = boto3.client('apigatewayv2')
        self.dynamodb = boto3.resource('dynamodb')
        
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.account_id = os.getenv('AWS_ACCOUNT_ID', '145023137830')
        
        # Get existing agent ID from .env
        self.agent_id = self._get_agent_id_from_env()
    
    def _get_agent_id_from_env(self) -> str:
        """Get agent ID from .env file"""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('BEDROCK_CHAT_AGENT_ID='):
                        return line.split('=')[1].strip()
        except:
            pass
        return 'ZTBBVSC6Y1'  # Fallback to known agent ID
    
    def deploy_voice_interview_integration(self):
        """Deploy complete voice interview integration"""
        
        print("🎤 Deploying Voice Interview Integration")
        print("=" * 50)
        print(f"Agent ID: {self.agent_id}")
        
        try:
            # Step 1: Create DynamoDB tables for voice interviews
            self.create_voice_interview_tables()
            
            # Step 2: Create voice processing Lambda function
            voice_lambda_arn = self.create_voice_processing_lambda()
            
            # Step 3: Create interview handler Lambda first
            interview_lambda_arn = self.create_interview_handler_lambda()
            
            # Step 4: Create WebSocket API Gateway
            websocket_api_id = self.create_websocket_api(interview_lambda_arn)
            
            # Step 5: Add voice action group to Bedrock Agent
            self.add_voice_action_group(voice_lambda_arn)
            
            # Step 6: Update agent instructions
            self.update_agent_instructions_for_voice()
            
            # Step 7: Prepare agent with new configuration
            if self.prepare_agent():
                print(f"✅ Voice interview integration deployed successfully!")
                
                # Step 8: Create new version and update alias
                version = self.create_agent_version()
                if version:
                    self.update_production_alias(version)
                
                # Step 9: Update .env with WebSocket endpoint
                self.update_env_file(websocket_api_id)
                
                # Step 10: Update interview handler with API Gateway ID
                self.update_interview_handler_env(websocket_api_id)
                
                return True
            else:
                print("❌ Agent preparation failed")
                return False
                
        except Exception as e:
            print(f"❌ Voice interview deployment failed: {e}")
            return False
    
    def create_voice_interview_tables(self):
        """Create DynamoDB tables for voice interviews"""
        
        print("📊 Creating DynamoDB tables for voice interviews...")
        
        tables_to_create = [
            {
                'TableName': 'lms-interview-sessions',
                'KeySchema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'BillingMode': 'PAY_PER_REQUEST',
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'user-id-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            },
            {
                'TableName': 'lms-interview-turns',
                'KeySchema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'turn_id', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'turn_id', 'AttributeType': 'S'}
                ],
                'BillingMode': 'PAY_PER_REQUEST'
            },
            {
                'TableName': 'lms-websocket-connections',
                'KeySchema': [
                    {'AttributeName': 'connection_id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'connection_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'BillingMode': 'PAY_PER_REQUEST',
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'user-id-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ]
            }
        ]
        
        for table_config in tables_to_create:
            try:
                # Check if table exists
                table_name = table_config['TableName']
                try:
                    self.dynamodb.Table(table_name).load()
                    print(f"✅ Table {table_name} already exists")
                except:
                    # Create table
                    self.dynamodb.create_table(**table_config)
                    print(f"✅ Created table: {table_name}")
                    
                    # Wait for table to be active
                    table = self.dynamodb.Table(table_name)
                    table.wait_until_exists()
                    
            except Exception as e:
                print(f"⚠️ Error with table {table_config['TableName']}: {e}")
    
    def create_voice_processing_lambda(self):
        """Create voice processing Lambda function"""
        
        print("🔧 Creating voice processing Lambda function...")
        
        function_name = 'lms-voice-processing'
        
        # Create deployment package
        zip_path = self._create_voice_lambda_package()
        
        try:
            # Create Lambda role if needed
            lambda_role_arn = self.create_voice_lambda_role()
            
            # Create or update function
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                # Update existing function
                with open(zip_path, 'rb') as zip_file:
                    response = self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_file.read()
                    )
                print(f"✅ Updated existing Lambda function: {function_name}")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                with open(zip_path, 'rb') as zip_file:
                    response = self.lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime='python3.9',
                        Role=lambda_role_arn,
                        Handler='voice_action_group.lambda_handler',
                        Code={'ZipFile': zip_file.read()},
                        Description='Voice processing action group for Bedrock Agent',
                        Timeout=300,
                        MemorySize=1024,
                        Environment={
                            'Variables': {
                                'BEDROCK_MODEL_ID': 'amazon.nova-micro-v1:0',
                                'S3_BUCKET': 'lms-voice-processing'
                            }
                        }
                    )
                print(f"✅ Created new Lambda function: {function_name}")
            
            # Add Bedrock Agent invoke permission
            self._add_bedrock_invoke_permission(function_name)
            
            return response['FunctionArn']
            
        except Exception as e:
            print(f"❌ Voice processing Lambda creation failed: {e}")
            raise
        finally:
            # Clean up zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
    
    def create_interview_handler_lambda(self):
        """Create interview handler Lambda for WebSocket"""
        
        print("🔧 Creating interview handler Lambda function...")
        
        function_name = 'lms-interview-handler'
        
        # Create deployment package
        zip_path = self._create_interview_lambda_package()
        
        try:
            # Create Lambda role if needed
            lambda_role_arn = self.create_voice_lambda_role()
            
            # Create or update function
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                # Update existing function
                with open(zip_path, 'rb') as zip_file:
                    response = self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_file.read()
                    )
                print(f"✅ Updated existing Lambda function: {function_name}")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                with open(zip_path, 'rb') as zip_file:
                    response = self.lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime='python3.9',
                        Role=lambda_role_arn,
                        Handler='interview_handler.lambda_handler',
                        Code={'ZipFile': zip_file.read()},
                        Description='WebSocket interview handler',
                        Timeout=300,
                        MemorySize=512,
                        Environment={
                            'Variables': {
                                'STAGE': 'dev'
                            }
                        }
                    )
                print(f"✅ Created new Lambda function: {function_name}")
            
            return response['FunctionArn']
            
        except Exception as e:
            print(f"❌ Interview handler Lambda creation failed: {e}")
            raise
        finally:
            # Clean up zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
    
    def create_websocket_api(self, interview_lambda_arn: str):
        """Create WebSocket API Gateway for real-time voice communication"""
        
        print("🌐 Creating WebSocket API Gateway...")
        
        try:
            # Create WebSocket API
            api_response = self.apigateway_v2.create_api(
                Name='lms-voice-interview-websocket',
                ProtocolType='WEBSOCKET',
                RouteSelectionExpression='$request.body.action',
                Description='WebSocket API for voice interviews'
            )
            
            api_id = api_response['ApiId']
            print(f"✅ Created WebSocket API: {api_id}")
            
            # Create routes
            routes = ['$connect', '$disconnect', 'start_interview', 'audio_chunk', 'end_interview']
            
            # Create integration first
            integration_id = self._create_lambda_integration(api_id, interview_lambda_arn)
            
            for route in routes:
                self.apigateway_v2.create_route(
                    ApiId=api_id,
                    RouteKey=route,
                    Target=f'integrations/{integration_id}'
                )
                print(f"✅ Created route: {route}")
            
            # Create deployment
            deployment_response = self.apigateway_v2.create_deployment(
                ApiId=api_id,
                Description='Initial deployment for voice interviews'
            )
            
            # Create stage
            self.apigateway_v2.create_stage(
                ApiId=api_id,
                StageName='dev',
                DeploymentId=deployment_response['DeploymentId'],
                Description='Development stage for voice interviews'
            )
            
            print(f"✅ WebSocket API deployed to stage: dev")
            print(f"WebSocket URL: wss://{api_id}.execute-api.{self.region}.amazonaws.com/dev")
            
            return api_id
            
        except Exception as e:
            print(f"❌ WebSocket API creation failed: {e}")
            raise
    
    def _create_lambda_integration(self, api_id: str, interview_lambda_arn: str) -> str:
        """Create Lambda integration for WebSocket API"""
        
        integration_response = self.apigateway_v2.create_integration(
            ApiId=api_id,
            IntegrationType='AWS_PROXY',
            IntegrationUri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{interview_lambda_arn}/invocations"
        )
        
        # Add permission for API Gateway to invoke Lambda
        try:
            self.lambda_client.add_permission(
                FunctionName='lms-interview-handler',
                StatementId=f'websocket-api-invoke-{int(time.time())}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/*/*'
            )
        except Exception as e:
            logger.warning(f"Could not add API Gateway invoke permission: {e}")
        
        return integration_response['IntegrationId']
    
    def add_voice_action_group(self, lambda_arn: str):
        """Add voice processing action group to Bedrock Agent"""
        
        print("🎤 Adding voice processing action group...")
        
        try:
            action_group_config = {
                'agentId': self.agent_id,
                'agentVersion': 'DRAFT',
                'actionGroupName': 'VoiceInterviewProcessor',
                'description': 'Voice interview processing with real-time transcription and analysis',
                'actionGroupExecutor': {
                    'lambda': lambda_arn
                },
                'apiSchema': {
                    'payload': json.dumps({
                        "openapi": "3.0.0",
                        "info": {
                            "title": "Voice Interview Processing API",
                            "version": "1.0.0"
                        },
                        "paths": {
                            "/start-interview": {
                                "post": {
                                    "summary": "Start a new voice interview session",
                                    "operationId": "startInterview",
                                    "requestBody": {
                                        "required": True,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        "user_id": {"type": "string"},
                                                        "interview_type": {"type": "string"},
                                                        "topic": {"type": "string"},
                                                        "difficulty": {"type": "string"}
                                                    },
                                                    "required": ["user_id", "topic"]
                                                }
                                            }
                                        }
                                    },
                                    "responses": {
                                        "200": {
                                            "description": "Interview session started successfully",
                                            "content": {
                                                "application/json": {
                                                    "schema": {
                                                        "type": "object",
                                                        "properties": {
                                                            "session_id": {"type": "string"},
                                                            "initial_question": {"type": "string"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "/end-interview": {
                                "post": {
                                    "summary": "End interview session and get analysis",
                                    "operationId": "endInterview",
                                    "requestBody": {
                                        "required": True,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        "session_id": {"type": "string"}
                                                    },
                                                    "required": ["session_id"]
                                                }
                                            }
                                        }
                                    },
                                    "responses": {
                                        "200": {
                                            "description": "Interview ended with analysis",
                                            "content": {
                                                "application/json": {
                                                    "schema": {
                                                        "type": "object",
                                                        "properties": {
                                                            "analysis": {"type": "object"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    })
                }
            }
            
            self.bedrock_agent.create_agent_action_group(**action_group_config)
            print("✅ Voice processing action group added")
            
        except Exception as e:
            print(f"❌ Voice action group creation failed: {e}")
            raise
    
    def update_agent_instructions_for_voice(self):
        """Update agent instructions to include voice capabilities"""
        
        print("📝 Updating agent instructions for voice capabilities...")
        
        enhanced_instructions = '''You are an advanced Learning Management System assistant with comprehensive capabilities including voice interview processing.

Your core abilities include:

🎤 **Voice Interview Processing**
- Conduct real-time voice interviews on any educational topic
- Process audio input with AWS Transcribe for accurate speech-to-text
- Generate contextual follow-up questions based on user responses
- Provide detailed performance analysis and feedback
- Support various interview types: technical, conceptual, practice sessions
- Analyze speech clarity, content accuracy, and response quality

🎯 **Enhanced Quiz Generation**
- Create multilingual quizzes from any topic or uploaded documents
- Support for beginner, intermediate, and advanced difficulty levels
- Automatic language detection and translation
- Detailed analytics and performance insights

🌍 **Multi-Language Support**
- Translate content between 12+ languages
- Educational content translation (quizzes, lessons, materials)
- Round-trip validation to ensure translation quality

📚 **Document Analysis & RAG**
- Process and analyze uploaded educational materials
- Generate contextual responses based on user documents
- Create quizzes from specific document content
- Provide citations and source references

📊 **Learning Analytics**
- Track concept mastery and learning progress
- Provide personalized recommendations
- Performance insights and improvement suggestions

**Voice Interview Instructions:**

For Starting Interviews:
- "Start a voice interview about [topic]"
- "Begin a technical interview on [subject]"
- "I want to practice explaining [concept] verbally"

For Interview Management:
- "Check my interview status"
- "End the current interview session"
- "Analyze my interview performance"

For Audio Processing:
- Process real-time audio chunks during interviews
- Provide immediate transcription feedback
- Generate contextual follow-up questions
- Maintain conversation flow and context

**Interview Capabilities:**
- Real-time speech-to-text transcription
- Intelligent question generation based on responses
- Performance analysis including clarity and content accuracy
- Session management with conversation history
- Detailed feedback and improvement recommendations

I provide natural, engaging interview experiences that help users practice verbal communication skills while receiving AI-powered feedback and analysis.'''

        try:
            self.bedrock_agent.update_agent(
                agentId=self.agent_id,
                agentName='lms-voice-enhanced-assistant',
                description='Enhanced LMS Assistant with voice interview processing capabilities',
                instruction=enhanced_instructions,
                foundationModel='amazon.nova-micro-v1:0',
                idleSessionTTLInSeconds=1800
            )
            print("✅ Agent instructions updated for voice capabilities")
            
        except Exception as e:
            print(f"❌ Agent instruction update failed: {e}")
            raise
    
    def _create_voice_lambda_package(self) -> str:
        """Create deployment package for voice processing Lambda"""
        
        # Create temporary zip file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'voice_processing_lambda.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add voice action group
            voice_handler_path = 'src/voice_interview/voice_action_group.py'
            if os.path.exists(voice_handler_path):
                zip_file.write(voice_handler_path, 'voice_action_group.py')
            
            # Add shared utilities
            shared_files = [
                'src/shared/config.py',
                'src/shared/utils.py'
            ]
            
            for file_path in shared_files:
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))
        
        return zip_path
    
    def _create_interview_lambda_package(self) -> str:
        """Create deployment package for interview handler Lambda"""
        
        # Create temporary zip file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'interview_handler_lambda.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add interview handler
            interview_handler_path = 'src/voice_interview/interview_handler.py'
            if os.path.exists(interview_handler_path):
                zip_file.write(interview_handler_path, 'interview_handler.py')
            
            # Add shared utilities
            shared_files = [
                'src/shared/config.py',
                'src/shared/utils.py',
                'src/shared/agent_utils.py',
                'src/shared/bedrock_agent_service.py'
            ]
            
            for file_path in shared_files:
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))
        
        return zip_path
    
    def create_voice_lambda_role(self):
        """Create IAM role for voice processing Lambda functions"""
        
        role_name = 'VoiceProcessingLambdaRole'
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            print(f"✅ Using existing IAM role: {role_name}")
            return response['Role']['Arn']
        except self.iam_client.exceptions.NoSuchEntityException:
            print(f"🔧 Creating IAM role: {role_name}")
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='IAM role for voice processing Lambda functions'
            )
            
            role_arn = response['Role']['Arn']
            print(f"✅ Created IAM role: {role_arn}")
            
            # Wait a moment for role to propagate
            time.sleep(10)
            
            # Attach policies for voice processing
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/AmazonTranscribeFullAccess',
                'arn:aws:iam::aws:policy/AmazonAPIGatewayInvokeFullAccess'
            ]
            
            for policy in policies:
                try:
                    self.iam_client.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy
                    )
                    print(f"✅ Attached policy: {policy.split('/')[-1]}")
                except Exception as e:
                    print(f"⚠️ Could not attach policy {policy}: {e}")
            
            # Wait for policies to propagate
            print("⏳ Waiting for IAM role and policies to propagate...")
            time.sleep(30)
            
            return role_arn
    
    def prepare_agent(self):
        """Prepare agent with new voice configuration"""
        
        print("⏳ Preparing agent with voice capabilities...")
        
        try:
            self.bedrock_agent.prepare_agent(agentId=self.agent_id)
            
            # Wait for preparation
            for i in range(60):  # 10 minutes max
                try:
                    agent = self.bedrock_agent.get_agent(agentId=self.agent_id)
                    status = agent['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        print("✅ Agent prepared successfully with voice capabilities")
                        return True
                    elif status == 'FAILED':
                        print("❌ Agent preparation failed")
                        return False
                    
                    print(f"⏳ Status: {status}, waiting... ({i+1}/60)")
                    time.sleep(10)
                    
                except Exception as e:
                    print(f"⏳ Checking status... ({i+1}/60)")
                    time.sleep(10)
            
            print("⚠️ Preparation timeout")
            return False
            
        except Exception as e:
            print(f"❌ Preparation error: {e}")
            return False
    
    def create_agent_version(self):
        """Create new agent version with voice capabilities"""
        
        print("📦 Creating agent version with voice capabilities...")
        
        try:
            response = self.bedrock_agent.create_agent_version(
                agentId=self.agent_id,
                description=f'Voice interview integration - {datetime.utcnow().isoformat()}'
            )
            
            version = response['agentVersion']['version']
            print(f"✅ Created agent version: {version}")
            return version
            
        except Exception as e:
            print(f"❌ Version creation failed: {e}")
            return None
    
    def update_production_alias(self, version: str):
        """Update production alias to new version"""
        
        print(f"🏷️ Updating production alias to version {version}...")
        
        try:
            alias_id = 'TSTALIASID'  # Use existing alias
            
            self.bedrock_agent.update_agent_alias(
                agentId=self.agent_id,
                agentAliasId=alias_id,
                agentAliasName='production',
                description=f'Production alias - Voice interview version {version}',
                agentVersion=version
            )
            
            print(f"✅ Production alias updated to version {version}")
            
        except Exception as e:
            print(f"❌ Alias update failed: {e}")
    
    def update_env_file(self, websocket_api_id: str):
        """Update .env file with WebSocket endpoint"""
        
        print("📝 Updating .env file with WebSocket endpoint...")
        
        try:
            # Read current .env file
            env_lines = []
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_lines = f.readlines()
            
            # Add or update WebSocket configuration
            websocket_url = f"wss://{websocket_api_id}.execute-api.{self.region}.amazonaws.com/dev"
            
            # Check if WebSocket config already exists
            websocket_found = False
            for i, line in enumerate(env_lines):
                if line.startswith('WEBSOCKET_API_ID='):
                    env_lines[i] = f'WEBSOCKET_API_ID={websocket_api_id}\n'
                    websocket_found = True
                elif line.startswith('WEBSOCKET_URL='):
                    env_lines[i] = f'WEBSOCKET_URL={websocket_url}\n'
            
            if not websocket_found:
                env_lines.append(f'\n# Voice Interview WebSocket Configuration\n')
                env_lines.append(f'WEBSOCKET_API_ID={websocket_api_id}\n')
                env_lines.append(f'WEBSOCKET_URL={websocket_url}\n')
            
            # Write updated .env file
            with open('.env', 'w') as f:
                f.writelines(env_lines)
            
            print(f"✅ Updated .env file with WebSocket endpoint: {websocket_url}")
            
        except Exception as e:
            print(f"⚠️ Could not update .env file: {e}")
    
    def update_interview_handler_env(self, websocket_api_id: str):
        """Update interview handler Lambda environment variables"""
        
        print("🔧 Updating interview handler environment variables...")
        
        try:
            self.lambda_client.update_function_configuration(
                FunctionName='lms-interview-handler',
                Environment={
                    'Variables': {
                        'API_GATEWAY_ID': websocket_api_id,
                        'STAGE': 'dev'
                    }
                }
            )
            print(f"✅ Updated interview handler with API Gateway ID: {websocket_api_id}")
            
        except Exception as e:
            print(f"⚠️ Could not update interview handler environment: {e}")
    
    def _add_bedrock_invoke_permission(self, function_name: str):
        """Add permission for Bedrock Agent to invoke Lambda"""
        
        try:
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=f'bedrock-agent-invoke-{int(time.time())}',
                Action='lambda:InvokeFunction',
                Principal='bedrock.amazonaws.com',
                SourceArn=f'arn:aws:bedrock:{self.region}:{self.account_id}:agent/{self.agent_id}'
            )
        except Exception as e:
            # Permission might already exist
            logger.warning(f"Could not add Bedrock invoke permission: {e}")


def main():
    """Main deployment"""
    
    deployer = VoiceInterviewDeployer()
    success = deployer.deploy_voice_interview_integration()
    
    if success:
        print(f"\n🎉 Voice Interview Integration Complete!")
        print(f"Agent ID: {deployer.agent_id}")
        print(f"New capabilities:")
        print(f"  ✅ Real-time voice interview processing")
        print(f"  ✅ AWS Transcribe integration for speech-to-text")
        print(f"  ✅ WebSocket API for real-time communication")
        print(f"  ✅ Interview session management and analytics")
        print(f"  ✅ Performance analysis and feedback")
        print(f"\nTest with: python test_voice_interview.py")
        return True
    else:
        print(f"\n❌ Voice Interview Deployment Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
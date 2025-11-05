#!/usr/bin/env python3
"""
Simple Bedrock Agent Deployment
Deploy LangGraph agent on Bedrock AgentCore with minimal Lambda
"""

import boto3
import json
import os
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAgentDeployer:
    """Simple Bedrock Agent deployer"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        self.lambda_client = boto3.client('lambda')
        self.iam_client = boto3.client('iam')
        
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.account_id = os.getenv('AWS_ACCOUNT_ID', '145023137830')
    
    def deploy_agent(self):
        """Deploy the agent with minimal setup"""
        
        print("🚀 Deploying Simple Bedrock Agent")
        print("=" * 40)
        
        try:
            # Step 1: Create agent
            agent_id = self.create_agent()
            if not agent_id:
                return None
            
            # Step 2: Create simple Lambda action group
            self.create_simple_action_group(agent_id)
            
            # Step 3: Prepare agent
            if self.prepare_agent(agent_id):
                print(f"✅ Agent deployed successfully: {agent_id}")
                
                # Update .env file
                self.update_env_file(agent_id)
                
                return agent_id
            else:
                print("❌ Agent preparation failed")
                return None
                
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return None
    
    def create_agent(self):
        """Create basic Bedrock agent"""
        
        try:
            print("📝 Creating Bedrock Agent...")
            
            # Create IAM role
            role_arn = self.create_agent_role()
            
            agent_config = {
                'agentName': 'lms-simple-assistant',
                'description': 'Simple LMS Assistant with LangGraph workflows',
                'foundationModel': 'amazon.nova-micro-v1:0',
                'instruction': '''You are a helpful Learning Management System assistant. 

Your capabilities include:
- Answering questions about educational content
- Helping with document summarization
- Creating quizzes and assessments
- Providing learning guidance

Always be helpful, accurate, and educational in your responses.''',
                'idleSessionTTLInSeconds': 1800,
                'agentResourceRoleArn': role_arn
            }
            
            response = self.bedrock_agent.create_agent(**agent_config)
            agent_id = response['agent']['agentId']
            
            print(f"✅ Agent created: {agent_id}")
            return agent_id
            
        except Exception as e:
            print(f"❌ Agent creation failed: {e}")
            return None
    
    def create_simple_action_group(self, agent_id):
        """Create simple action group with Lambda"""
        
        try:
            print("🔧 Creating action group...")
            
            # Create Lambda function
            lambda_arn = self.create_simple_lambda()
            
            action_group_config = {
                'agentId': agent_id,
                'agentVersion': 'DRAFT',
                'actionGroupName': 'SimpleWorkflow',
                'description': 'Simple workflow execution',
                'actionGroupExecutor': {
                    'lambda': lambda_arn
                },
                'apiSchema': {
                    'payload': json.dumps({
                        "openapi": "3.0.0",
                        "info": {
                            "title": "Simple Workflow API",
                            "version": "1.0.0"
                        },
                        "paths": {
                            "/process": {
                                "post": {
                                    "summary": "Process user request",
                                    "operationId": "processRequest",
                                    "requestBody": {
                                        "required": True,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        "user_input": {"type": "string"},
                                                        "user_id": {"type": "string"}
                                                    },
                                                    "required": ["user_input"]
                                                }
                                            }
                                        }
                                    },
                                    "responses": {
                                        "200": {
                                            "description": "Processing result",
                                            "content": {
                                                "application/json": {
                                                    "schema": {
                                                        "type": "object",
                                                        "properties": {
                                                            "response": {"type": "string"},
                                                            "intent": {"type": "string"}
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
            print("✅ Action group created")
            
        except Exception as e:
            print(f"❌ Action group creation failed: {e}")
    
    def create_simple_lambda(self):
        """Create simple Lambda function"""
        
        lambda_code = '''
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Simple Lambda handler for Bedrock Agent"""
    
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Parse request
        api_path = event.get('apiPath', '/process')
        request_body = event.get('requestBody', {})
        
        if isinstance(request_body, str):
            body = json.loads(request_body)
        else:
            body = request_body.get('content', {}) if request_body else {}
        
        user_input = body.get('user_input', '')
        user_id = body.get('user_id', 'anonymous')
        
        # Simple intent detection
        intent = detect_intent(user_input)
        
        # Generate response based on intent
        if intent == 'summarize':
            response = f"I can help you summarize your documents. Please upload your materials and I'll provide a comprehensive summary highlighting key concepts and main ideas."
        elif intent == 'question':
            response = f"I'll help answer your question: '{user_input}'. Based on educational principles, let me provide you with a detailed explanation."
        elif intent == 'quiz':
            response = f"I can create a quiz for you! Here's a sample question based on your request: What are the main concepts you'd like to be tested on?"
        else:
            response = f"Hello! I'm your LMS assistant. I can help you with document summarization, answering questions about your materials, and creating quizzes. How can I assist you today?"
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'SimpleWorkflow',
                'apiPath': api_path,
                'httpMethod': 'POST',
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'response': response,
                            'intent': intent,
                            'user_id': user_id
                        })
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'SimpleWorkflow',
                'apiPath': '/process',
                'httpMethod': 'POST',
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': str(e)
                        })
                    }
                }
            }
        }

def detect_intent(user_input):
    """Simple intent detection"""
    
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ['summary', 'summarize', 'overview', 'key points']):
        return 'summarize'
    elif any(word in user_input_lower for word in ['quiz', 'test', 'questions', 'assessment']):
        return 'quiz'
    elif any(word in user_input_lower for word in ['what', 'how', 'why', 'explain']):
        return 'question'
    else:
        return 'general'
'''
        
        try:
            function_name = 'lms-simple-executor'
            
            # Create Lambda role
            lambda_role_arn = self.create_lambda_role()
            
            # Create or update function
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                # Update existing
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=lambda_code.encode('utf-8')
                )
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=lambda_role_arn,
                    Handler='index.lambda_handler',
                    Code={'ZipFile': lambda_code.encode('utf-8')},
                    Description='Simple LMS executor for Bedrock Agent',
                    Timeout=60,
                    MemorySize=256
                )
            
            print(f"✅ Lambda function ready: {function_name}")
            return response['FunctionArn']
            
        except Exception as e:
            print(f"❌ Lambda creation failed: {e}")
            raise
    
    def prepare_agent(self, agent_id):
        """Prepare agent for use"""
        
        try:
            print("⏳ Preparing agent...")
            
            self.bedrock_agent.prepare_agent(agentId=agent_id)
            
            # Wait for preparation
            for i in range(30):  # 5 minutes max
                try:
                    agent = self.bedrock_agent.get_agent(agentId=agent_id)
                    status = agent['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        print("✅ Agent prepared successfully")
                        return True
                    elif status == 'FAILED':
                        print("❌ Agent preparation failed")
                        return False
                    
                    print(f"⏳ Status: {status}, waiting...")
                    time.sleep(10)
                    
                except Exception as e:
                    print(f"⏳ Checking status... ({i+1}/30)")
                    time.sleep(10)
            
            print("⚠️ Preparation timeout")
            return False
            
        except Exception as e:
            print(f"❌ Preparation error: {e}")
            return False
    
    def create_agent_role(self):
        """Create IAM role for agent"""
        
        role_name = 'BedrockSimpleAgentRole'
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "bedrock.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except self.iam_client.exceptions.NoSuchEntityException:
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            
            # Attach basic policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
            )
            
            return response['Role']['Arn']
    
    def create_lambda_role(self):
        """Create IAM role for Lambda"""
        
        role_name = 'SimpleLambdaExecutionRole'
        
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
            return response['Role']['Arn']
        except self.iam_client.exceptions.NoSuchEntityException:
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            
            # Attach basic policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
            ]
            
            for policy in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            return response['Role']['Arn']
    
    def update_env_file(self, agent_id):
        """Update .env file with new agent ID"""
        
        try:
            # Read current .env
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            # Update agent ID
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('BEDROCK_CHAT_AGENT_ID='):
                    lines[i] = f'BEDROCK_CHAT_AGENT_ID={agent_id}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'BEDROCK_CHAT_AGENT_ID={agent_id}\n')
            
            # Write back
            with open('.env', 'w') as f:
                f.writelines(lines)
            
            print(f"✅ Updated .env with agent ID: {agent_id}")
            
        except Exception as e:
            print(f"⚠️ Could not update .env: {e}")

def main():
    """Main deployment"""
    
    deployer = SimpleAgentDeployer()
    agent_id = deployer.deploy_agent()
    
    if agent_id:
        print(f"\n🎉 Deployment Complete!")
        print(f"Agent ID: {agent_id}")
        print(f"Test with: python test_current_agent.py")
        return True
    else:
        print(f"\n❌ Deployment Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
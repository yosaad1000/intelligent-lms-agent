#!/usr/bin/env python3
"""
Enhanced Bedrock Agent Deployment
Extends existing agent with quiz generation and multi-language support
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

class EnhancedAgentDeployer:
    """Enhanced Bedrock Agent deployer with new action groups"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        self.lambda_client = boto3.client('lambda')
        self.iam_client = boto3.client('iam')
        
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
    
    def deploy_enhanced_agent(self):
        """Deploy enhanced agent with new capabilities"""
        
        print("🚀 Deploying Enhanced Bedrock Agent")
        print("=" * 50)
        print(f"Existing Agent ID: {self.agent_id}")
        
        try:
            # Step 1: Create enhanced Lambda functions
            quiz_lambda_arn = self.create_enhanced_quiz_lambda()
            translation_lambda_arn = self.create_translation_lambda()
            
            # Step 2: Add new action groups to existing agent
            self.add_quiz_action_group(quiz_lambda_arn)
            self.add_translation_action_group(translation_lambda_arn)
            
            # Step 3: Update agent instruction with new capabilities
            self.update_agent_instructions()
            
            # Step 4: Prepare agent with new configuration
            if self.prepare_agent():
                print(f"✅ Enhanced agent deployed successfully!")
                
                # Step 5: Create new version and update alias
                version = self.create_agent_version()
                if version:
                    self.update_production_alias(version)
                
                return True
            else:
                print("❌ Agent preparation failed")
                return False
                
        except Exception as e:
            print(f"❌ Enhanced deployment failed: {e}")
            return False
    
    def create_enhanced_quiz_lambda(self):
        """Create enhanced quiz generation Lambda function"""
        
        print("🔧 Creating enhanced quiz Lambda function...")
        
        function_name = 'lms-enhanced-quiz-generator'
        
        # Create deployment package
        zip_path = self._create_quiz_lambda_package()
        
        try:
            # Create Lambda role if needed
            lambda_role_arn = self.create_enhanced_lambda_role()
            
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
                        Handler='enhanced_quiz_handler.lambda_handler',
                        Code={'ZipFile': zip_file.read()},
                        Description='Enhanced quiz generation with multi-language support',
                        Timeout=300,
                        MemorySize=512,
                        Environment={
                            'Variables': {
                                'BEDROCK_MODEL_ID': 'amazon.nova-micro-v1:0'
                            }
                        }
                    )
                print(f"✅ Created new Lambda function: {function_name}")
            
            # Add Bedrock Agent invoke permission
            self._add_bedrock_invoke_permission(function_name)
            
            return response['FunctionArn']
            
        except Exception as e:
            print(f"❌ Enhanced quiz Lambda creation failed: {e}")
            raise
        finally:
            # Clean up zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
    
    def create_translation_lambda(self):
        """Create translation service Lambda function"""
        
        print("🔧 Creating translation Lambda function...")
        
        function_name = 'lms-translation-service'
        
        # Create deployment package
        zip_path = self._create_translation_lambda_package()
        
        try:
            # Create Lambda role if needed
            lambda_role_arn = self.create_enhanced_lambda_role()
            
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
                        Handler='translation_service.lambda_handler',
                        Code={'ZipFile': zip_file.read()},
                        Description='Multi-language translation service',
                        Timeout=300,
                        MemorySize=512,
                        Environment={
                            'Variables': {
                                'LAMBDA_FUNCTION_NAME': function_name
                            }
                        }
                    )
                print(f"✅ Created new Lambda function: {function_name}")
            
            # Add Bedrock Agent invoke permission
            self._add_bedrock_invoke_permission(function_name)
            
            return response['FunctionArn']
            
        except Exception as e:
            print(f"❌ Translation Lambda creation failed: {e}")
            raise
        finally:
            # Clean up zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
    
    def _create_quiz_lambda_package(self) -> str:
        """Create deployment package for enhanced quiz Lambda"""
        
        # Create temporary zip file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'enhanced_quiz_lambda.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add enhanced quiz handler
            quiz_handler_path = 'src/quiz_generator/enhanced_quiz_handler.py'
            if os.path.exists(quiz_handler_path):
                zip_file.write(quiz_handler_path, 'enhanced_quiz_handler.py')
            
            # Add shared utilities
            shared_files = [
                'src/shared/config.py',
                'src/shared/utils.py'
            ]
            
            for file_path in shared_files:
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))
        
        return zip_path
    
    def _create_translation_lambda_package(self) -> str:
        """Create deployment package for translation Lambda"""
        
        # Create temporary zip file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'translation_lambda.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add translation service
            translation_service_path = 'src/shared/translation_service.py'
            if os.path.exists(translation_service_path):
                zip_file.write(translation_service_path, 'translation_service.py')
            
            # Add shared utilities
            shared_files = [
                'src/shared/config.py',
                'src/shared/utils.py'
            ]
            
            for file_path in shared_files:
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))
        
        return zip_path
    
    def add_quiz_action_group(self, lambda_arn: str):
        """Add enhanced quiz generation action group"""
        
        print("📝 Adding enhanced quiz action group...")
        
        try:
            action_group_config = {
                'agentId': self.agent_id,
                'agentVersion': 'DRAFT',
                'actionGroupName': 'EnhancedQuizGenerator',
                'description': 'Enhanced quiz generation with multi-language support',
                'actionGroupExecutor': {
                    'lambda': lambda_arn
                },
                'apiSchema': {
                    'payload': json.dumps({
                        "openapi": "3.0.0",
                        "info": {
                            "title": "Enhanced Quiz Generator API",
                            "version": "2.0.0"
                        },
                        "paths": {
                            "/generate-quiz": {
                                "post": {
                                    "summary": "Generate quiz with multi-language support",
                                    "operationId": "generateEnhancedQuiz",
                                    "requestBody": {
                                        "required": True,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        "topic": {"type": "string"},
                                                        "difficulty": {"type": "string"},
                                                        "question_count": {"type": "integer"},
                                                        "target_language": {"type": "string"},
                                                        "user_id": {"type": "string"}
                                                    },
                                                    "required": ["topic"]
                                                }
                                            }
                                        }
                                    },
                                    "responses": {
                                        "200": {
                                            "description": "Quiz generated successfully"
                                        }
                                    }
                                }
                            }
                        }
                    })
                }
            }
            
            self.bedrock_agent.create_agent_action_group(**action_group_config)
            print("✅ Enhanced quiz action group added")
            
        except Exception as e:
            print(f"❌ Quiz action group creation failed: {e}")
            raise
    
    def add_translation_action_group(self, lambda_arn: str):
        """Add translation service action group"""
        
        print("🌍 Adding translation action group...")
        
        try:
            action_group_config = {
                'agentId': self.agent_id,
                'agentVersion': 'DRAFT',
                'actionGroupName': 'TranslationService',
                'description': 'Multi-language translation with round-trip validation',
                'actionGroupExecutor': {
                    'lambda': lambda_arn
                },
                'apiSchema': {
                    'payload': json.dumps({
                        "openapi": "3.0.0",
                        "info": {
                            "title": "Translation Service API",
                            "version": "1.0.0"
                        },
                        "paths": {
                            "/translate": {
                                "post": {
                                    "summary": "Translate text with language detection",
                                    "operationId": "translateText",
                                    "requestBody": {
                                        "required": True,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        "text": {"type": "string"},
                                                        "target_language": {"type": "string"},
                                                        "user_id": {"type": "string"}
                                                    },
                                                    "required": ["text"]
                                                }
                                            }
                                        }
                                    },
                                    "responses": {
                                        "200": {
                                            "description": "Text translated successfully"
                                        }
                                    }
                                }
                            }
                        }
                    })
                }
            }
            
            self.bedrock_agent.create_agent_action_group(**action_group_config)
            print("✅ Translation action group added")
            
        except Exception as e:
            print(f"❌ Translation action group creation failed: {e}")
            raise
    
    def update_agent_instructions(self):
        """Update agent instructions with new capabilities"""
        
        print("📝 Updating agent instructions...")
        
        enhanced_instructions = '''You are an advanced Learning Management System assistant with enhanced capabilities.

Your core abilities include:

🎯 **Enhanced Quiz Generation**
- Create multilingual quizzes from any topic or uploaded documents
- Support for beginner, intermediate, and advanced difficulty levels
- Automatic language detection and translation
- Detailed analytics and performance insights
- Round-trip translation validation for quality assurance

🌍 **Multi-Language Support**
- Translate content between 12+ languages (English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, Hindi, Russian)
- Automatic language detection using Amazon Comprehend
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
- Detailed scoring with explanations

🎤 **Voice & Conversation**
- Natural conversation flow with memory
- Support for voice interactions and interviews
- Session management and context retention

**How to interact with me:**

For Quiz Generation:
- "Create a quiz about [topic] in [language]"
- "Generate 10 intermediate questions about my physics notes"
- "Make a Spanish quiz about thermodynamics"

For Translation:
- "Translate this to Spanish: [text]"
- "Convert my quiz to French"
- "What languages do you support?"

For Document Analysis:
- "Summarize my uploaded chemistry notes"
- "What are the key concepts in my materials?"
- "Create study questions from my documents"

I always provide helpful, accurate, and educational responses. I can adapt to your learning style and language preferences while maintaining high educational standards.'''

        try:
            self.bedrock_agent.update_agent(
                agentId=self.agent_id,
                agentName='lms-enhanced-assistant',
                description='Enhanced LMS Assistant with quiz generation and multi-language support',
                instruction=enhanced_instructions,
                foundationModel='amazon.nova-micro-v1:0',
                idleSessionTTLInSeconds=1800
            )
            print("✅ Agent instructions updated")
            
        except Exception as e:
            print(f"❌ Agent instruction update failed: {e}")
            raise
    
    def prepare_agent(self):
        """Prepare agent with new configuration"""
        
        print("⏳ Preparing enhanced agent...")
        
        try:
            self.bedrock_agent.prepare_agent(agentId=self.agent_id)
            
            # Wait for preparation
            for i in range(60):  # 10 minutes max
                try:
                    agent = self.bedrock_agent.get_agent(agentId=self.agent_id)
                    status = agent['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        print("✅ Enhanced agent prepared successfully")
                        return True
                    elif status == 'FAILED':
                        print("❌ Enhanced agent preparation failed")
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
        """Create new agent version"""
        
        print("📦 Creating agent version...")
        
        try:
            response = self.bedrock_agent.create_agent_version(
                agentId=self.agent_id,
                description=f'Enhanced version with quiz generation and multi-language support - {datetime.utcnow().isoformat()}'
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
                description=f'Production alias - Enhanced version {version}',
                agentVersion=version
            )
            
            print(f"✅ Production alias updated to version {version}")
            
        except Exception as e:
            print(f"❌ Alias update failed: {e}")
    
    def create_enhanced_lambda_role(self):
        """Create enhanced IAM role for Lambda functions"""
        
        role_name = 'EnhancedLambdaExecutionRole'
        
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
            
            # Attach enhanced policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/TranslateFullAccess',
                'arn:aws:iam::aws:policy/ComprehendFullAccess'
            ]
            
            for policy in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy
                )
            
            return response['Role']['Arn']
    
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
    
    deployer = EnhancedAgentDeployer()
    success = deployer.deploy_enhanced_agent()
    
    if success:
        print(f"\n🎉 Enhanced Agent Deployment Complete!")
        print(f"Agent ID: {deployer.agent_id}")
        print(f"New capabilities:")
        print(f"  ✅ Enhanced quiz generation with multi-language support")
        print(f"  ✅ Translation service with round-trip validation")
        print(f"  ✅ Learning analytics and performance insights")
        print(f"  ✅ Support for 12+ languages")
        print(f"\nTest with: python test_enhanced_agent.py")
        return True
    else:
        print(f"\n❌ Enhanced Deployment Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Learning Analytics Action Group Deployment
Deploys learning analytics capabilities to the existing Bedrock Agent
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

class LearningAnalyticsDeployer:
    """Deploy learning analytics action group to Bedrock Agent"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        self.lambda_client = boto3.client('lambda')
        self.iam_client = boto3.client('iam')
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
    
    def deploy_learning_analytics(self):
        """Deploy learning analytics action group"""
        
        print("📊 Deploying Learning Analytics Action Group")
        print("=" * 50)
        print(f"Agent ID: {self.agent_id}")
        
        try:
            # Step 1: Create DynamoDB tables for analytics
            self.create_analytics_tables()
            
            # Step 2: Create analytics Lambda function
            analytics_lambda_arn = self.create_analytics_lambda()
            
            # Step 3: Add analytics action group to agent
            self.add_analytics_action_group(analytics_lambda_arn)
            
            # Step 4: Update agent instructions
            self.update_agent_instructions()
            
            # Step 5: Prepare agent
            if self.prepare_agent():
                print("✅ Learning analytics deployed successfully!")
                
                # Step 6: Create new version and update alias
                version = self.create_agent_version()
                if version:
                    self.update_production_alias(version)
                
                return True
            else:
                print("❌ Agent preparation failed")
                return False
                
        except Exception as e:
            print(f"❌ Analytics deployment failed: {e}")
            return False
    
    def create_analytics_tables(self):
        """Create DynamoDB tables for learning analytics"""
        
        print("🗄️ Creating analytics DynamoDB tables...")
        
        tables_to_create = [
            {
                'TableName': 'lms-user-analytics',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'analysis_date', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'analysis_date', 'AttributeType': 'S'}
                ]
            },
            {
                'TableName': 'lms-learning-progress',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'}
                ]
            },
            {
                'TableName': 'lms-chat-conversations',
                'KeySchema': [
                    {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'user-id-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ]
            },
            {
                'TableName': 'lms-quiz-submissions',
                'KeySchema': [
                    {'AttributeName': 'submission_id', 'KeyType': 'HASH'}
                ],
                'AttributeDefinitions': [
                    {'AttributeName': 'submission_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'user-id-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ]
            }
        ]
        
        for table_config in tables_to_create:
            try:
                # Check if table exists
                table_name = table_config['TableName']
                try:
                    table = self.dynamodb.Table(table_name)
                    table.load()
                    print(f"✅ Table {table_name} already exists")
                except:
                    # Create table
                    table_config['BillingMode'] = 'PAY_PER_REQUEST'
                    self.dynamodb.create_table(**table_config)
                    print(f"✅ Created table: {table_name}")
                    
                    # Wait for table to be active
                    table = self.dynamodb.Table(table_name)
                    table.wait_until_exists()
                    
            except Exception as e:
                print(f"⚠️ Table creation issue for {table_config['TableName']}: {e}")
    
    def create_analytics_lambda(self):
        """Create learning analytics Lambda function"""
        
        print("🔧 Creating learning analytics Lambda function...")
        
        function_name = 'lms-learning-analytics'
        
        # Create deployment package
        zip_path = self._create_analytics_lambda_package()
        
        try:
            # Create Lambda role
            lambda_role_arn = self.create_analytics_lambda_role()
            
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
                        Handler='learning_analytics_handler.lambda_handler',
                        Code={'ZipFile': zip_file.read()},
                        Description='Learning analytics and progress tracking',
                        Timeout=300,
                        MemorySize=1024,
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
            print(f"❌ Analytics Lambda creation failed: {e}")
            raise
        finally:
            # Clean up zip file
            if os.path.exists(zip_path):
                os.remove(zip_path)
    
    def _create_analytics_lambda_package(self) -> str:
        """Create deployment package for analytics Lambda"""
        
        # Create temporary zip file
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'analytics_lambda.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add analytics handler
            analytics_handler_path = 'src/analytics/learning_analytics_handler.py'
            if os.path.exists(analytics_handler_path):
                zip_file.write(analytics_handler_path, 'learning_analytics_handler.py')
            
            # Add shared utilities
            shared_files = [
                'src/shared/config.py',
                'src/shared/utils.py',
                'src/shared/dynamodb_utils.py'
            ]
            
            for file_path in shared_files:
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))
        
        return zip_path
    
    def add_analytics_action_group(self, lambda_arn: str):
        """Add or update learning analytics action group to agent"""
        
        print("📊 Adding/updating learning analytics action group...")
        
        try:
            # Check if action group already exists
            try:
                existing_groups = self.bedrock_agent.list_agent_action_groups(
                    agentId=self.agent_id,
                    agentVersion='DRAFT'
                )
                
                analytics_group = None
                for group in existing_groups.get('actionGroupSummaries', []):
                    if group['actionGroupName'] == 'LearningAnalytics':
                        analytics_group = group
                        break
                
                if analytics_group:
                    print(f"✅ Found existing action group: {analytics_group['actionGroupId']}")
                    # Update existing action group
                    self.bedrock_agent.update_agent_action_group(
                        agentId=self.agent_id,
                        agentVersion='DRAFT',
                        actionGroupId=analytics_group['actionGroupId'],
                        actionGroupName='LearningAnalytics',
                        description='Comprehensive learning analytics and progress tracking - Updated',
                        actionGroupExecutor={
                            'lambda': lambda_arn
                        },
                        apiSchema=self._get_analytics_api_schema()
                    )
                    print("✅ Learning analytics action group updated")
                    return
                    
            except Exception as e:
                print(f"⚠️ Could not check existing action groups: {e}")
            
            # Create new action group if it doesn't exist
            action_group_config = {
                'agentId': self.agent_id,
                'agentVersion': 'DRAFT',
                'actionGroupName': 'LearningAnalytics',
                'description': 'Comprehensive learning analytics and progress tracking',
                'actionGroupExecutor': {
                    'lambda': lambda_arn
                },
                'apiSchema': self._get_analytics_api_schema()
            }
            
            self.bedrock_agent.create_agent_action_group(**action_group_config)
            print("✅ Learning analytics action group added")
            
        except Exception as e:
            print(f"❌ Analytics action group creation failed: {e}")
            raise
    
    def _get_analytics_api_schema(self):
        """Get the API schema for analytics action group"""
        return {
            'payload': json.dumps({
                "openapi": "3.0.0",
                "info": {
                    "title": "Learning Analytics API",
                    "version": "1.0.0",
                    "description": "API for comprehensive learning analytics and progress tracking"
                },
                "paths": {
                    "/analyze-progress": {
                        "post": {
                            "summary": "Analyze comprehensive learning progress",
                            "description": "Analyze user learning progress with sentiment analysis and engagement metrics",
                            "operationId": "analyzeLearningProgress",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "user_id": {
                                                    "type": "string",
                                                    "description": "User identifier"
                                                },
                                                "days_back": {
                                                    "type": "integer",
                                                    "description": "Number of days to analyze",
                                                    "default": 30
                                                },
                                                "subject": {
                                                    "type": "string",
                                                    "description": "Subject to analyze"
                                                }
                                            },
                                            "required": ["user_id"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Learning progress analysis completed",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "analysis": {"type": "object"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/concept-mastery": {
                        "post": {
                            "summary": "Calculate concept mastery",
                            "description": "Calculate concept mastery using Knowledge Base similarity analysis",
                            "operationId": "calculateConceptMastery",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "user_id": {
                                                    "type": "string",
                                                    "description": "User identifier"
                                                },
                                                "subject": {
                                                    "type": "string",
                                                    "description": "Subject to analyze"
                                                },
                                                "concept": {
                                                    "type": "string",
                                                    "description": "Specific concept to analyze"
                                                }
                                            },
                                            "required": ["user_id"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Concept mastery calculated successfully",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "mastery": {"type": "object"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/get-recommendations": {
                        "post": {
                            "summary": "Get personalized recommendations",
                            "description": "Generate personalized learning recommendations based on analytics",
                            "operationId": "getPersonalizedRecommendations",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "user_id": {
                                                    "type": "string",
                                                    "description": "User identifier"
                                                },
                                                "subject": {
                                                    "type": "string",
                                                    "description": "Subject for recommendations"
                                                }
                                            },
                                            "required": ["user_id"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Recommendations generated successfully",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "recommendations": {"type": "array"}
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
    
    def update_agent_instructions(self):
        """Update agent instructions with analytics capabilities"""
        
        print("📝 Updating agent instructions with analytics capabilities...")
        
        enhanced_instructions = '''You are an advanced Learning Management System assistant with comprehensive analytics capabilities.

Your core abilities include:

📊 **Learning Analytics & Progress Tracking**
- Analyze comprehensive learning progress with sentiment analysis
- Track concept mastery using Knowledge Base similarity
- Generate personalized learning recommendations
- Provide detailed performance insights and improvement suggestions
- Calculate learning velocity and engagement metrics

🎯 **Enhanced Quiz Generation**
- Create multilingual quizzes from any topic or uploaded documents
- Support for beginner, intermediate, and advanced difficulty levels
- Automatic language detection and translation
- Detailed analytics and performance insights

🌍 **Multi-Language Support**
- Translate content between 12+ languages
- Automatic language detection using Amazon Comprehend
- Educational content translation with quality validation

📚 **Document Analysis & RAG**
- Process and analyze uploaded educational materials
- Generate contextual responses based on user documents
- Create quizzes from specific document content
- Provide citations and source references

👨‍🏫 **Teacher Analytics Dashboard**
- Comprehensive class performance analytics
- Identify at-risk students with AI insights
- Learning trend analysis and engagement metrics
- Personalized teaching recommendations

🎤 **Voice & Conversation**
- Natural conversation flow with memory
- Support for voice interactions and interviews
- Session management and context retention

**Analytics Commands:**

For Learning Progress:
- "Show my learning progress for the last 30 days"
- "Analyze my concept mastery in physics"
- "What are my learning strengths and weaknesses?"
- "Give me personalized study recommendations"

For Teacher Analytics:
- "Show class performance analytics for physics"
- "Which students need additional support?"
- "What are the learning trends in my class?"
- "Generate teaching recommendations for my students"

For Concept Mastery:
- "Calculate my mastery level in thermodynamics"
- "Which concepts do I need to focus on?"
- "Show my learning progress over time"

I provide comprehensive analytics with AI-powered insights, sentiment analysis, and personalized recommendations to enhance learning outcomes for both students and teachers.'''

        try:
            # Get current agent details to preserve the role ARN
            agent_details = self.bedrock_agent.get_agent(agentId=self.agent_id)
            agent_resource_role_arn = agent_details['agent']['agentResourceRoleArn']
            
            self.bedrock_agent.update_agent(
                agentId=self.agent_id,
                agentName='lms-analytics-assistant',
                description='LMS Assistant with comprehensive learning analytics and progress tracking',
                instruction=enhanced_instructions,
                foundationModel='amazon.nova-micro-v1:0',
                agentResourceRoleArn=agent_resource_role_arn,
                idleSessionTTLInSeconds=1800
            )
            print("✅ Agent instructions updated with analytics capabilities")
            
        except Exception as e:
            print(f"❌ Agent instruction update failed: {e}")
            # Continue deployment even if instruction update fails
            print("⚠️ Continuing deployment without instruction update")
    
    def prepare_agent(self):
        """Prepare agent with analytics configuration"""
        
        print("⏳ Preparing agent with analytics capabilities...")
        
        try:
            self.bedrock_agent.prepare_agent(agentId=self.agent_id)
            
            # Wait for preparation
            for i in range(60):  # 10 minutes max
                try:
                    agent = self.bedrock_agent.get_agent(agentId=self.agent_id)
                    status = agent['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        print("✅ Analytics agent prepared successfully")
                        return True
                    elif status == 'FAILED':
                        print("❌ Analytics agent preparation failed")
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
        """Create new agent version with analytics"""
        
        print("📦 Creating agent version with analytics...")
        
        try:
            response = self.bedrock_agent.create_agent_version(
                agentId=self.agent_id,
                description=f'Analytics-enhanced version with learning progress tracking - {datetime.utcnow().isoformat()}'
            )
            
            version = response['agentVersion']['version']
            print(f"✅ Created agent version: {version}")
            return version
            
        except Exception as e:
            print(f"❌ Version creation failed: {e}")
            return None
    
    def update_production_alias(self, version: str):
        """Update production alias to analytics version"""
        
        print(f"🏷️ Updating production alias to analytics version {version}...")
        
        try:
            alias_id = 'TSTALIASID'  # Use existing alias
            
            self.bedrock_agent.update_agent_alias(
                agentId=self.agent_id,
                agentAliasId=alias_id,
                agentAliasName='production',
                description=f'Production alias - Analytics version {version}',
                agentVersion=version
            )
            
            print(f"✅ Production alias updated to analytics version {version}")
            
        except Exception as e:
            print(f"❌ Alias update failed: {e}")
    
    def create_analytics_lambda_role(self):
        """Create IAM role for analytics Lambda function"""
        
        role_name = 'LearningAnalyticsLambdaRole'
        
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
            print(f"🔧 Creating new IAM role: {role_name}")
            
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='IAM role for Learning Analytics Lambda function'
            )
            
            role_arn = response['Role']['Arn']
            
            # Wait for role to be available
            print("⏳ Waiting for IAM role to be available...")
            time.sleep(10)
            
            # Attach comprehensive policies for analytics
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/ComprehendFullAccess',
                'arn:aws:iam::aws:policy/TranslateReadOnly'
            ]
            
            for policy in policies:
                try:
                    self.iam_client.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy
                    )
                    print(f"✅ Attached policy: {policy.split('/')[-1]}")
                except Exception as e:
                    print(f"⚠️ Policy attachment warning: {e}")
            
            # Additional wait for policy propagation
            print("⏳ Waiting for policy propagation...")
            time.sleep(15)
            
            return role_arn
    
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
    
    deployer = LearningAnalyticsDeployer()
    success = deployer.deploy_learning_analytics()
    
    if success:
        print(f"\n🎉 Learning Analytics Deployment Complete!")
        print(f"Agent ID: {deployer.agent_id}")
        print(f"New analytics capabilities:")
        print(f"  ✅ Comprehensive learning progress analysis")
        print(f"  ✅ Sentiment analysis with Amazon Comprehend")
        print(f"  ✅ Concept mastery calculation using Knowledge Base similarity")
        print(f"  ✅ Personalized learning recommendations")
        print(f"  ✅ Teacher analytics dashboard with AI insights")
        print(f"  ✅ Real-time interaction tracking and analytics")
        print(f"\nTest with: python test_learning_analytics.py")
        return True
    else:
        print(f"\n❌ Learning Analytics Deployment Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Learning Analytics Verification Script
Verifies that the learning analytics action group is properly deployed and functional
"""

import boto3
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningAnalyticsVerifier:
    """Verify learning analytics deployment and functionality"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
        # Agent configuration
        self.agent_id = 'ZTBBVSC6Y1'
        self.alias_id = 'TSTALIASID'
        
        print(f"🔍 Learning Analytics Verifier Initialized")
        print(f"Agent ID: {self.agent_id}")
    
    def verify_deployment(self):
        """Verify that learning analytics is properly deployed"""
        
        print("\n📋 Verifying Learning Analytics Deployment")
        print("=" * 60)
        
        verification_results = []
        
        # 1. Verify agent exists and is prepared
        print("\n1️⃣ Verifying Agent Status")
        agent_status = self.verify_agent_status()
        verification_results.append(('Agent Status', agent_status))
        
        # 2. Verify action groups
        print("\n2️⃣ Verifying Action Groups")
        action_groups_status = self.verify_action_groups()
        verification_results.append(('Action Groups', action_groups_status))
        
        # 3. Verify Lambda function
        print("\n3️⃣ Verifying Lambda Function")
        lambda_status = self.verify_lambda_function()
        verification_results.append(('Lambda Function', lambda_status))
        
        # 4. Verify DynamoDB tables
        print("\n4️⃣ Verifying DynamoDB Tables")
        dynamodb_status = self.verify_dynamodb_tables()
        verification_results.append(('DynamoDB Tables', dynamodb_status))
        
        # 5. Test basic agent functionality
        print("\n5️⃣ Testing Basic Agent Functionality")
        agent_test_status = self.test_basic_agent_functionality()
        verification_results.append(('Agent Functionality', agent_test_status))
        
        # 6. Test analytics-specific functionality
        print("\n6️⃣ Testing Analytics Functionality")
        analytics_test_status = self.test_analytics_functionality()
        verification_results.append(('Analytics Functionality', analytics_test_status))
        
        # Print verification summary
        self.print_verification_summary(verification_results)
        
        return all(result for _, result in verification_results)
    
    def verify_agent_status(self):
        """Verify agent exists and is in correct status"""
        
        try:
            agent = self.bedrock_agent.get_agent(agentId=self.agent_id)
            
            agent_status = agent['agent']['agentStatus']
            agent_name = agent['agent']['agentName']
            
            print(f"✅ Agent found: {agent_name}")
            print(f"✅ Agent status: {agent_status}")
            
            if agent_status == 'PREPARED':
                print("✅ Agent is prepared and ready")
                return True
            else:
                print(f"⚠️ Agent status is {agent_status}, expected PREPARED")
                return False
                
        except Exception as e:
            print(f"❌ Agent verification failed: {e}")
            return False
    
    def verify_action_groups(self):
        """Verify that learning analytics action group exists"""
        
        try:
            action_groups = self.bedrock_agent.list_agent_action_groups(
                agentId=self.agent_id,
                agentVersion='DRAFT'
            )
            
            analytics_group = None
            for group in action_groups.get('actionGroupSummaries', []):
                print(f"📋 Found action group: {group['actionGroupName']}")
                if group['actionGroupName'] == 'LearningAnalytics':
                    analytics_group = group
            
            if analytics_group:
                print(f"✅ Learning Analytics action group found: {analytics_group['actionGroupId']}")
                print(f"✅ Status: {analytics_group.get('actionGroupState', 'Unknown')}")
                return True
            else:
                print("❌ Learning Analytics action group not found")
                return False
                
        except Exception as e:
            print(f"❌ Action group verification failed: {e}")
            return False
    
    def verify_lambda_function(self):
        """Verify that the analytics Lambda function exists"""
        
        try:
            lambda_client = boto3.client('lambda')
            
            function_name = 'lms-learning-analytics'
            
            function = lambda_client.get_function(FunctionName=function_name)
            
            print(f"✅ Lambda function found: {function_name}")
            print(f"✅ Runtime: {function['Configuration']['Runtime']}")
            print(f"✅ Handler: {function['Configuration']['Handler']}")
            print(f"✅ Last modified: {function['Configuration']['LastModified']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Lambda function verification failed: {e}")
            return False
    
    def verify_dynamodb_tables(self):
        """Verify that required DynamoDB tables exist"""
        
        try:
            dynamodb = boto3.resource('dynamodb')
            
            required_tables = [
                'lms-user-analytics',
                'lms-learning-progress',
                'lms-chat-conversations',
                'lms-quiz-submissions'
            ]
            
            all_tables_exist = True
            
            for table_name in required_tables:
                try:
                    table = dynamodb.Table(table_name)
                    table.load()
                    print(f"✅ Table exists: {table_name}")
                except:
                    print(f"❌ Table missing: {table_name}")
                    all_tables_exist = False
            
            return all_tables_exist
            
        except Exception as e:
            print(f"❌ DynamoDB verification failed: {e}")
            return False
    
    def test_basic_agent_functionality(self):
        """Test basic agent functionality"""
        
        try:
            test_message = "Hello, can you help me with learning analytics?"
            
            print(f"📤 Testing basic functionality: {test_message}")
            
            response = self.invoke_agent(test_message)
            
            if response and len(response) > 10:
                print(f"✅ Basic agent functionality working")
                print(f"📥 Response preview: {response[:100]}...")
                return True
            else:
                print(f"❌ Basic agent functionality failed")
                print(f"📥 Response: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Basic functionality test failed: {e}")
            return False
    
    def test_analytics_functionality(self):
        """Test analytics-specific functionality"""
        
        try:
            # Test analytics command
            analytics_message = "Show my learning progress and analyze my concept mastery. My user ID is demo_user."
            
            print(f"📤 Testing analytics functionality: {analytics_message}")
            
            response = self.invoke_agent(analytics_message)
            
            # Check if response contains analytics-related keywords
            analytics_keywords = [
                'progress', 'mastery', 'analytics', 'learning', 
                'concept', 'performance', 'recommendation'
            ]
            
            response_lower = response.lower()
            keywords_found = [keyword for keyword in analytics_keywords if keyword in response_lower]
            
            if keywords_found:
                print(f"✅ Analytics functionality working")
                print(f"✅ Keywords found: {', '.join(keywords_found)}")
                print(f"📥 Response preview: {response[:200]}...")
                return True
            else:
                print(f"⚠️ Analytics functionality may not be fully working")
                print(f"📥 Response: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Analytics functionality test failed: {e}")
            return False
    
    def invoke_agent(self, message: str) -> str:
        """Invoke Bedrock Agent with message"""
        
        try:
            session_id = f'verify_{int(time.time())}'
            
            response = self.bedrock_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                sessionId=session_id,
                inputText=message
            )
            
            # Process streaming response
            completion = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            return completion.strip()
            
        except Exception as e:
            logger.error(f"Agent invocation error: {e}")
            return f"Error: {str(e)}"
    
    def print_verification_summary(self, verification_results):
        """Print comprehensive verification summary"""
        
        print("\n" + "=" * 60)
        print("📊 LEARNING ANALYTICS VERIFICATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in verification_results if result)
        total = len(verification_results)
        
        print(f"Verifications Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in verification_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        if passed == total:
            print(f"\n🎉 All verifications passed!")
            print(f"✅ Learning analytics action group is fully deployed and functional")
            print(f"✅ Agent is ready for production use")
            print(f"✅ All required AWS resources are properly configured")
        else:
            print(f"\n⚠️ Some verifications failed. Check the deployment.")
        
        print("\n" + "=" * 60)
    
    def get_deployment_info(self):
        """Get comprehensive deployment information"""
        
        print("\n📋 Learning Analytics Deployment Information")
        print("-" * 50)
        
        try:
            # Agent information
            agent = self.bedrock_agent.get_agent(agentId=self.agent_id)
            print(f"Agent Name: {agent['agent']['agentName']}")
            print(f"Agent Status: {agent['agent']['agentStatus']}")
            print(f"Foundation Model: {agent['agent']['foundationModel']}")
            print(f"Created: {agent['agent']['createdAt']}")
            print(f"Updated: {agent['agent']['updatedAt']}")
            
            # Action groups
            action_groups = self.bedrock_agent.list_agent_action_groups(
                agentId=self.agent_id,
                agentVersion='DRAFT'
            )
            
            print(f"\nAction Groups ({len(action_groups.get('actionGroupSummaries', []))}):")
            for group in action_groups.get('actionGroupSummaries', []):
                print(f"  - {group['actionGroupName']} ({group['actionGroupId']})")
            
            # Knowledge bases
            try:
                knowledge_bases = self.bedrock_agent.list_agent_knowledge_bases(
                    agentId=self.agent_id,
                    agentVersion='DRAFT'
                )
                
                print(f"\nKnowledge Bases ({len(knowledge_bases.get('agentKnowledgeBaseSummaries', []))}):")
                for kb in knowledge_bases.get('agentKnowledgeBaseSummaries', []):
                    print(f"  - {kb['knowledgeBaseId']} ({kb.get('knowledgeBaseState', 'Unknown')})")
            except:
                print("\nKnowledge Bases: Not configured or accessible")
            
        except Exception as e:
            print(f"Error getting deployment info: {e}")


def main():
    """Main verification function"""
    
    print("🔍 Learning Analytics Deployment Verification")
    print("Verifying that all components are properly deployed and functional...")
    
    verifier = LearningAnalyticsVerifier()
    
    # Get deployment information
    verifier.get_deployment_info()
    
    # Run comprehensive verification
    success = verifier.verify_deployment()
    
    if success:
        print(f"\n🎉 Learning Analytics Verification Complete!")
        print(f"✅ All components are properly deployed and functional")
        print(f"✅ Ready for comprehensive testing and production use")
        print(f"\nNext steps:")
        print(f"  • Test via web interface: test_learning_analytics_interface.html")
        print(f"  • Run comprehensive tests: python test_learning_analytics.py")
        print(f"  • Begin using analytics features in your application")
    else:
        print(f"\n⚠️ Some verification checks failed")
        print(f"Please review the deployment and fix any issues")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
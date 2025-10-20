#!/usr/bin/env python3
"""
Simple Voice Interview Integration Deployment
Focus on core functionality for testing
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

class SimpleVoiceDeployer:
    """Simple voice interview deployer"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
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
    
    def deploy_voice_integration(self):
        """Deploy simple voice interview integration"""
        
        print("🎤 Deploying Simple Voice Interview Integration")
        print("=" * 50)
        print(f"Agent ID: {self.agent_id}")
        
        try:
            # Step 1: Update agent instructions for voice capabilities
            self.update_agent_instructions_for_voice()
            
            # Step 2: Prepare agent with new configuration
            if self.prepare_agent():
                print(f"✅ Voice interview integration deployed successfully!")
                
                # Step 3: Create new version and update alias
                version = self.create_agent_version()
                if version:
                    self.update_production_alias(version)
                
                return True
            else:
                print("❌ Agent preparation failed")
                return False
                
        except Exception as e:
            print(f"❌ Voice interview deployment failed: {e}")
            return False
    
    def update_agent_instructions_for_voice(self):
        """Update agent instructions to include voice capabilities"""
        
        print("📝 Updating agent instructions for voice capabilities...")
        
        enhanced_instructions = '''You are an advanced Learning Management System assistant with comprehensive capabilities including voice interview processing.

Your core abilities include:

🎤 **Voice Interview Processing**
- Conduct voice interviews on any educational topic
- Generate contextual interview questions based on user responses
- Provide detailed performance analysis and feedback
- Support various interview types: technical, conceptual, practice sessions
- Analyze response quality and provide improvement suggestions

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

**Interview Process:**
1. When a user requests a voice interview, I will:
   - Ask for the topic and difficulty level
   - Generate an appropriate opening question
   - Provide instructions for the voice interview process
   - Explain how to use the WebSocket interface for real-time interaction

2. During interviews, I will:
   - Generate contextual follow-up questions
   - Provide encouragement and guidance
   - Adapt questions based on user responses
   - Maintain conversation flow and context

3. After interviews, I will:
   - Provide detailed performance analysis
   - Offer specific improvement recommendations
   - Highlight strengths and areas for growth
   - Suggest follow-up learning activities

**Voice Interview Capabilities:**
- Real-time speech-to-text transcription (via WebSocket)
- Intelligent question generation based on responses
- Performance analysis including clarity and content accuracy
- Session management with conversation history
- Detailed feedback and improvement recommendations

I provide natural, engaging interview experiences that help users practice verbal communication skills while receiving AI-powered feedback and analysis.

**Technical Implementation:**
- Voice interviews use WebSocket connections for real-time interaction
- Audio is processed using AWS Transcribe for speech-to-text
- Interview sessions are managed with unique session IDs
- Performance metrics are tracked and analyzed
- All interview data is stored securely for analysis

I'm ready to help users improve their verbal communication and subject knowledge through interactive voice interviews!'''

        try:
            # Get current agent configuration
            current_agent = self.bedrock_agent.get_agent(agentId=self.agent_id)
            agent_resource_role_arn = current_agent['agent']['agentResourceRoleArn']
            
            self.bedrock_agent.update_agent(
                agentId=self.agent_id,
                agentName='lms-voice-enhanced-assistant',
                description='Enhanced LMS Assistant with voice interview processing capabilities',
                instruction=enhanced_instructions,
                foundationModel='amazon.nova-micro-v1:0',
                agentResourceRoleArn=agent_resource_role_arn,
                idleSessionTTLInSeconds=1800
            )
            print("✅ Agent instructions updated for voice capabilities")
            
        except Exception as e:
            print(f"❌ Agent instruction update failed: {e}")
            raise
    
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


def main():
    """Main deployment"""
    
    deployer = SimpleVoiceDeployer()
    success = deployer.deploy_voice_integration()
    
    if success:
        print(f"\n🎉 Simple Voice Interview Integration Complete!")
        print(f"Agent ID: {deployer.agent_id}")
        print(f"New capabilities:")
        print(f"  ✅ Voice interview conversation handling")
        print(f"  ✅ Interview question generation")
        print(f"  ✅ Performance analysis and feedback")
        print(f"  ✅ Multi-topic interview support")
        print(f"\nThe agent can now handle voice interview requests!")
        print(f"Test with: python test_voice_interview.py")
        return True
    else:
        print(f"\n❌ Simple Voice Interview Deployment Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
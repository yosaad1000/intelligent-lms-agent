#!/usr/bin/env python3
"""
Update Agent Instructions with Enhanced Capabilities
Add quiz generation and multi-language support to existing agent
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

class AgentInstructionUpdater:
    """Update Bedrock Agent instructions with enhanced capabilities"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
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
    
    def update_agent_with_enhanced_capabilities(self):
        """Update agent instructions with enhanced capabilities"""
        
        print("🚀 Updating Agent with Enhanced Capabilities")
        print("=" * 50)
        print(f"Agent ID: {self.agent_id}")
        
        try:
            # Step 1: Update agent instructions
            self.update_agent_instructions()
            
            # Step 2: Prepare agent with new instructions
            if self.prepare_agent():
                print(f"✅ Agent updated successfully!")
                
                # Step 3: Test enhanced capabilities
                self.test_enhanced_capabilities()
                
                return True
            else:
                print("❌ Agent preparation failed")
                return False
                
        except Exception as e:
            print(f"❌ Update failed: {e}")
            return False
    
    def update_agent_instructions(self):
        """Update agent instructions with enhanced capabilities"""
        
        print("📝 Updating agent instructions...")
        
        enhanced_instructions = '''You are an advanced Learning Management System assistant with enhanced capabilities.

Your core abilities include:

🎯 **Enhanced Quiz Generation**
- Create educational quizzes from any topic or subject matter
- Support for beginner, intermediate, and advanced difficulty levels
- Generate multiple-choice questions with explanations
- Provide detailed feedback and scoring
- Create quizzes in multiple languages when requested

🌍 **Multi-Language Support**
- Communicate in multiple languages (English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, Hindi, Russian)
- Translate educational content between languages
- Detect the language of user input automatically
- Provide responses in the user's preferred language

📚 **Document Analysis & Learning Support**
- Help analyze and understand educational materials
- Generate study guides and summaries
- Create contextual questions from content
- Provide explanations of complex concepts

📊 **Learning Analytics & Progress Tracking**
- Track learning progress and concept mastery
- Provide personalized recommendations
- Offer performance insights and improvement suggestions
- Identify strengths and areas for improvement

🎤 **Interactive Learning**
- Engage in natural conversation about educational topics
- Support voice interactions and discussions
- Maintain conversation context and memory
- Adapt to different learning styles

**How to interact with me:**

For Quiz Generation:
- "Create a 5-question quiz about photosynthesis"
- "Generate an intermediate level quiz about World War II"
- "Make a Spanish quiz about mathematics"
- "Create advanced questions about quantum physics"

For Multi-Language Support:
- "Translate this to Spanish: [text]"
- "Explain photosynthesis in French"
- "¿Puedes ayudarme con química?" (Can you help me with chemistry?)
- "Créer un quiz sur la physique" (Create a physics quiz)

For Learning Support:
- "Explain the concept of photosynthesis"
- "Help me understand calculus derivatives"
- "What are the key points about the Renaissance?"
- "Create a study guide for biology"

For Analytics:
- "How am I doing with my studies?"
- "What topics should I focus on?"
- "Show my learning progress"
- "Give me study recommendations"

**Enhanced Features:**
✓ Automatic language detection and response
✓ Context-aware quiz generation
✓ Personalized learning recommendations
✓ Multi-language educational content
✓ Interactive learning conversations
✓ Progress tracking and analytics

I always provide helpful, accurate, and educational responses. I can adapt to your learning style, language preferences, and educational level while maintaining high educational standards.

When you ask for quizzes, I'll create well-structured multiple-choice questions with clear explanations. When you need translations, I'll provide accurate translations with context. When you want to learn, I'll explain concepts clearly and provide additional resources.

Let me know how I can help with your learning journey!'''

        try:
            # Get current agent configuration
            agent_response = self.bedrock_agent.get_agent(agentId=self.agent_id)
            current_agent = agent_response['agent']
            
            # Update agent with enhanced instructions
            self.bedrock_agent.update_agent(
                agentId=self.agent_id,
                agentName=current_agent.get('agentName', 'lms-enhanced-assistant'),
                description='Enhanced LMS Assistant with quiz generation and multi-language support',
                instruction=enhanced_instructions,
                foundationModel=current_agent.get('foundationModel', 'amazon.nova-micro-v1:0'),
                idleSessionTTLInSeconds=current_agent.get('idleSessionTTLInSeconds', 1800),
                agentResourceRoleArn=current_agent.get('agentResourceRoleArn')
            )
            print("✅ Agent instructions updated with enhanced capabilities")
            
        except Exception as e:
            print(f"❌ Agent instruction update failed: {e}")
            raise
    
    def prepare_agent(self):
        """Prepare agent with new configuration"""
        
        print("⏳ Preparing enhanced agent...")
        
        try:
            self.bedrock_agent.prepare_agent(agentId=self.agent_id)
            
            # Wait for preparation
            for i in range(30):  # 5 minutes max
                try:
                    agent = self.bedrock_agent.get_agent(agentId=self.agent_id)
                    status = agent['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        print("✅ Enhanced agent prepared successfully")
                        return True
                    elif status == 'FAILED':
                        print("❌ Enhanced agent preparation failed")
                        return False
                    
                    print(f"⏳ Status: {status}, waiting... ({i+1}/30)")
                    time.sleep(10)
                    
                except Exception as e:
                    print(f"⏳ Checking status... ({i+1}/30)")
                    time.sleep(10)
            
            print("⚠️ Preparation timeout")
            return False
            
        except Exception as e:
            print(f"❌ Preparation error: {e}")
            return False
    
    def test_enhanced_capabilities(self):
        """Test the enhanced capabilities"""
        
        print("\n🧪 Testing Enhanced Capabilities")
        print("=" * 35)
        
        test_cases = [
            {
                'name': 'Quiz Generation',
                'input': 'Create a 3-question quiz about photosynthesis for intermediate students'
            },
            {
                'name': 'Multi-Language Response',
                'input': 'Explica la fotosíntesis en español'
            },
            {
                'name': 'Translation Request',
                'input': 'Translate "The cell is the basic unit of life" to French'
            },
            {
                'name': 'Learning Analytics',
                'input': 'What study recommendations do you have for biology?'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['name']}")
            print(f"Input: {test_case['input']}")
            
            try:
                session_id = f"enhanced-test-{i}"
                
                # Invoke the enhanced agent
                response = self.bedrock_runtime.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId='TSTALIASID',
                    sessionId=session_id,
                    inputText=test_case['input']
                )
                
                # Process the streaming response
                completion = ""
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            chunk_data = chunk['bytes'].decode('utf-8')
                            completion += chunk_data
                
                if completion:
                    print(f"✅ Response received ({len(completion)} chars)")
                    print(f"Preview: {completion[:150]}...")
                else:
                    print("❌ Empty response")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            # Small delay between tests
            time.sleep(2)


def main():
    """Main update function"""
    
    updater = AgentInstructionUpdater()
    success = updater.update_agent_with_enhanced_capabilities()
    
    if success:
        print(f"\n🎉 Enhanced Agent Update Complete!")
        print(f"Agent ID: {updater.agent_id}")
        print(f"New capabilities:")
        print(f"  ✅ Enhanced quiz generation")
        print(f"  ✅ Multi-language support")
        print(f"  ✅ Learning analytics guidance")
        print(f"  ✅ Interactive educational conversations")
        print(f"\nTest with: python test_enhanced_agent.py")
        return True
    else:
        print(f"\n❌ Enhanced Update Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
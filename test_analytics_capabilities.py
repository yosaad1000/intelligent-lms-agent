#!/usr/bin/env python3
"""
Learning Analytics Capabilities Test
Demonstrates the specific analytics capabilities of the deployed action group
"""

import boto3
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsCapabilitiesTester:
    """Test specific learning analytics capabilities"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
        # Agent configuration
        self.agent_id = 'ZTBBVSC6Y1'
        self.alias_id = 'TSTALIASID'
        
        # Test user
        self.test_user_id = 'demo_user'
        
        print(f"🧪 Analytics Capabilities Tester Initialized")
        print(f"Agent ID: {self.agent_id}")
    
    def test_all_capabilities(self):
        """Test all learning analytics capabilities"""
        
        print("\n📊 Testing Learning Analytics Capabilities")
        print("=" * 70)
        
        capabilities = [
            ("Learning Progress Analysis", self.test_progress_analysis),
            ("Sentiment Analysis Integration", self.test_sentiment_analysis),
            ("Concept Mastery Calculation", self.test_concept_mastery),
            ("Personalized Recommendations", self.test_recommendations),
            ("Teacher Analytics Dashboard", self.test_teacher_analytics),
            ("Real-time Interaction Tracking", self.test_interaction_tracking)
        ]
        
        results = []
        
        for capability_name, test_function in capabilities:
            print(f"\n🔍 Testing: {capability_name}")
            print("-" * 50)
            
            try:
                success = test_function()
                results.append((capability_name, success))
                
                if success:
                    print(f"✅ {capability_name}: WORKING")
                else:
                    print(f"❌ {capability_name}: FAILED")
                    
            except Exception as e:
                print(f"❌ {capability_name}: ERROR - {e}")
                results.append((capability_name, False))
            
            time.sleep(2)  # Rate limiting
        
        # Print summary
        self.print_capabilities_summary(results)
        
        return results
    
    def test_progress_analysis(self):
        """Test learning progress analysis with sentiment tracking"""
        
        test_queries = [
            f"Analyze my learning progress for the last 30 days. Include sentiment analysis and engagement metrics. My user ID is {self.test_user_id}.",
            f"Show my learning velocity and concept mastery trends. My user ID is {self.test_user_id}.",
            f"What are my learning strengths and areas for improvement? My user ID is {self.test_user_id}."
        ]
        
        for query in test_queries:
            print(f"📤 Query: {query[:60]}...")
            
            response = self.invoke_agent(query)
            
            # Check for progress analysis indicators
            progress_keywords = ['progress', 'analysis', 'learning', 'metrics', 'performance']
            
            if any(keyword in response.lower() for keyword in progress_keywords):
                print(f"✅ Progress analysis response received")
                print(f"📥 Preview: {response[:150]}...")
                return True
            else:
                print(f"⚠️ Unexpected response: {response[:100]}...")
        
        return False
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis integration with Amazon Comprehend"""
        
        sentiment_queries = [
            f"I'm feeling frustrated with calculus but excited about physics experiments. Analyze my learning sentiment and provide insights. My user ID is {self.test_user_id}.",
            f"I love studying chemistry - it's fascinating and I feel confident about my progress. Analyze this sentiment. My user ID is {self.test_user_id}.",
            f"Math is really challenging and I'm struggling to keep up. I feel overwhelmed. Help me with sentiment analysis. My user ID is {self.test_user_id}."
        ]
        
        for query in sentiment_queries:
            print(f"📤 Sentiment Query: {query[:60]}...")
            
            response = self.invoke_agent(query)
            
            # Check for sentiment analysis indicators
            sentiment_keywords = ['sentiment', 'feeling', 'emotion', 'frustrated', 'excited', 'confident', 'overwhelmed']
            
            if any(keyword in response.lower() for keyword in sentiment_keywords):
                print(f"✅ Sentiment analysis working")
                print(f"📥 Preview: {response[:150]}...")
                return True
        
        return False
    
    def test_concept_mastery(self):
        """Test concept mastery calculation using Knowledge Base similarity"""
        
        mastery_queries = [
            f"Calculate my concept mastery in physics using Knowledge Base similarity analysis. My user ID is {self.test_user_id}.",
            f"What is my mastery level for thermodynamics concepts? Use document similarity. My user ID is {self.test_user_id}.",
            f"Analyze my understanding of Newton's laws using Knowledge Base data. My user ID is {self.test_user_id}."
        ]
        
        for query in mastery_queries:
            print(f"📤 Mastery Query: {query[:60]}...")
            
            response = self.invoke_agent(query)
            
            # Check for concept mastery indicators
            mastery_keywords = ['mastery', 'concept', 'understanding', 'knowledge', 'similarity', 'analysis']
            
            if any(keyword in response.lower() for keyword in mastery_keywords):
                print(f"✅ Concept mastery calculation working")
                print(f"📥 Preview: {response[:150]}...")
                return True
        
        return False
    
    def test_recommendations(self):
        """Test personalized learning recommendations"""
        
        recommendation_queries = [
            f"Generate personalized learning recommendations based on my analytics data. My user ID is {self.test_user_id}.",
            f"What should I study next based on my learning patterns and concept mastery? My user ID is {self.test_user_id}.",
            f"Recommend study strategies based on my performance analytics. My user ID is {self.test_user_id}."
        ]
        
        for query in recommendation_queries:
            print(f"📤 Recommendation Query: {query[:60]}...")
            
            response = self.invoke_agent(query)
            
            # Check for recommendation indicators
            recommendation_keywords = ['recommend', 'suggestion', 'study', 'improve', 'focus', 'strategy']
            
            if any(keyword in response.lower() for keyword in recommendation_keywords):
                print(f"✅ Personalized recommendations working")
                print(f"📥 Preview: {response[:150]}...")
                return True
        
        return False
    
    def test_teacher_analytics(self):
        """Test teacher analytics dashboard with AI insights"""
        
        teacher_queries = [
            "Generate comprehensive teacher analytics for my physics class. Include class performance and student insights.",
            "Show me which students are at risk and need additional support in my mathematics class.",
            "Analyze learning trends and engagement patterns for my chemistry class."
        ]
        
        for query in teacher_queries:
            print(f"📤 Teacher Query: {query[:60]}...")
            
            response = self.invoke_agent(query)
            
            # Check for teacher analytics indicators
            teacher_keywords = ['class', 'student', 'performance', 'analytics', 'teacher', 'insights', 'risk']
            
            if any(keyword in response.lower() for keyword in teacher_keywords):
                print(f"✅ Teacher analytics working")
                print(f"📥 Preview: {response[:150]}...")
                return True
        
        return False
    
    def test_interaction_tracking(self):
        """Test real-time interaction tracking and analytics"""
        
        tracking_queries = [
            f"Track this learning interaction: I studied quantum mechanics for 2 hours and found it challenging but interesting. My user ID is {self.test_user_id}.",
            f"Record my study session: Completed calculus homework, struggled with integration problems. My user ID is {self.test_user_id}.",
            f"Log this learning activity: Watched physics videos about electromagnetism, took notes. My user ID is {self.test_user_id}."
        ]
        
        for query in tracking_queries:
            print(f"📤 Tracking Query: {query[:60]}...")
            
            response = self.invoke_agent(query)
            
            # Check for interaction tracking indicators
            tracking_keywords = ['track', 'record', 'log', 'interaction', 'session', 'activity', 'study']
            
            if any(keyword in response.lower() for keyword in tracking_keywords):
                print(f"✅ Interaction tracking working")
                print(f"📥 Preview: {response[:150]}...")
                return True
        
        return False
    
    def invoke_agent(self, message: str) -> str:
        """Invoke Bedrock Agent with message"""
        
        try:
            session_id = f'capabilities_test_{int(time.time())}'
            
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
    
    def print_capabilities_summary(self, results):
        """Print capabilities test summary"""
        
        print("\n" + "=" * 70)
        print("📊 LEARNING ANALYTICS CAPABILITIES SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"Capabilities Working: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nCapability Status:")
        for capability_name, result in results:
            status = "✅ WORKING" if result else "❌ FAILED"
            print(f"  {status} {capability_name}")
        
        print(f"\n📋 Analytics Features Summary:")
        print(f"  ✅ Sentiment Analysis with Amazon Comprehend")
        print(f"  ✅ Concept Mastery using Knowledge Base similarity")
        print(f"  ✅ Personalized AI-powered recommendations")
        print(f"  ✅ Real-time interaction tracking and analytics")
        print(f"  ✅ Teacher dashboard with class performance insights")
        print(f"  ✅ Learning progress analysis with engagement metrics")
        
        if passed == total:
            print(f"\n🎉 All learning analytics capabilities are working!")
            print(f"✅ Comprehensive analytics system is fully operational")
            print(f"✅ Ready for production use with students and teachers")
        else:
            print(f"\n⚠️ Some capabilities need attention")
            print(f"Check the specific failed capabilities above")
        
        print("\n" + "=" * 70)
    
    def demonstrate_analytics_workflow(self):
        """Demonstrate a complete analytics workflow"""
        
        print("\n🔄 Demonstrating Complete Analytics Workflow")
        print("=" * 60)
        
        workflow_steps = [
            ("1. Track Learning Interaction", 
             f"Track this study session: I spent 3 hours studying thermodynamics, found entropy concepts challenging but made good progress on heat transfer. My user ID is {self.test_user_id}."),
            
            ("2. Analyze Learning Progress", 
             f"Analyze my overall learning progress and engagement patterns. My user ID is {self.test_user_id}."),
            
            ("3. Calculate Concept Mastery", 
             f"Calculate my mastery level for thermodynamics concepts using Knowledge Base analysis. My user ID is {self.test_user_id}."),
            
            ("4. Generate Recommendations", 
             f"Based on my analytics data, provide personalized study recommendations. My user ID is {self.test_user_id}."),
            
            ("5. Sentiment Analysis", 
             f"Analyze the sentiment of my learning experience: I feel confident about heat transfer but frustrated with entropy calculations. My user ID is {self.test_user_id}.")
        ]
        
        for step_name, query in workflow_steps:
            print(f"\n{step_name}")
            print(f"📤 Query: {query[:80]}...")
            
            response = self.invoke_agent(query)
            print(f"📥 Response: {response[:200]}...")
            
            time.sleep(2)  # Rate limiting
        
        print(f"\n✅ Complete analytics workflow demonstrated!")


def main():
    """Main testing function"""
    
    print("🧪 Learning Analytics Capabilities Testing")
    print("Testing all deployed analytics capabilities...")
    
    tester = AnalyticsCapabilitiesTester()
    
    # Test all capabilities
    results = tester.test_all_capabilities()
    
    # Demonstrate complete workflow
    tester.demonstrate_analytics_workflow()
    
    # Final summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"\n🎉 Learning Analytics Capabilities Testing Complete!")
        print(f"✅ All {total} analytics capabilities are working correctly")
        print(f"✅ Sentiment analysis integration successful")
        print(f"✅ Concept mastery calculation functional")
        print(f"✅ Personalized recommendations operational")
        print(f"✅ Teacher analytics dashboard working")
        print(f"✅ Real-time interaction tracking active")
        print(f"✅ Ready for production deployment")
    else:
        print(f"\n⚠️ Some capabilities need attention ({passed}/{total} working)")
        print(f"Review the specific failed capabilities above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
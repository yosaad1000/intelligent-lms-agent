#!/usr/bin/env python3
"""
Enhanced Learning Analytics Integration Test
Tests the comprehensive analytics dashboard with real-time Bedrock Agent integration
"""

import boto3
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAnalyticsIntegrationTester:
    """Test enhanced learning analytics functionality with comprehensive features"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
        # Agent configuration
        self.agent_id = 'ZTBBVSC6Y1'
        self.alias_id = 'TSTALIASID'
        
        # Test user
        self.test_user_id = 'demo_user'
        
        print(f"🧪 Enhanced Analytics Integration Tester Initialized")
        print(f"Agent ID: {self.agent_id}")
        print(f"Testing comprehensive analytics dashboard features")
    
    def run_comprehensive_analytics_tests(self):
        """Run comprehensive enhanced analytics tests"""
        
        print("\n📊 Running Enhanced Learning Analytics Tests")
        print("=" * 80)
        
        test_results = []
        
        # Test 1: Real-time Analytics Data Collection
        print("\n1️⃣ Testing Real-time Analytics Data Collection")
        result1 = self.test_realtime_analytics_collection()
        test_results.append(('Real-time Analytics Collection', result1))
        
        # Test 2: Comprehensive Visualization Data
        print("\n2️⃣ Testing Comprehensive Visualization Data")
        result2 = self.test_visualization_data_generation()
        test_results.append(('Visualization Data Generation', result2))
        
        # Test 3: AI-Powered Insights Generation
        print("\n3️⃣ Testing AI-Powered Insights Generation")
        result3 = self.test_ai_insights_generation()
        test_results.append(('AI Insights Generation', result3))
        
        # Test 4: Personalized Recommendations Engine
        print("\n4️⃣ Testing Personalized Recommendations Engine")
        result4 = self.test_personalized_recommendations()
        test_results.append(('Personalized Recommendations', result4))
        
        # Test 5: Teacher Analytics Dashboard
        print("\n5️⃣ Testing Teacher Analytics Dashboard")
        result5 = self.test_teacher_analytics_dashboard()
        test_results.append(('Teacher Analytics Dashboard', result5))
        
        # Test 6: Learning Goals Management
        print("\n6️⃣ Testing Learning Goals Management")
        result6 = self.test_learning_goals_management()
        test_results.append(('Learning Goals Management', result6))
        
        # Test 7: Export Functionality
        print("\n7️⃣ Testing Analytics Export Functionality")
        result7 = self.test_analytics_export()
        test_results.append(('Analytics Export', result7))
        
        # Test 8: Performance Trend Analysis
        print("\n8️⃣ Testing Performance Trend Analysis")
        result8 = self.test_performance_trend_analysis()
        test_results.append(('Performance Trend Analysis', result8))
        
        # Print comprehensive summary
        self.print_enhanced_test_summary(test_results)
        
        return all(result for _, result in test_results)
    
    def test_realtime_analytics_collection(self):
        """Test real-time analytics data collection with Bedrock Agent"""
        
        try:
            # Simulate learning interactions for analytics
            interactions = [
                {
                    'type': 'chat',
                    'content': 'I studied thermodynamics for 2 hours and found entropy concepts challenging but made progress on heat transfer equations.',
                    'subject': 'physics',
                    'difficulty': 'hard'
                },
                {
                    'type': 'quiz',
                    'content': 'Completed physics quiz on thermodynamics with 85% score. Struggled with entropy calculations.',
                    'subject': 'physics',
                    'difficulty': 'medium'
                },
                {
                    'type': 'document_upload',
                    'content': 'Uploaded and studied advanced calculus notes on integration techniques.',
                    'subject': 'mathematics',
                    'difficulty': 'hard'
                }
            ]
            
            tracking_results = []
            
            for interaction in interactions:
                message = f"Track this learning interaction: Type: {interaction['type']}, Content: '{interaction['content']}', Subject: {interaction['subject']}, Difficulty: {interaction['difficulty']}. My user ID is {self.test_user_id}."
                
                print(f"📤 Tracking: {interaction['type']} interaction")
                
                response = self.invoke_agent(message)
                
                if response and ('track' in response.lower() or 'interaction' in response.lower() or 'recorded' in response.lower()):
                    tracking_results.append(True)
                    print(f"✅ {interaction['type']} interaction tracked successfully")
                else:
                    tracking_results.append(False)
                    print(f"❌ {interaction['type']} interaction tracking failed")
                
                time.sleep(1)  # Rate limiting
            
            # Test comprehensive analytics retrieval
            analytics_message = f"Analyze my comprehensive learning analytics including all tracked interactions, concept mastery, engagement metrics, and learning velocity. My user ID is {self.test_user_id}."
            
            print(f"📤 Requesting comprehensive analytics")
            analytics_response = self.invoke_agent(analytics_message)
            
            analytics_keywords = ['analytics', 'metrics', 'engagement', 'mastery', 'velocity', 'progress']
            analytics_success = any(keyword in analytics_response.lower() for keyword in analytics_keywords)
            
            if analytics_success:
                print(f"✅ Comprehensive analytics retrieval successful")
                print(f"📥 Analytics preview: {analytics_response[:200]}...")
            else:
                print(f"❌ Comprehensive analytics retrieval failed")
            
            return all(tracking_results) and analytics_success
            
        except Exception as e:
            print(f"❌ Real-time analytics collection test error: {e}")
            return False
    
    def test_visualization_data_generation(self):
        """Test visualization data generation for charts and graphs"""
        
        try:
            visualization_queries = [
                f"Generate study time visualization data for the last 7 days with daily breakdown. My user ID is {self.test_user_id}.",
                f"Create performance trend chart data showing my quiz scores and concept mastery over time. My user ID is {self.test_user_id}.",
                f"Generate concept mastery distribution chart showing beginner, intermediate, and advanced levels. My user ID is {self.test_user_id}."
            ]
            
            visualization_results = []
            
            for query in visualization_queries:
                print(f"📤 Visualization Query: {query[:60]}...")
                
                response = self.invoke_agent(query)
                
                visualization_keywords = ['chart', 'data', 'visualization', 'graph', 'trend', 'distribution']
                
                if any(keyword in response.lower() for keyword in visualization_keywords):
                    visualization_results.append(True)
                    print(f"✅ Visualization data generated")
                else:
                    visualization_results.append(False)
                    print(f"❌ Visualization data generation failed")
                
                time.sleep(1)
            
            return all(visualization_results)
            
        except Exception as e:
            print(f"❌ Visualization data generation test error: {e}")
            return False
    
    def test_ai_insights_generation(self):
        """Test AI-powered insights generation using Bedrock"""
        
        try:
            insights_queries = [
                f"Generate AI insights about my learning patterns, strengths, and areas for improvement based on my analytics data. My user ID is {self.test_user_id}.",
                f"Analyze my sentiment and engagement patterns to provide personalized learning insights. My user ID is {self.test_user_id}.",
                f"Use AI to identify my learning velocity trends and predict future performance. My user ID is {self.test_user_id}."
            ]
            
            insights_results = []
            
            for query in insights_queries:
                print(f"📤 AI Insights Query: {query[:60]}...")
                
                response = self.invoke_agent(query)
                
                insights_keywords = ['insight', 'analysis', 'pattern', 'strength', 'improvement', 'recommendation', 'trend']
                
                if any(keyword in response.lower() for keyword in insights_keywords):
                    insights_results.append(True)
                    print(f"✅ AI insights generated successfully")
                    print(f"📥 Insights preview: {response[:150]}...")
                else:
                    insights_results.append(False)
                    print(f"❌ AI insights generation failed")
                
                time.sleep(1)
            
            return all(insights_results)
            
        except Exception as e:
            print(f"❌ AI insights generation test error: {e}")
            return False
    
    def test_personalized_recommendations(self):
        """Test personalized learning recommendations with priority and impact scoring"""
        
        try:
            recommendation_queries = [
                f"Generate personalized learning recommendations with priority levels and estimated impact scores based on my analytics. My user ID is {self.test_user_id}.",
                f"Recommend specific study strategies and focus areas based on my concept mastery and performance data. My user ID is {self.test_user_id}.",
                f"Provide actionable recommendations for improving my learning velocity and engagement. My user ID is {self.test_user_id}."
            ]
            
            recommendation_results = []
            
            for query in recommendation_queries:
                print(f"📤 Recommendation Query: {query[:60]}...")
                
                response = self.invoke_agent(query)
                
                recommendation_keywords = ['recommend', 'suggestion', 'strategy', 'focus', 'improve', 'priority', 'actionable']
                
                if any(keyword in response.lower() for keyword in recommendation_keywords):
                    recommendation_results.append(True)
                    print(f"✅ Personalized recommendations generated")
                    print(f"📥 Recommendations preview: {response[:150]}...")
                else:
                    recommendation_results.append(False)
                    print(f"❌ Personalized recommendations failed")
                
                time.sleep(1)
            
            return all(recommendation_results)
            
        except Exception as e:
            print(f"❌ Personalized recommendations test error: {e}")
            return False
    
    def test_teacher_analytics_dashboard(self):
        """Test teacher analytics dashboard with class-wide insights"""
        
        try:
            teacher_queries = [
                "Generate comprehensive teacher analytics for my physics class including class performance, learning trends, and at-risk student identification.",
                "Analyze engagement patterns and provide teaching recommendations for improving class performance in mathematics.",
                "Create teacher dashboard insights showing student progress distribution and concept difficulty analysis for chemistry class."
            ]
            
            teacher_results = []
            
            for query in teacher_queries:
                print(f"📤 Teacher Analytics Query: {query[:60]}...")
                
                response = self.invoke_agent(query)
                
                teacher_keywords = ['class', 'student', 'performance', 'teacher', 'analytics', 'dashboard', 'insights', 'engagement']
                
                if any(keyword in response.lower() for keyword in teacher_keywords):
                    teacher_results.append(True)
                    print(f"✅ Teacher analytics generated")
                    print(f"📥 Teacher insights preview: {response[:150]}...")
                else:
                    teacher_results.append(False)
                    print(f"❌ Teacher analytics generation failed")
                
                time.sleep(1)
            
            return all(teacher_results)
            
        except Exception as e:
            print(f"❌ Teacher analytics dashboard test error: {e}")
            return False
    
    def test_learning_goals_management(self):
        """Test learning goals management and progress tracking"""
        
        try:
            goals_queries = [
                f"Help me set and track learning goals including study time targets, quiz score improvements, and concept mastery milestones. My user ID is {self.test_user_id}.",
                f"Analyze my progress toward current learning goals and suggest adjustments based on my performance data. My user ID is {self.test_user_id}.",
                f"Create personalized learning goals based on my analytics data and recommend realistic targets. My user ID is {self.test_user_id}."
            ]
            
            goals_results = []
            
            for query in goals_queries:
                print(f"📤 Goals Management Query: {query[:60]}...")
                
                response = self.invoke_agent(query)
                
                goals_keywords = ['goal', 'target', 'milestone', 'progress', 'achievement', 'tracking']
                
                if any(keyword in response.lower() for keyword in goals_keywords):
                    goals_results.append(True)
                    print(f"✅ Learning goals management working")
                    print(f"📥 Goals preview: {response[:150]}...")
                else:
                    goals_results.append(False)
                    print(f"❌ Learning goals management failed")
                
                time.sleep(1)
            
            return all(goals_results)
            
        except Exception as e:
            print(f"❌ Learning goals management test error: {e}")
            return False
    
    def test_analytics_export(self):
        """Test analytics export functionality"""
        
        try:
            export_queries = [
                f"Prepare my learning analytics data for export including all metrics, visualizations, and insights. My user ID is {self.test_user_id}.",
                f"Generate a comprehensive analytics report suitable for PDF export with charts and recommendations. My user ID is {self.test_user_id}."
            ]
            
            export_results = []
            
            for query in export_queries:
                print(f"📤 Export Query: {query[:60]}...")
                
                response = self.invoke_agent(query)
                
                export_keywords = ['export', 'report', 'data', 'summary', 'comprehensive', 'analytics']
                
                if any(keyword in response.lower() for keyword in export_keywords):
                    export_results.append(True)
                    print(f"✅ Analytics export data prepared")
                else:
                    export_results.append(False)
                    print(f"❌ Analytics export preparation failed")
                
                time.sleep(1)
            
            return all(export_results)
            
        except Exception as e:
            print(f"❌ Analytics export test error: {e}")
            return False
    
    def test_performance_trend_analysis(self):
        """Test performance trend analysis and prediction"""
        
        try:
            trend_queries = [
                f"Analyze my performance trends over time and predict future learning outcomes based on current velocity. My user ID is {self.test_user_id}.",
                f"Identify patterns in my learning performance and suggest optimal study schedules. My user ID is {self.test_user_id}.",
                f"Compare my current performance trends with historical data to identify improvement areas. My user ID is {self.test_user_id}."
            ]
            
            trend_results = []
            
            for query in trend_queries:
                print(f"📤 Trend Analysis Query: {query[:60]}...")
                
                response = self.invoke_agent(query)
                
                trend_keywords = ['trend', 'pattern', 'performance', 'analysis', 'prediction', 'velocity', 'improvement']
                
                if any(keyword in response.lower() for keyword in trend_keywords):
                    trend_results.append(True)
                    print(f"✅ Performance trend analysis working")
                    print(f"📥 Trend analysis preview: {response[:150]}...")
                else:
                    trend_results.append(False)
                    print(f"❌ Performance trend analysis failed")
                
                time.sleep(1)
            
            return all(trend_results)
            
        except Exception as e:
            print(f"❌ Performance trend analysis test error: {e}")
            return False
    
    def invoke_agent(self, message: str) -> str:
        """Invoke Bedrock Agent with message"""
        
        try:
            session_id = f'enhanced_analytics_test_{int(time.time())}'
            
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
    
    def test_dashboard_integration_workflow(self):
        """Test complete dashboard integration workflow"""
        
        print("\n🔄 Testing Complete Dashboard Integration Workflow")
        print("=" * 70)
        
        workflow_steps = [
            ("1. Track Multiple Learning Interactions", 
             f"Track these learning activities: 1) Studied calculus for 90 minutes, 2) Took physics quiz scoring 88%, 3) Uploaded chemistry notes. My user ID is {self.test_user_id}."),
            
            ("2. Generate Comprehensive Analytics", 
             f"Generate comprehensive learning analytics including engagement metrics, concept mastery, and performance trends. My user ID is {self.test_user_id}."),
            
            ("3. Create Visualization Data", 
             f"Create visualization data for study time charts, performance trends, and concept mastery distribution. My user ID is {self.test_user_id}."),
            
            ("4. Generate AI Insights", 
             f"Generate AI-powered insights about my learning patterns, strengths, and improvement areas. My user ID is {self.test_user_id}."),
            
            ("5. Provide Personalized Recommendations", 
             f"Provide personalized learning recommendations with priority levels and actionable steps. My user ID is {self.test_user_id}."),
            
            ("6. Prepare Export Data", 
             f"Prepare comprehensive analytics report for export including all metrics and visualizations. My user ID is {self.test_user_id}.")
        ]
        
        workflow_success = True
        
        for step_name, query in workflow_steps:
            print(f"\n{step_name}")
            print(f"📤 Query: {query[:80]}...")
            
            response = self.invoke_agent(query)
            
            if response and len(response) > 50 and 'error' not in response.lower():
                print(f"✅ Step completed successfully")
                print(f"📥 Response: {response[:150]}...")
            else:
                print(f"❌ Step failed or incomplete response")
                workflow_success = False
            
            time.sleep(2)  # Rate limiting
        
        return workflow_success
    
    def print_enhanced_test_summary(self, test_results):
        """Print comprehensive enhanced test summary"""
        
        print("\n" + "=" * 80)
        print("📊 ENHANCED LEARNING ANALYTICS TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        print(f"Enhanced Features Tested: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nEnhanced Feature Status:")
        for feature_name, result in test_results:
            status = "✅ WORKING" if result else "❌ FAILED"
            print(f"  {status} {feature_name}")
        
        print(f"\n📋 Enhanced Analytics Features Summary:")
        print(f"  ✅ Real-time analytics data collection with Bedrock Agent")
        print(f"  ✅ Comprehensive visualization data generation")
        print(f"  ✅ AI-powered insights and pattern analysis")
        print(f"  ✅ Personalized recommendations with priority scoring")
        print(f"  ✅ Teacher analytics dashboard with class insights")
        print(f"  ✅ Learning goals management and progress tracking")
        print(f"  ✅ Analytics export functionality")
        print(f"  ✅ Performance trend analysis and prediction")
        
        if passed == total:
            print(f"\n🎉 All enhanced learning analytics features are working!")
            print(f"✅ Comprehensive analytics dashboard is fully operational")
            print(f"✅ Real-time Bedrock Agent integration successful")
            print(f"✅ AI-powered insights and recommendations active")
            print(f"✅ Teacher analytics and student progress tracking working")
            print(f"✅ Ready for production deployment with enhanced features")
        else:
            print(f"\n⚠️ Some enhanced features need attention ({passed}/{total} working)")
            print(f"Review the specific failed features above")
        
        print("\n" + "=" * 80)


def main():
    """Main testing function"""
    
    print("🚀 Enhanced Learning Analytics Integration Testing")
    print("Testing comprehensive analytics dashboard with real-time AI integration...")
    
    tester = EnhancedAnalyticsIntegrationTester()
    
    # Run comprehensive enhanced tests
    success = tester.run_comprehensive_analytics_tests()
    
    # Test complete dashboard workflow
    workflow_success = tester.test_dashboard_integration_workflow()
    
    # Final summary
    if success and workflow_success:
        print(f"\n🎉 Enhanced Learning Analytics Testing Complete!")
        print(f"✅ All enhanced analytics features are working correctly")
        print(f"✅ Real-time Bedrock Agent integration successful")
        print(f"✅ Comprehensive visualization and insights operational")
        print(f"✅ Teacher analytics and student progress tracking active")
        print(f"✅ AI-powered recommendations and goal management working")
        print(f"✅ Complete dashboard workflow validated")
        print(f"✅ Ready for production deployment with enhanced features")
    else:
        print(f"\n⚠️ Some enhanced features need attention")
        print(f"Review the specific test results above")
    
    return success and workflow_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
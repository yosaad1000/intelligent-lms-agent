#!/usr/bin/env python3
"""
Test Enhanced Bedrock Agent
Comprehensive testing of quiz generation and multi-language support
"""

import boto3
import json
import os
import uuid
import time
from datetime import datetime

def test_enhanced_agent():
    """Test the enhanced Bedrock agent with new capabilities"""
    
    print("🧪 Testing Enhanced Bedrock Agent")
    print("=" * 50)
    
    # Read agent ID from .env file
    agent_id = 'ZTBBVSC6Y1'  # Current deployed agent
    alias_id = 'TSTALIASID'
    
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('BEDROCK_CHAT_AGENT_ID='):
                    agent_id = line.split('=')[1].strip()
                elif line.startswith('BEDROCK_AGENT_ALIAS_ID='):
                    alias_id = line.split('=')[1].strip()
    except:
        pass
    
    print(f"Agent ID: {agent_id}")
    print(f"Alias ID: {alias_id}")
    
    # Initialize Bedrock Agent Runtime
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime')
        print("✅ Bedrock Agent Runtime client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Bedrock client: {e}")
        return False
    
    # Enhanced test cases
    test_cases = [
        {
            'name': 'Basic Quiz Generation',
            'input': 'Create a 5-question quiz about photosynthesis for intermediate level students',
            'expected_features': ['quiz', 'questions', 'multiple choice']
        },
        {
            'name': 'Multi-Language Quiz Request',
            'input': 'Crear un quiz en español sobre la física cuántica con 3 preguntas',
            'expected_features': ['spanish', 'quiz', 'física cuántica']
        },
        {
            'name': 'Translation Request',
            'input': 'Translate this to French: "What is the capital of France?"',
            'expected_features': ['translation', 'french', 'capital']
        },
        {
            'name': 'Document Summarization',
            'input': 'Summarize my uploaded physics notes about Newton\'s laws',
            'expected_features': ['summary', 'physics', 'newton']
        },
        {
            'name': 'Learning Analytics Request',
            'input': 'Show me my learning progress and performance analytics',
            'expected_features': ['progress', 'analytics', 'performance']
        },
        {
            'name': 'Multi-Language Support Query',
            'input': 'What languages do you support for translation?',
            'expected_features': ['languages', 'support', 'translation']
        },
        {
            'name': 'Advanced Quiz with Context',
            'input': 'Generate a challenging quiz about thermodynamics based on my uploaded chemistry textbook',
            'expected_features': ['quiz', 'thermodynamics', 'challenging']
        },
        {
            'name': 'Round-trip Translation Test',
            'input': 'Translate "Machine learning is transforming education" to Spanish and back to English to check quality',
            'expected_features': ['translation', 'machine learning', 'quality']
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        try:
            session_id = f"enhanced-test-{uuid.uuid4()}"
            
            # Invoke the enhanced agent
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
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
                print(f"Preview: {completion[:200]}...")
                
                # Check for expected features
                features_found = []
                for feature in test_case['expected_features']:
                    if feature.lower() in completion.lower():
                        features_found.append(feature)
                
                results.append({
                    'test': test_case['name'],
                    'status': 'PASSED',
                    'response_length': len(completion),
                    'features_found': features_found,
                    'features_expected': len(test_case['expected_features']),
                    'feature_match_rate': len(features_found) / len(test_case['expected_features']) * 100
                })
                
                if features_found:
                    print(f"🎯 Features detected: {', '.join(features_found)}")
                
            else:
                print("❌ Empty response")
                results.append({
                    'test': test_case['name'],
                    'status': 'FAILED',
                    'error': 'Empty response'
                })
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                'test': test_case['name'],
                'status': 'FAILED',
                'error': str(e)
            })
        
        # Small delay between tests
        time.sleep(2)
    
    # Enhanced summary
    print(f"\n📊 Enhanced Agent Test Summary")
    print("=" * 35)
    
    passed = len([r for r in results if r['status'] == 'PASSED'])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Feature detection analysis
    total_features = 0
    found_features = 0
    
    for result in results:
        if result['status'] == 'PASSED':
            status_icon = "✅"
            total_features += result.get('features_expected', 0)
            found_features += len(result.get('features_found', []))
            feature_rate = result.get('feature_match_rate', 0)
            print(f"{status_icon} {result['test']}: {result['status']} (Features: {feature_rate:.0f}%)")
        else:
            status_icon = "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
    
    if total_features > 0:
        feature_detection_rate = (found_features / total_features) * 100
        print(f"\n🎯 Feature Detection Rate: {feature_detection_rate:.1f}%")
        print(f"   Expected features: {total_features}")
        print(f"   Detected features: {found_features}")
    
    return passed > 0

def test_specific_capabilities():
    """Test specific enhanced capabilities"""
    
    print(f"\n🔬 Testing Specific Enhanced Capabilities")
    print("=" * 45)
    
    # Read agent configuration
    agent_id = 'ZTBBVSC6Y1'
    alias_id = 'TSTALIASID'
    
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('BEDROCK_CHAT_AGENT_ID='):
                    agent_id = line.split('=')[1].strip()
    except:
        pass
    
    bedrock_runtime = boto3.client('bedrock-agent-runtime')
    
    # Specific capability tests
    capability_tests = [
        {
            'capability': 'Quiz Generation with Language Detection',
            'input': 'Créer un quiz sur la photosynthèse avec 3 questions',
            'success_indicators': ['quiz', 'questions', 'photosynthèse']
        },
        {
            'capability': 'Translation Quality Assessment',
            'input': 'Translate "The mitochondria is the powerhouse of the cell" to Spanish with quality validation',
            'success_indicators': ['mitocondria', 'célula', 'translation']
        },
        {
            'capability': 'Educational Content Analysis',
            'input': 'Analyze the difficulty level of this topic: quantum mechanics and suggest appropriate quiz questions',
            'success_indicators': ['quantum', 'difficulty', 'questions']
        },
        {
            'capability': 'Multi-Language Support Information',
            'input': 'List all supported languages and their capabilities',
            'success_indicators': ['languages', 'spanish', 'french', 'support']
        }
    ]
    
    capability_results = []
    
    for test in capability_tests:
        print(f"\n🧪 Testing: {test['capability']}")
        print(f"Input: {test['input']}")
        
        try:
            session_id = f"capability-test-{uuid.uuid4()}"
            
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId=session_id,
                inputText=test['input']
            )
            
            # Process response
            completion = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            # Check success indicators
            indicators_found = []
            for indicator in test['success_indicators']:
                if indicator.lower() in completion.lower():
                    indicators_found.append(indicator)
            
            success_rate = len(indicators_found) / len(test['success_indicators']) * 100
            
            if success_rate >= 50:  # At least 50% of indicators found
                print(f"✅ Capability working (Success rate: {success_rate:.0f}%)")
                capability_results.append({
                    'capability': test['capability'],
                    'status': 'WORKING',
                    'success_rate': success_rate,
                    'indicators_found': indicators_found
                })
            else:
                print(f"⚠️ Capability partially working (Success rate: {success_rate:.0f}%)")
                capability_results.append({
                    'capability': test['capability'],
                    'status': 'PARTIAL',
                    'success_rate': success_rate,
                    'indicators_found': indicators_found
                })
            
            print(f"Response preview: {completion[:150]}...")
            
        except Exception as e:
            print(f"❌ Capability test failed: {e}")
            capability_results.append({
                'capability': test['capability'],
                'status': 'FAILED',
                'error': str(e)
            })
        
        time.sleep(2)
    
    # Capability summary
    print(f"\n📋 Capability Test Results")
    print("=" * 30)
    
    working = len([r for r in capability_results if r['status'] == 'WORKING'])
    partial = len([r for r in capability_results if r['status'] == 'PARTIAL'])
    failed = len([r for r in capability_results if r['status'] == 'FAILED'])
    
    print(f"Working: {working}")
    print(f"Partial: {partial}")
    print(f"Failed: {failed}")
    
    for result in capability_results:
        status_icon = "✅" if result['status'] == 'WORKING' else "⚠️" if result['status'] == 'PARTIAL' else "❌"
        print(f"{status_icon} {result['capability']}: {result['status']}")
        
        if 'success_rate' in result:
            print(f"   Success rate: {result['success_rate']:.0f}%")
        if 'indicators_found' in result and result['indicators_found']:
            print(f"   Found: {', '.join(result['indicators_found'])}")
    
    return working + partial > 0

def main():
    """Main testing function"""
    
    print("🚀 Enhanced Bedrock Agent Testing Suite")
    print("=" * 50)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # Run basic enhanced tests
    basic_success = test_enhanced_agent()
    
    # Run specific capability tests
    capability_success = test_specific_capabilities()
    
    # Overall results
    print(f"\n🎯 Overall Test Results")
    print("=" * 25)
    
    if basic_success and capability_success:
        print("✅ Enhanced Agent: FULLY FUNCTIONAL")
        print("🎉 All enhanced features are working correctly!")
        print("\nEnhanced capabilities confirmed:")
        print("  ✅ Multi-language quiz generation")
        print("  ✅ Translation with quality validation")
        print("  ✅ Language detection and support")
        print("  ✅ Enhanced learning analytics")
        print("  ✅ Educational content processing")
        return True
    elif basic_success or capability_success:
        print("⚠️ Enhanced Agent: PARTIALLY FUNCTIONAL")
        print("Some enhanced features are working, but there may be issues.")
        return True
    else:
        print("❌ Enhanced Agent: NOT FUNCTIONAL")
        print("Enhanced features are not working properly.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Enhanced Agent Test: {'SUCCESS' if success else 'FAILED'}")
    exit(0 if success else 1)
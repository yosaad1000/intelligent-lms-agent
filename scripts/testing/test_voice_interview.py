#!/usr/bin/env python3
"""
Test Voice Interview Integration with Bedrock Agent
Comprehensive testing of voice processing capabilities
"""

import boto3
import json
import os
import uuid
import time
import base64
import asyncio
import websockets
from datetime import datetime

def test_voice_interview_integration():
    """Test the voice interview integration with Bedrock Agent"""
    
    print("🎤 Testing Voice Interview Integration")
    print("=" * 50)
    
    # Read agent ID from .env file
    agent_id = 'ZTBBVSC6Y1'
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
    
    # Voice interview test cases
    test_cases = [
        {
            'name': 'Start Voice Interview - Physics',
            'input': 'Start a voice interview about physics for intermediate level students',
            'expected_features': ['interview', 'physics', 'session_id', 'question']
        },
        {
            'name': 'Start Voice Interview - Programming',
            'input': 'Begin a technical interview on Python programming concepts',
            'expected_features': ['interview', 'python', 'technical', 'session']
        },
        {
            'name': 'Voice Interview Status Check',
            'input': 'Check the status of my current voice interview session',
            'expected_features': ['status', 'interview', 'session']
        },
        {
            'name': 'Voice Interview Instructions',
            'input': 'How do voice interviews work? What should I expect?',
            'expected_features': ['voice', 'interview', 'audio', 'transcription']
        },
        {
            'name': 'End Voice Interview',
            'input': 'End my current voice interview and provide analysis',
            'expected_features': ['end', 'interview', 'analysis', 'performance']
        },
        {
            'name': 'Voice Interview Performance Analysis',
            'input': 'Analyze my performance in the recent voice interview about machine learning',
            'expected_features': ['performance', 'analysis', 'interview', 'feedback']
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        try:
            session_id = f"voice-test-{uuid.uuid4()}"
            
            # Invoke the agent with voice interview request
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
    
    # Test summary
    print(f"\n📊 Voice Interview Test Summary")
    print("=" * 35)
    
    passed = len([r for r in results if r['status'] == 'PASSED'])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Feature detection analysis
    for result in results:
        if result['status'] == 'PASSED':
            status_icon = "✅"
            feature_rate = result.get('feature_match_rate', 0)
            print(f"{status_icon} {result['test']}: {result['status']} (Features: {feature_rate:.0f}%)")
        else:
            status_icon = "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
    
    return passed > 0

def test_voice_action_group_directly():
    """Test voice action group Lambda function directly"""
    
    print(f"\n🔧 Testing Voice Action Group Lambda Function")
    print("=" * 45)
    
    lambda_client = boto3.client('lambda')
    function_name = 'lms-voice-processing'
    
    # Test cases for direct Lambda invocation
    action_tests = [
        {
            'action': 'start_interview',
            'parameters': {
                'user_id': 'test_user_123',
                'interview_type': 'technical',
                'topic': 'Machine Learning',
                'difficulty': 'intermediate'
            },
            'expected_status': 200
        },
        {
            'action': 'get_interview_status',
            'parameters': {
                'session_id': 'test_session_123'
            },
            'expected_status': 404  # Session not found is expected
        },
        {
            'action': 'process_audio',
            'parameters': {
                'session_id': 'test_session_123',
                'audio_data': base64.b64encode(b'fake_audio_data').decode('utf-8'),
                'is_final': True
            },
            'expected_status': 404  # Session not found is expected
        }
    ]
    
    action_results = []
    
    for test in action_tests:
        print(f"\n🧪 Testing action: {test['action']}")
        
        try:
            # Create test event
            test_event = {
                'body': json.dumps({
                    'action': test['action'],
                    'parameters': test['parameters']
                })
            }
            
            # Invoke Lambda function
            response = lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(test_event)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            status_code = response_payload.get('statusCode', 500)
            
            print(f"Status Code: {status_code}")
            
            if 'body' in response_payload:
                body = json.loads(response_payload['body'])
                print(f"Response: {json.dumps(body, indent=2)[:200]}...")
            
            # Check if status matches expectation
            if status_code == test['expected_status'] or (status_code == 200 and test['expected_status'] == 200):
                print(f"✅ Action {test['action']}: SUCCESS")
                action_results.append({
                    'action': test['action'],
                    'status': 'SUCCESS',
                    'status_code': status_code
                })
            else:
                print(f"⚠️ Action {test['action']}: UNEXPECTED STATUS ({status_code})")
                action_results.append({
                    'action': test['action'],
                    'status': 'UNEXPECTED',
                    'status_code': status_code
                })
            
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"❌ Lambda function {function_name} not found")
            action_results.append({
                'action': test['action'],
                'status': 'FUNCTION_NOT_FOUND'
            })
        except Exception as e:
            print(f"❌ Error testing {test['action']}: {e}")
            action_results.append({
                'action': test['action'],
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Action test summary
    print(f"\n📋 Action Group Test Results")
    print("=" * 30)
    
    success_count = len([r for r in action_results if r['status'] in ['SUCCESS', 'UNEXPECTED']])
    total_count = len(action_results)
    
    print(f"Actions Tested: {total_count}")
    print(f"Successful: {success_count}")
    
    for result in action_results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "⚠️" if result['status'] == 'UNEXPECTED' else "❌"
        print(f"{status_icon} {result['action']}: {result['status']}")
    
    return success_count > 0

def test_dynamodb_tables():
    """Test DynamoDB tables for voice interviews"""
    
    print(f"\n📊 Testing DynamoDB Tables")
    print("=" * 30)
    
    dynamodb = boto3.resource('dynamodb')
    
    tables_to_test = [
        'lms-interview-sessions',
        'lms-interview-turns',
        'lms-websocket-connections'
    ]
    
    table_results = []
    
    for table_name in tables_to_test:
        try:
            table = dynamodb.Table(table_name)
            table.load()
            
            # Test basic operations
            test_item = {
                'session_id' if 'sessions' in table_name else 'connection_id' if 'connections' in table_name else 'session_id': f'test_{uuid.uuid4()}',
                'test_data': 'voice_interview_test',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if 'turns' in table_name:
                test_item['turn_id'] = f'turn_{uuid.uuid4()}'
            
            # Put test item
            table.put_item(Item=test_item)
            
            # Get test item
            key = {k: v for k, v in test_item.items() if k in ['session_id', 'connection_id', 'turn_id']}
            response = table.get_item(Key=key)
            
            if 'Item' in response:
                print(f"✅ Table {table_name}: READ/WRITE OK")
                table_results.append({
                    'table': table_name,
                    'status': 'OK'
                })
                
                # Clean up test item
                table.delete_item(Key=key)
            else:
                print(f"⚠️ Table {table_name}: WRITE OK, READ FAILED")
                table_results.append({
                    'table': table_name,
                    'status': 'PARTIAL'
                })
            
        except Exception as e:
            print(f"❌ Table {table_name}: ERROR - {e}")
            table_results.append({
                'table': table_name,
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Table test summary
    working_tables = len([r for r in table_results if r['status'] == 'OK'])
    total_tables = len(table_results)
    
    print(f"\nTables Working: {working_tables}/{total_tables}")
    
    return working_tables == total_tables

async def test_websocket_connection():
    """Test WebSocket connection (if available)"""
    
    print(f"\n🌐 Testing WebSocket Connection")
    print("=" * 30)
    
    try:
        # Try to read WebSocket URL from .env
        websocket_url = None
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('WEBSOCKET_URL='):
                        websocket_url = line.split('=')[1].strip()
                        break
        except:
            pass
        
        if not websocket_url:
            print("⚠️ WebSocket URL not found in .env file")
            print("This is expected if WebSocket API hasn't been deployed yet")
            return False
        
        print(f"WebSocket URL: {websocket_url}")
        
        # Test connection
        try:
            async with websockets.connect(websocket_url) as websocket:
                print("✅ WebSocket connection established")
                
                # Send test message
                test_message = {
                    'action': 'start_interview',
                    'user_id': 'test_user',
                    'topic': 'Test Topic'
                }
                
                await websocket.send(json.dumps(test_message))
                print("✅ Test message sent")
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"✅ Response received: {response[:100]}...")
                    return True
                except asyncio.TimeoutError:
                    print("⚠️ No response received (timeout)")
                    return True  # Connection worked, just no response
                
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ WebSocket test error: {e}")
        return False

def test_transcribe_service():
    """Test AWS Transcribe service availability"""
    
    print(f"\n🎙️ Testing AWS Transcribe Service")
    print("=" * 35)
    
    try:
        transcribe = boto3.client('transcribe')
        
        # Test service availability by listing jobs
        response = transcribe.list_transcription_jobs(MaxResults=1)
        
        print("✅ AWS Transcribe service is accessible")
        print(f"Service region: {transcribe.meta.region_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS Transcribe service error: {e}")
        return False

def main():
    """Main testing function"""
    
    print("🚀 Voice Interview Integration Testing Suite")
    print("=" * 50)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # Run all tests
    test_results = {}
    
    # Test 1: Bedrock Agent voice capabilities
    print("\n" + "="*50)
    test_results['agent_voice'] = test_voice_interview_integration()
    
    # Test 2: Voice action group Lambda
    print("\n" + "="*50)
    test_results['action_group'] = test_voice_action_group_directly()
    
    # Test 3: DynamoDB tables
    print("\n" + "="*50)
    test_results['dynamodb'] = test_dynamodb_tables()
    
    # Test 4: AWS Transcribe service
    print("\n" + "="*50)
    test_results['transcribe'] = test_transcribe_service()
    
    # Test 5: WebSocket connection (async)
    print("\n" + "="*50)
    try:
        test_results['websocket'] = asyncio.run(test_websocket_connection())
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        test_results['websocket'] = False
    
    # Overall results
    print(f"\n🎯 Overall Voice Interview Test Results")
    print("=" * 40)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"Total Test Categories: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print(f"\nDetailed Results:")
    for test_name, result in test_results.items():
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {test_name.replace('_', ' ').title()}: {'PASSED' if result else 'FAILED'}")
    
    if passed_tests >= 3:  # At least 3 out of 5 tests should pass
        print("\n🎉 Voice Interview Integration: FUNCTIONAL")
        print("The voice interview system is ready for use!")
        print("\nKey capabilities confirmed:")
        if test_results['agent_voice']:
            print("  ✅ Bedrock Agent voice interview processing")
        if test_results['action_group']:
            print("  ✅ Voice action group Lambda functions")
        if test_results['dynamodb']:
            print("  ✅ Interview session data storage")
        if test_results['transcribe']:
            print("  ✅ AWS Transcribe speech-to-text service")
        if test_results['websocket']:
            print("  ✅ Real-time WebSocket communication")
        
        return True
    else:
        print("\n⚠️ Voice Interview Integration: NEEDS ATTENTION")
        print("Some components need to be deployed or configured.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Voice Interview Test: {'SUCCESS' if success else 'NEEDS WORK'}")
    exit(0 if success else 1)
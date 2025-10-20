#!/usr/bin/env python3
"""
Test Current Bedrock Agent
Simple test to verify the existing agent works
"""

import boto3
import json
import os
import uuid
from datetime import datetime

def test_current_agent():
    """Test the currently deployed Bedrock agent"""
    
    print("🧪 Testing Current Bedrock Agent")
    print("=" * 40)
    
    # Read agent ID from .env file directly
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
    
    # Test cases
    test_cases = [
        {
            'name': 'Simple Greeting',
            'input': 'Hello, can you help me with my studies?'
        },
        {
            'name': 'Document Summarization Request',
            'input': 'Summarize my uploaded physics notes'
        },
        {
            'name': 'Question About Content',
            'input': 'What is Newton\'s first law of motion?'
        },
        {
            'name': 'Quiz Generation Request',
            'input': 'Create a quiz about thermodynamics'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        try:
            session_id = f"test-{uuid.uuid4()}"
            
            # Invoke the agent
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
                print(f"Preview: {completion[:150]}...")
                results.append({
                    'test': test_case['name'],
                    'status': 'PASSED',
                    'response_length': len(completion)
                })
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
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 20)
    
    passed = len([r for r in results if r['status'] == 'PASSED'])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    for result in results:
        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result.get('error'):
            print(f"   Error: {result['error']}")
    
    return passed > 0

if __name__ == "__main__":
    success = test_current_agent()
    print(f"\n🎯 Agent Test: {'SUCCESS' if success else 'FAILED'}")
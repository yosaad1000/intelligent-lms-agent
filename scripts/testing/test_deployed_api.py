#!/usr/bin/env python3
"""
Test script for deployed RAG-Enhanced Chat API
Tests all endpoints and functionality
"""

import requests
import json
import time

# API Configuration
BASE_URL = "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod"

def test_health_endpoint():
    """Test the health check endpoint"""
    
    print("🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health Check: {data['status']}")
            print(f"   📊 Services: {data['services']}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Health test error: {e}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint"""
    
    print("\n💬 Testing Chat Endpoint...")
    
    test_messages = [
        {
            "user_id": "test-user-123",
            "message": "Hello, can you help me learn about machine learning?",
            "subject_id": "cs101"
        },
        {
            "user_id": "test-user-123", 
            "message": "What are the main types of machine learning?",
            "subject_id": "cs101"
        }
    ]
    
    success_count = 0
    
    for i, test_data in enumerate(test_messages, 1):
        print(f"\n   Test {i}: {test_data['message'][:50]}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json=test_data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success: {data.get('success', 'Unknown')}")
                    print(f"   🤖 Response: {data.get('response', 'No response')[:100]}...")
                    print(f"   🔍 RAG Enhanced: {data.get('rag_enhanced', False)}")
                    print(f"   📚 Documents Used: {data.get('rag_documents_used', 0)}")
                    success_count += 1
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON response: {response.text[:100]}")
            else:
                print(f"   ❌ Chat test failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Chat test error: {e}")
    
    return success_count > 0

def test_file_upload_endpoint():
    """Test the file upload endpoint"""
    
    print("\n📁 Testing File Upload Endpoint...")
    
    test_files = [
        {
            "user_id": "test-user-123",
            "filename": "ml-basics.txt",
            "content": """Machine Learning Fundamentals
            
Machine learning is a subset of artificial intelligence (AI) that enables computers to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.

Types of Machine Learning:
1. Supervised Learning: Uses labeled training data
2. Unsupervised Learning: Finds hidden patterns in data  
3. Reinforcement Learning: Learns through rewards and penalties

Key concepts include training data, features, models, and algorithms.""",
            "subject_id": "cs101"
        },
        {
            "user_id": "test-user-123",
            "filename": "ai-overview.txt", 
            "content": """Artificial Intelligence Overview
            
Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.

Applications of AI:
- Natural Language Processing
- Computer Vision
- Robotics
- Expert Systems
- Machine Learning""",
            "subject_id": "cs101"
        }
    ]
    
    success_count = 0
    
    for i, file_data in enumerate(test_files, 1):
        print(f"\n   Test {i}: Uploading {file_data['filename']}...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/files",
                json=file_data,
                timeout=60,  # File processing may take longer
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Upload Success: {data.get('success', 'Unknown')}")
                    print(f"   📄 File ID: {data.get('file_id', 'Unknown')}")
                    print(f"   🔄 Processing: {data.get('processing_status', 'Unknown')}")
                    success_count += 1
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON response: {response.text[:100]}")
            else:
                print(f"   ❌ Upload failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Upload error: {e}")
    
    return success_count > 0

def test_chat_history_endpoint():
    """Test the chat history endpoint"""
    
    print("\n📜 Testing Chat History Endpoint...")
    
    try:
        # Test getting user conversations
        response = requests.get(
            f"{BASE_URL}/api/chat",
            params={"user_id": "test-user-123"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                conversations = data.get('conversations', [])
                print(f"   ✅ Found {len(conversations)} conversations")
                
                if conversations:
                    print(f"   📋 Latest conversation: {conversations[0].get('title', 'Unknown')}")
                
                return True
            except json.JSONDecodeError:
                print(f"   ⚠️  Non-JSON response: {response.text[:100]}")
        else:
            print(f"   ❌ History test failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ History test error: {e}")
    
    return False

def test_rag_workflow():
    """Test the complete RAG workflow"""
    
    print("\n🔄 Testing Complete RAG Workflow...")
    
    # Step 1: Upload a document
    print("   Step 1: Uploading test document...")
    file_success = test_file_upload_endpoint()
    
    if file_success:
        print("   ⏳ Waiting for document processing...")
        time.sleep(5)  # Wait for processing
        
        # Step 2: Ask questions about the document
        print("   Step 2: Asking questions about uploaded content...")
        
        rag_questions = [
            "What is machine learning according to my documents?",
            "What are the types of machine learning mentioned?",
            "Tell me about artificial intelligence from my files."
        ]
        
        for question in rag_questions:
            print(f"\n   Question: {question}")
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/chat",
                    json={
                        "user_id": "test-user-123",
                        "message": question,
                        "subject_id": "cs101"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rag_enhanced = data.get('rag_enhanced', False)
                    docs_used = data.get('rag_documents_used', 0)
                    
                    print(f"   🔍 RAG Enhanced: {rag_enhanced}")
                    print(f"   📚 Documents Used: {docs_used}")
                    
                    if rag_enhanced and docs_used > 0:
                        print(f"   ✅ RAG workflow working!")
                        return True
                    else:
                        print(f"   ⚠️  RAG not yet active (may need more processing time)")
                
            except Exception as e:
                print(f"   ❌ RAG test error: {e}")
    
    return False

def main():
    """Run all API tests"""
    
    print("🧪 Testing Deployed RAG-Enhanced Chat API")
    print("=" * 60)
    print(f"🌐 API Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Track test results
    results = {
        'health': False,
        'chat': False, 
        'file_upload': False,
        'chat_history': False,
        'rag_workflow': False
    }
    
    # Run tests
    results['health'] = test_health_endpoint()
    results['chat'] = test_chat_endpoint()
    results['file_upload'] = test_file_upload_endpoint()
    results['chat_history'] = test_chat_history_endpoint()
    results['rag_workflow'] = test_rag_workflow()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if results['health']:
        print("\n🎉 Core API is working! Your RAG system is deployed successfully.")
        
        if results['chat']:
            print("💬 Chat functionality is operational.")
            
        if results['file_upload']:
            print("📁 File upload system is working.")
            
        if results['rag_workflow']:
            print("🔄 Complete RAG workflow is functional!")
        else:
            print("⚠️  RAG workflow needs Bedrock Agent configuration for full functionality.")
            
        print(f"\n🌐 Your API is live at: {BASE_URL}")
        print("🚀 Ready for frontend integration!")
        
    else:
        print("\n❌ Core API issues detected. Check CloudWatch logs for details.")
    
    return passed >= 2  # Consider success if at least 2 core tests pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
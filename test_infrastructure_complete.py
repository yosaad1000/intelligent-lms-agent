#!/usr/bin/env python3
"""
Complete Infrastructure Test Script
Tests all deployed Lambda functions and API endpoints
"""

import requests
import json
import time
from datetime import datetime

# API Base URL
BASE_URL = "https://c6bmm2h3sk.execute-api.us-east-1.amazonaws.com/prod"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🔍 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health Status: {health_data['status']}")
            
            for service, status in health_data['services'].items():
                if status == 'healthy' or status == 'configured':
                    print(f"  ✅ {service}: {status}")
                else:
                    print(f"  ⚠️  {service}: {status}")
            
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint"""
    print("\n💬 Testing Chat Endpoint...")
    
    try:
        # Test chat message
        chat_data = {
            "message": "Hello! Can you help me understand machine learning concepts?",
            "user_id": "test-user-123",
            "subject_id": "cs-101"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ Chat Response Received")
            print(f"  📝 Message: {chat_response['response'][:100]}...")
            print(f"  🆔 Conversation ID: {chat_response['conversation_id']}")
            print(f"  ⏰ Timestamp: {chat_response['timestamp']}")
            
            # Test follow-up message in same conversation
            followup_data = {
                "message": "Can you explain neural networks?",
                "user_id": "test-user-123",
                "conversation_id": chat_response['conversation_id']
            }
            
            followup_response = requests.post(
                f"{BASE_URL}/api/chat",
                json=followup_data,
                headers={"Content-Type": "application/json"}
            )
            
            if followup_response.status_code == 200:
                print("✅ Follow-up message successful")
                return True
            else:
                print(f"⚠️  Follow-up message failed: {followup_response.status_code}")
                return False
                
        else:
            print(f"❌ Chat failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        return False

def test_file_endpoints():
    """Test file upload and retrieval endpoints"""
    print("\n📁 Testing File Endpoints...")
    
    try:
        # Test getting files (should be empty initially)
        response = requests.get(f"{BASE_URL}/api/files?user_id=test-user-123")
        
        if response.status_code == 200:
            files_data = response.json()
            print(f"✅ File list retrieved: {files_data['total']} files")
        else:
            print(f"❌ File list failed: {response.status_code}")
            return False
        
        # Test file upload request
        upload_data = {
            "filename": "machine-learning-notes.pdf",
            "file_size": 2048,
            "subject_id": "cs-101",
            "user_id": "test-user-123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/files",
            json=upload_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            upload_response = response.json()
            print(f"✅ File upload URL generated")
            print(f"  🆔 File ID: {upload_response['file_id']}")
            print(f"  📤 Upload URL: {upload_response['upload_url'][:50]}...")
            print(f"  📊 Status: {upload_response['status']}")
            
            # Test getting files again (should show the new file)
            response = requests.get(f"{BASE_URL}/api/files?user_id=test-user-123")
            if response.status_code == 200:
                files_data = response.json()
                print(f"✅ Updated file list: {files_data['total']} files")
                if files_data['total'] > 0:
                    print(f"  📄 Latest file: {files_data['files'][0]['filename']}")
            
            return True
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ File endpoints error: {str(e)}")
        return False

def test_api_performance():
    """Test API performance and response times"""
    print("\n⚡ Testing API Performance...")
    
    endpoints = [
        ("Health", f"{BASE_URL}/api/health", "GET"),
        ("Files", f"{BASE_URL}/api/files?user_id=test-user-123", "GET")
    ]
    
    for name, url, method in endpoints:
        try:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url, json={})
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code in [200, 201]:
                print(f"✅ {name}: {response_time:.0f}ms")
            else:
                print(f"⚠️  {name}: {response_time:.0f}ms (Status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")

def main():
    """Run all infrastructure tests"""
    print("🚀 LMS API Infrastructure Test Suite")
    print("=" * 50)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Health Check", test_health_endpoint),
        ("Chat Functionality", test_chat_endpoint),
        ("File Management", test_file_endpoints),
        ("Performance", test_api_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Infrastructure is ready for development.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
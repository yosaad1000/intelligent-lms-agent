#!/usr/bin/env python3
"""
Test Frontend-Backend Integration for Task 12
Comprehensive testing of API Gateway endpoints and WebSocket functionality
"""

import requests
import json
import time
import asyncio
import websockets
import threading
from datetime import datetime

class FrontendIntegrationTester:
    def __init__(self):
        # Load configuration
        with open('api_config.json', 'r') as f:
            self.config = json.load(f)
        
        self.api_url = self.config['api_gateway_url']
        self.websocket_url = self.config.get('websocket_url', '')
        self.user_id = 'test-user'
        self.session_id = f"test-session-{int(time.time())}"
        
        print(f"🔧 Configuration loaded:")
        print(f"   API URL: {self.api_url}")
        print(f"   WebSocket URL: {self.websocket_url}")
        print(f"   Session ID: {self.session_id}")
    
    def test_api_endpoints(self):
        """Test all REST API endpoints"""
        print("\n🧪 Testing REST API Endpoints")
        print("=" * 40)
        
        tests = [
            ("Health Check", self.test_health),
            ("Capabilities", self.test_capabilities),
            ("Chat Message", self.test_chat),
            ("Session History", self.test_session_history),
            ("Documents List", self.test_documents),
            ("Presigned Upload", self.test_presigned_upload)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 Testing {test_name}...")
                result = test_func()
                results.append((test_name, result, None))
                print(f"✅ {test_name}: PASSED")
            except Exception as e:
                results.append((test_name, False, str(e)))
                print(f"❌ {test_name}: FAILED - {e}")
        
        return results
    
    def test_health(self):
        """Test health endpoint"""
        response = requests.get(f"{self.api_url}/api/v1/health", timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Health check failed: {data.get('error')}")
        
        if not data.get('agent_responsive'):
            raise Exception("Agent not responsive")
        
        print(f"   Agent ID: {data.get('agent_id')}")
        print(f"   Status: {data.get('status')}")
        return True
    
    def test_capabilities(self):
        """Test capabilities endpoint"""
        response = requests.get(f"{self.api_url}/api/v1/capabilities", timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Capabilities test failed: {data.get('error')}")
        
        capabilities = data.get('capabilities', [])
        if len(capabilities) == 0:
            raise Exception("No capabilities returned")
        
        print(f"   Capabilities: {len(capabilities)}")
        for cap in capabilities[:3]:
            print(f"     - {cap}")
        if len(capabilities) > 3:
            print(f"     ... and {len(capabilities) - 3} more")
        
        return True
    
    def test_chat(self):
        """Test chat endpoint with Bedrock Agent"""
        payload = {
            "message": "Hello! Can you help me understand machine learning concepts?",
            "session_id": self.session_id,
            "user_id": self.user_id
        }
        
        response = requests.post(
            f"{self.api_url}/api/v1/chat",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Chat failed: {data.get('error')}")
        
        agent_response = data.get('response', '')
        if len(agent_response) < 10:
            raise Exception("Agent response too short")
        
        print(f"   Response length: {len(agent_response)} characters")
        print(f"   Tools used: {data.get('tools_used', [])}")
        print(f"   Citations: {len(data.get('citations', []))}")
        print(f"   Preview: {agent_response[:100]}...")
        
        return True
    
    def test_session_history(self):
        """Test session history endpoint"""
        response = requests.get(
            f"{self.api_url}/api/v1/session/history?session_id={self.session_id}",
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Session history failed: {data.get('error')}")
        
        history = data.get('conversation_history', [])
        print(f"   History entries: {len(history)}")
        
        return True
    
    def test_documents(self):
        """Test documents list endpoint"""
        response = requests.get(
            f"{self.api_url}/api/v1/documents?user_id={self.user_id}",
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Documents test failed: {data.get('error')}")
        
        documents = data.get('documents', [])
        print(f"   Documents found: {len(documents)}")
        
        return True
    
    def test_presigned_upload(self):
        """Test presigned URL generation"""
        payload = {
            "file_name": "test-document.pdf",
            "content_type": "application/pdf",
            "user_id": self.user_id
        }
        
        response = requests.post(
            f"{self.api_url}/api/v1/upload/presigned",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        data = response.json()
        if not data.get('success'):
            raise Exception(f"Presigned URL failed: {data.get('error')}")
        
        upload_url = data.get('upload_url', '')
        if not upload_url.startswith('https://'):
            raise Exception("Invalid upload URL")
        
        print(f"   Upload URL generated: {upload_url[:50]}...")
        print(f"   File key: {data.get('file_key')}")
        
        return True
    
    def test_websocket_connection(self):
        """Test WebSocket connection and messaging"""
        if not self.websocket_url:
            print("⚠️ WebSocket URL not available, skipping WebSocket tests")
            return []
        
        print("\n🔌 Testing WebSocket Connection")
        print("=" * 35)
        
        results = []
        
        try:
            # Test WebSocket connection
            print("🔍 Testing WebSocket connection...")
            
            async def test_websocket():
                ws_url = f"{self.websocket_url}?user_id={self.user_id}"
                
                try:
                    async with websockets.connect(ws_url) as websocket:
                        print("✅ WebSocket connected successfully")
                        
                        # Test sending a message
                        message = {
                            "action": "sendMessage",
                            "message": "Hello via WebSocket!",
                            "session_id": f"ws-{self.session_id}",
                            "user_id": self.user_id
                        }
                        
                        await websocket.send(json.dumps(message))
                        print("✅ Message sent via WebSocket")
                        
                        # Wait for response
                        response_received = False
                        timeout = 30
                        start_time = time.time()
                        
                        while time.time() - start_time < timeout:
                            try:
                                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                                data = json.loads(response)
                                
                                print(f"📨 WebSocket message received: {data.get('type')}")
                                
                                if data.get('type') == 'final_response':
                                    print(f"   Response: {data.get('content', '')[:100]}...")
                                    response_received = True
                                    break
                                elif data.get('type') == 'error':
                                    raise Exception(f"WebSocket error: {data.get('message')}")
                                    
                            except asyncio.TimeoutError:
                                continue
                        
                        if response_received:
                            print("✅ WebSocket response received")
                            return True
                        else:
                            raise Exception("No response received within timeout")
                            
                except Exception as e:
                    print(f"❌ WebSocket test failed: {e}")
                    return False
            
            # Run async WebSocket test
            result = asyncio.run(test_websocket())
            results.append(("WebSocket Connection", result, None))
            
        except Exception as e:
            results.append(("WebSocket Connection", False, str(e)))
            print(f"❌ WebSocket test failed: {e}")
        
        return results
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        print("\n🌐 Testing CORS Configuration")
        print("=" * 30)
        
        try:
            response = requests.options(f"{self.api_url}/api/v1/health", timeout=30)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print("CORS Headers:")
            for header, value in cors_headers.items():
                print(f"   {header}: {value}")
            
            if cors_headers['Access-Control-Allow-Origin'] == '*':
                print("✅ CORS configuration is correct")
                return True
            else:
                print("⚠️ CORS configuration may need adjustment")
                return False
                
        except Exception as e:
            print(f"❌ CORS test failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests and generate report"""
        print("🚀 LMS Frontend-Backend Integration Test")
        print("Task 12: Frontend-Backend API Integration")
        print("=" * 50)
        
        start_time = time.time()
        
        # Test REST API endpoints
        api_results = self.test_api_endpoints()
        
        # Test CORS
        cors_result = self.test_cors_headers()
        
        # Test WebSocket
        ws_results = self.test_websocket_connection()
        
        # Generate report
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n📊 Test Results Summary")
        print("=" * 30)
        
        all_results = api_results + ws_results
        if cors_result:
            all_results.append(("CORS Configuration", True, None))
        else:
            all_results.append(("CORS Configuration", False, "CORS headers not properly configured"))
        
        passed = sum(1 for _, result, _ in all_results if result)
        total = len(all_results)
        
        for test_name, result, error in all_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if error:
                print(f"      Error: {error}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        print(f"Duration: {duration:.1f} seconds")
        
        if passed == total:
            print("\n🎉 All tests passed! Frontend-Backend integration is working correctly.")
            print("\n📋 Integration Status:")
            print("✅ REST API endpoints functional")
            print("✅ Bedrock Agent responding correctly")
            print("✅ CORS configured for frontend access")
            if self.websocket_url:
                print("✅ WebSocket real-time chat working")
            print("✅ File upload system operational")
            print("✅ Session management working")
            
            print("\n🎯 Ready for Frontend Integration:")
            print("1. Update frontend .env files with API URLs")
            print("2. Configure frontend to use apiBedrockAgentService")
            print("3. Test StudyChat component with real API")
            print("4. Implement file upload in DocumentManager")
            print("5. Add WebSocket support for real-time chat")
            
            return True
        else:
            print(f"\n⚠️ {total - passed} tests failed. Check the logs above for details.")
            return False

def main():
    """Main test function"""
    tester = FrontendIntegrationTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎊 Task 12 Implementation Complete!")
        print("Frontend-Backend API Integration is fully functional.")
    else:
        print("\n❌ Task 12 needs attention. Some tests failed.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
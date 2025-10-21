#!/usr/bin/env python3
"""
Test API Gateway Endpoints for Task 12: Frontend-Backend API Integration
"""

import requests
import json
import time
from datetime import datetime

def load_config():
    """Load API configuration"""
    try:
        with open('api_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ api_config.json not found. Run deployment first.")
        return None

def test_health_endpoint(api_url):
    """Test health check endpoint"""
    print("\n🏥 Testing Health Endpoint")
    print("-" * 30)
    
    try:
        url = f"{api_url}/api/v1/health"
        print(f"GET {url}")
        
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Health check failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_capabilities_endpoint(api_url):
    """Test capabilities endpoint"""
    print("\n🎯 Testing Capabilities Endpoint")
    print("-" * 35)
    
    try:
        url = f"{api_url}/api/v1/capabilities"
        print(f"GET {url}")
        
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Capabilities check passed")
            print(f"Available capabilities: {len(data.get('capabilities', []))}")
            for capability in data.get('capabilities', []):
                print(f"  - {capability}")
            return True
        else:
            print(f"❌ Capabilities check failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Capabilities check error: {e}")
        return False

def test_chat_endpoint(api_url):
    """Test chat endpoint with Bedrock Agent"""
    print("\n💬 Testing Chat Endpoint")
    print("-" * 25)
    
    try:
        url = f"{api_url}/api/v1/chat"
        print(f"POST {url}")
        
        # Test message
        payload = {
            "message": "Hello! Can you help me with my studies?",
            "session_id": f"test-session-{int(time.time())}",
            "user_id": "test-user"
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            url, 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat test passed")
            print(f"Agent Response: {data.get('response', 'No response')[:200]}...")
            print(f"Session ID: {data.get('session_id')}")
            print(f"Tools Used: {data.get('tools_used', [])}")
            print(f"Citations: {len(data.get('citations', []))} citations")
            return True
        else:
            print(f"❌ Chat test failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat test error: {e}")
        return False

def test_cors_headers(api_url):
    """Test CORS headers"""
    print("\n🌐 Testing CORS Headers")
    print("-" * 25)
    
    try:
        url = f"{api_url}/api/v1/health"
        print(f"OPTIONS {url}")
        
        response = requests.options(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print("CORS Headers:")
        for header, value in cors_headers.items():
            print(f"  {header}: {value}")
        
        if cors_headers['Access-Control-Allow-Origin'] == '*':
            print("✅ CORS configuration looks good")
            return True
        else:
            print("⚠️ CORS may need adjustment")
            return False
            
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def test_documents_endpoint(api_url):
    """Test documents listing endpoint"""
    print("\n📁 Testing Documents Endpoint")
    print("-" * 30)
    
    try:
        url = f"{api_url}/api/v1/documents?user_id=test-user"
        print(f"GET {url}")
        
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Documents endpoint working")
            print(f"Documents found: {data.get('count', 0)}")
            return True
        else:
            print(f"❌ Documents test failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Documents test error: {e}")
        return False

def test_upload_presigned_url(api_url):
    """Test presigned URL generation"""
    print("\n📤 Testing Upload Presigned URL")
    print("-" * 35)
    
    try:
        url = f"{api_url}/api/v1/upload/presigned"
        print(f"POST {url}")
        
        payload = {
            "file_name": "test-document.pdf",
            "content_type": "application/pdf",
            "user_id": "test-user"
        }
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Presigned URL generation working")
                print(f"Upload URL generated: {data.get('upload_url', '')[:50]}...")
                print(f"File key: {data.get('file_key')}")
                return True
            else:
                print(f"❌ Presigned URL generation failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Presigned URL test failed")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Presigned URL test error: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 LMS API Gateway Endpoint Testing")
    print("Task 12: Frontend-Backend API Integration")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    if not config:
        return False
    
    api_url = config['api_gateway_url']
    print(f"Testing API: {api_url}")
    
    # Run tests
    tests = [
        ("Health Check", lambda: test_health_endpoint(api_url)),
        ("Capabilities", lambda: test_capabilities_endpoint(api_url)),
        ("CORS Headers", lambda: test_cors_headers(api_url)),
        ("Documents List", lambda: test_documents_endpoint(api_url)),
        ("Upload Presigned URL", lambda: test_upload_presigned_url(api_url)),
        ("Chat with Agent", lambda: test_chat_endpoint(api_url))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API Gateway is ready for frontend integration.")
        
        # Create frontend environment file
        create_frontend_env_file(config)
        
        return True
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        return False

def create_frontend_env_file(config):
    """Create environment file for frontend"""
    print("\n📝 Creating Frontend Environment Configuration")
    
    env_content = f"""# LMS Frontend Environment Configuration
# Generated on {datetime.utcnow().isoformat()}

# API Configuration
VITE_API_GATEWAY_URL={config['api_gateway_url']}
VITE_WEBSOCKET_URL={config.get('websocket_url', '')}
VITE_AWS_REGION={config['region']}

# Bedrock Agent Configuration
VITE_BEDROCK_AGENT_ID={config['bedrock_agent_id']}
VITE_BEDROCK_AGENT_ALIAS_ID={config['bedrock_agent_alias_id']}

# Storage Configuration
VITE_DOCUMENTS_BUCKET={config['documents_bucket']}

# Development Configuration
VITE_USE_MOCK_AGENT=false
VITE_USE_API_PROXY=true
VITE_NODE_ENV=production

# Supabase (for authentication)
VITE_SUPABASE_URL=https://scijpejtvneuqbhkoxuz.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjaWpwZWp0dm5ldXFiaGtveHV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU1OTcxNDEsImV4cCI6MjA3MTE3MzE0MX0.Z6Q_DmsuHYOOvCGed5hcKDrT93XPL5hHwCyGDREcmmw
"""
    
    # Write to frontend directory
    frontend_env_path = 'frontend_extracted/frontend/.env.production'
    with open(frontend_env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Frontend environment file created: {frontend_env_path}")
    
    # Also create a local copy
    with open('.env.frontend', 'w') as f:
        f.write(env_content)
    
    print("✅ Local environment file created: .env.frontend")

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
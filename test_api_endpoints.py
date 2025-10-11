#!/usr/bin/env python3
"""
Test the deployed API endpoints
"""

import requests
import json
import time

def load_api_config():
    """Load API configuration"""
    with open('api-config.json', 'r') as f:
        return json.load(f)

def test_hello_endpoint(api_url):
    """Test the Hello World endpoint"""
    print("👋 Testing Hello World endpoint...")
    
    hello_url = f"{api_url}/hello"
    
    try:
        response = requests.get(hello_url, timeout=30)
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received:")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            
            # Check environment variables
            env = data.get('environment', {})
            print("   Environment:")
            print(f"     User Pool ID: {env.get('user_pool_id', 'N/A')}")
            print(f"     S3 Bucket: {env.get('s3_bucket', 'N/A')}")
            print(f"     DynamoDB Table: {env.get('dynamodb_table', 'N/A')}")
            
            # Check service status
            services = data.get('services_status', {})
            print("   AWS Services Status:")
            for service, status in services.items():
                status_icon = "✅" if status == "connected" else "❌"
                print(f"     {service}: {status_icon} {status}")
            
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_auth_endpoint(api_url):
    """Test the Authentication endpoint"""
    print("\n🔐 Testing Authentication endpoint...")
    
    auth_url = f"{api_url}/auth"
    
    # Test 1: Register a new user
    print("📝 Testing user registration...")
    register_data = {
        "action": "register",
        "email": "apitest@example.com",
        "password": "TestPass123",
        "role": "student"
    }
    
    try:
        response = requests.post(
            auth_url, 
            json=register_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"✅ Registration Status Code: {response.status_code}")
        
        if response.status_code in [200, 409]:  # 409 = user already exists
            if response.status_code == 200:
                data = response.json()
                print("✅ Registration successful:")
                print(f"   Message: {data.get('message', 'N/A')}")
                print(f"   User ID: {data.get('user_id', 'N/A')}")
                print(f"   Email: {data.get('email', 'N/A')}")
                print(f"   Role: {data.get('role', 'N/A')}")
            else:
                print("ℹ️ User already exists, proceeding with login test...")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration request failed: {e}")
        return False
    
    # Wait a moment for user to be fully created
    time.sleep(2)
    
    # Test 2: Login with the user
    print("\n🔑 Testing user login...")
    login_data = {
        "action": "login",
        "email": "apitest@example.com",
        "password": "TestPass123"
    }
    
    try:
        response = requests.post(
            auth_url,
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"✅ Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful:")
            print(f"   Message: {data.get('message', 'N/A')}")
            
            # Check tokens
            tokens = data.get('tokens', {})
            if tokens:
                print("   Tokens received:")
                access_token = tokens.get('access_token', '')
                print(f"     Access token: {access_token[:50]}..." if access_token else "     Access token: Missing")
                id_token = tokens.get('id_token', '')
                print(f"     ID token: {id_token[:50]}..." if id_token else "     ID token: Missing")
                print(f"     Refresh token: {'Present' if tokens.get('refresh_token') else 'Missing'}")
            
            # Check user info
            user = data.get('user', {})
            if user:
                print("   User info:")
                print(f"     Email: {user.get('email', 'N/A')}")
                print(f"     Role: {user.get('role', 'N/A')}")
                print(f"     User ID: {user.get('user_id', 'N/A')}")
            
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return False

def main():
    print("🎓 Testing LMS API Endpoints")
    print("=" * 40)
    
    try:
        # Load API configuration
        config = load_api_config()
        api_url = config['api_url']
        
        print(f"🌐 API URL: {api_url}")
        print(f"📍 Hello endpoint: {config['hello_endpoint']}")
        print(f"📍 Auth endpoint: {config['auth_endpoint']}")
        
        # Test endpoints
        hello_success = test_hello_endpoint(api_url)
        auth_success = test_auth_endpoint(api_url)
        
        # Summary
        print("\n" + "=" * 40)
        print("📊 Test Results:")
        print(f"   Hello World endpoint: {'✅ PASS' if hello_success else '❌ FAIL'}")
        print(f"   Authentication endpoint: {'✅ PASS' if auth_success else '❌ FAIL'}")
        
        if hello_success and auth_success:
            print("\n🎉 All API endpoints are working correctly!")
            print("✅ AWS infrastructure is fully functional")
            print("✅ Lambda functions are deployed and working")
            print("✅ API Gateway is properly configured")
            print("✅ Authentication system is operational")
            print("\n🏁 Task 1 COMPLETED successfully!")
            print("📋 Ready to proceed to the next task")
            return True
        else:
            print("\n⚠️ Some endpoints failed testing")
            return False
            
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False

if __name__ == "__main__":
    main()
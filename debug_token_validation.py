#!/usr/bin/env python3
"""
Debug token validation endpoint
"""

import requests
import json

# API Configuration
API_BASE_URL = "https://djinft5ljj.execute-api.us-east-1.amazonaws.com/dev"

def test_login_and_validate():
    """Test login and then validate the token"""
    print("🧪 Testing login and token validation...")
    
    # First, login to get a token
    login_payload = {
        "action": "login",
        "email": "test.user.1760039613@example.com",  # Use the user from previous test
        "password": "TestPass123"
    }
    
    try:
        print("1. Logging in...")
        login_response = requests.post(f"{API_BASE_URL}/auth", json=login_payload)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"   Login failed: {login_response.text}")
            return
        
        login_result = login_response.json()
        access_token = login_result['tokens']['access_token']
        print(f"   Access token: {access_token[:50]}...")
        
        # Now test token validation
        print("\n2. Validating token...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        validate_response = requests.get(f"{API_BASE_URL}/auth/validate", headers=headers)
        print(f"   Validation status: {validate_response.status_code}")
        print(f"   Validation response: {validate_response.text}")
        
        if validate_response.status_code == 200:
            validate_result = validate_response.json()
            print(f"   Token valid: {validate_result.get('valid')}")
            print(f"   User: {validate_result.get('user')}")
        else:
            print(f"   Validation failed: {validate_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_direct_validation():
    """Test validation endpoint directly"""
    print("\n🧪 Testing validation endpoint directly...")
    
    # Test without token
    print("1. Testing without Authorization header...")
    response = requests.get(f"{API_BASE_URL}/auth/validate")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # Test with invalid token
    print("\n2. Testing with invalid token...")
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{API_BASE_URL}/auth/validate", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")

if __name__ == "__main__":
    test_direct_validation()
    test_login_and_validate()
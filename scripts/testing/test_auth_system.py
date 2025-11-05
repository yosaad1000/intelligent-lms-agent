#!/usr/bin/env python3
"""
Test script for the authentication system
Tests registration, login, and token validation
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "https://djinft5ljj.execute-api.us-east-1.amazonaws.com/dev"

def test_registration():
    """Test user registration"""
    print("🧪 Testing User Registration...")
    
    test_email = f"test.user.{int(time.time())}@example.com"
    test_password = "TestPass123"
    
    payload = {
        "action": "register",
        "email": test_email,
        "password": test_password,
        "role": "student"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth", json=payload)
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ Registration successful for {test_email}")
            print(f"   User ID: {result.get('user_id')}")
            return test_email, test_password
        else:
            print(f"❌ Registration failed: {result.get('error')}")
            return None, None
            
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return None, None

def test_login(email, password):
    """Test user login"""
    print(f"\n🧪 Testing User Login for {email}...")
    
    payload = {
        "action": "login",
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth", json=payload)
        result = response.json()
        
        if response.status_code == 200:
            print("✅ Login successful")
            tokens = result.get('tokens', {})
            user = result.get('user', {})
            
            print(f"   User: {user.get('email')} ({user.get('role')})")
            print(f"   Access Token: {tokens.get('access_token')[:50]}...")
            
            return tokens.get('access_token')
        else:
            print(f"❌ Login failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None

def test_token_validation(access_token):
    """Test token validation"""
    print(f"\n🧪 Testing Token Validation...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/auth/validate", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Token validation successful")
            user = result.get('user', {})
            print(f"   Valid: {result.get('valid')}")
            print(f"   User: {user.get('email')} ({user.get('role')})")
            return True
        else:
            try:
                result = response.json()
                print(f"❌ Token validation failed: {result.get('error')}")
            except:
                print(f"❌ Token validation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Token validation error: {str(e)}")
        return False

def test_invalid_login():
    """Test login with invalid credentials"""
    print(f"\n🧪 Testing Invalid Login...")
    
    payload = {
        "action": "login",
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth", json=payload)
        result = response.json()
        
        if response.status_code == 401:
            print("✅ Invalid login correctly rejected")
            return True
        else:
            print(f"❌ Invalid login should have been rejected: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Invalid login test error: {str(e)}")
        return False

def test_duplicate_registration(email, password):
    """Test duplicate registration"""
    print(f"\n🧪 Testing Duplicate Registration...")
    
    payload = {
        "action": "register",
        "email": email,
        "password": password,
        "role": "student"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth", json=payload)
        result = response.json()
        
        if response.status_code == 409:
            print("✅ Duplicate registration correctly rejected")
            return True
        else:
            print(f"❌ Duplicate registration should have been rejected: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Duplicate registration test error: {str(e)}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 Starting Authentication System Tests")
    print("=" * 50)
    
    # Test 1: Registration
    email, password = test_registration()
    if not email:
        print("\n❌ Registration test failed - stopping tests")
        return
    
    # Test 2: Login
    access_token = test_login(email, password)
    if not access_token:
        print("\n❌ Login test failed - stopping tests")
        return
    
    # Test 3: Token Validation
    token_valid = test_token_validation(access_token)
    if not token_valid:
        print("\n❌ Token validation test failed")
    
    # Test 4: Invalid Login
    invalid_login_test = test_invalid_login()
    
    # Test 5: Duplicate Registration
    duplicate_test = test_duplicate_registration(email, password)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Registration: {'✅' if email else '❌'}")
    print(f"   Login: {'✅' if access_token else '❌'}")
    print(f"   Token Validation: {'✅' if token_valid else '❌'}")
    print(f"   Invalid Login Rejection: {'✅' if invalid_login_test else '❌'}")
    print(f"   Duplicate Registration Rejection: {'✅' if duplicate_test else '❌'}")
    
    all_passed = all([email, access_token, token_valid, invalid_login_test, duplicate_test])
    
    if all_passed:
        print("\n🎉 All authentication tests passed!")
        print("\n📋 Manual Test Instructions:")
        print("1. Open frontend/index.html in a web browser")
        print("2. Register a new user account")
        print("3. Login with the registered credentials")
        print("4. Verify you are redirected to dashboard.html")
        print("5. Verify the dashboard shows your user information")
        print("6. Test the logout functionality")
    else:
        print("\n❌ Some tests failed - check the authentication system")

if __name__ == "__main__":
    main()
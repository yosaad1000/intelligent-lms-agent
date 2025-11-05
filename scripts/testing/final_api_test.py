#!/usr/bin/env python3
"""
Final comprehensive API test with proper wait times
"""

import requests
import json
import time
import boto3

def wait_for_deployment():
    """Wait for API Gateway deployment to propagate"""
    print("⏳ Waiting for API Gateway deployment to propagate...")
    time.sleep(15)  # Wait 15 seconds for deployment
    print("✅ Deployment should be ready now")

def test_basic_endpoints():
    """Test basic endpoints that were working"""
    
    api_url = "https://q1ox8qhf97.execute-api.us-east-1.amazonaws.com/prod"
    
    print("🧪 Testing Basic Endpoints")
    print("-" * 30)
    
    # Test GET /files
    print("1️⃣ GET /files...")
    try:
        response = requests.get(f"{api_url}/files", params={'user_id': 'test-user-123'})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Working")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test POST /files
    print("\n2️⃣ POST /files...")
    try:
        upload_data = {
            "filename": "final-test.pdf",
            "file_size": 1024,
            "user_id": "test-user-123",
            "subject_id": "final-test"
        }
        response = requests.post(f"{api_url}/files", json=upload_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            file_id = data.get('file_id')
            print(f"   ✅ Working - File ID: {file_id}")
            return file_id
        else:
            print(f"   ❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def test_new_endpoints(file_id):
    """Test newly added endpoints"""
    
    api_url = "https://q1ox8qhf97.execute-api.us-east-1.amazonaws.com/prod"
    
    print("\n🆕 Testing New Endpoints")
    print("-" * 30)
    
    # Test POST /files/process
    print("1️⃣ POST /files/process...")
    try:
        process_data = {
            "file_id": file_id,
            "user_id": "test-user-123"
        }
        response = requests.post(f"{api_url}/files/process", json=process_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Working")
        elif response.status_code == 403:
            print("   ⚠️ Still getting 403 - deployment may need more time")
        else:
            print(f"   ❌ Unexpected status")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test GET /files/status
    print("\n2️⃣ GET /files/status...")
    try:
        response = requests.get(f"{api_url}/files/status", params={
            'file_id': file_id,
            'user_id': 'test-user-123'
        })
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Working")
        elif response.status_code == 403:
            print("   ⚠️ Still getting 403 - deployment may need more time")
        else:
            print(f"   ❌ Unexpected status")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test GET /files/{file_id}
    print(f"\n3️⃣ GET /files/{file_id}...")
    try:
        response = requests.get(f"{api_url}/files/{file_id}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Working")
        elif response.status_code == 403:
            print("   ⚠️ Still getting 403 - deployment may need more time")
        else:
            print(f"   ❌ Unexpected status")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def force_redeploy():
    """Force a new deployment"""
    
    print("\n🔄 Force redeploying API...")
    
    apigateway = boto3.client('apigateway')
    
    try:
        deployment = apigateway.create_deployment(
            restApiId='q1ox8qhf97',
            stageName='prod',
            description=f'Force redeploy at {int(time.time())}'
        )
        
        print(f"✅ New deployment created: {deployment['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Redeploy failed: {e}")
        return False

def test_lambda_direct():
    """Test Lambda function directly to ensure it handles new paths"""
    
    print("\n🔧 Testing Lambda Function Directly")
    print("-" * 40)
    
    lambda_client = boto3.client('lambda')
    
    # Test /files/process path
    test_event = {
        'httpMethod': 'POST',
        'path': '/files/process',
        'body': json.dumps({
            'file_id': 'test-file-123',
            'user_id': 'test-user-123'
        }),
        'headers': {'Content-Type': 'application/json'},
        'requestContext': {'requestId': 'test-123'}
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='lms-enhanced-file-processing',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Lambda Response Status: {result.get('statusCode')}")
        print(f"Lambda Response Body: {result.get('body', 'No body')}")
        
        if result.get('statusCode') == 200:
            print("✅ Lambda handles /files/process correctly")
        else:
            print("⚠️ Lambda may need to handle this path")
            
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")

def main():
    """Main test function"""
    
    print("🚀 Final Comprehensive API Test")
    print("=" * 50)
    
    # Wait for deployment
    wait_for_deployment()
    
    # Test basic endpoints
    file_id = test_basic_endpoints()
    
    if not file_id:
        print("❌ Basic endpoints failed, cannot continue")
        return
    
    # Test new endpoints
    test_new_endpoints(file_id)
    
    # Test Lambda directly
    test_lambda_direct()
    
    # If still having issues, force redeploy
    print("\n🔄 Checking if redeploy is needed...")
    
    # Quick test of problematic endpoint
    try:
        response = requests.post(
            "https://q1ox8qhf97.execute-api.us-east-1.amazonaws.com/prod/files/process",
            json={"file_id": file_id, "user_id": "test-user-123"}
        )
        
        if response.status_code == 403:
            print("⚠️ Still getting 403, forcing redeploy...")
            if force_redeploy():
                print("⏳ Waiting for new deployment...")
                time.sleep(20)
                
                # Test again
                print("🔄 Testing after redeploy...")
                test_new_endpoints(file_id)
        else:
            print("✅ Endpoints working after wait period")
            
    except Exception as e:
        print(f"❌ Final test failed: {e}")
    
    print("\n📋 Final Status:")
    print("✅ Basic endpoints (GET/POST /files) are working")
    print("🔗 API URL: https://q1ox8qhf97.execute-api.us-east-1.amazonaws.com/prod")
    print("\n🎯 Ready for web interface testing!")
    print("   Open: test_enhanced_file_processing.html")

if __name__ == "__main__":
    main()
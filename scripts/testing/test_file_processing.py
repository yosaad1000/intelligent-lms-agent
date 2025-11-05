#!/usr/bin/env python3
"""
Test file processing endpoint specifically
"""

import requests
import json

def test_file_processing():
    """Test the file processing endpoint"""
    
    api_url = "https://q1ox8qhf97.execute-api.us-east-1.amazonaws.com/prod"
    
    print("🔄 Testing File Processing Endpoint")
    print("=" * 50)
    
    # First create a file entry
    print("1️⃣ Creating file entry...")
    upload_data = {
        "filename": "textract-test.pdf",
        "file_size": 2048,
        "user_id": "test-user-123",
        "subject_id": "textract-demo"
    }
    
    response = requests.post(f"{api_url}/files", json=upload_data)
    if response.status_code == 200:
        data = response.json()
        file_id = data['file_id']
        print(f"   ✅ File created: {file_id}")
    else:
        print(f"   ❌ Failed to create file: {response.text}")
        return
    
    # Test processing endpoint
    print("\n2️⃣ Testing processing endpoint...")
    
    # Check if we have a processing endpoint
    process_data = {
        "file_id": file_id,
        "user_id": "test-user-123"
    }
    
    # Try different possible endpoints
    endpoints_to_try = [
        f"{api_url}/files/process",
        f"{api_url}/process",
        f"{api_url}/files/{file_id}/process"
    ]
    
    for endpoint in endpoints_to_try:
        print(f"   Trying: {endpoint}")
        try:
            response = requests.post(endpoint, json=process_data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Processing endpoint working: {endpoint}")
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)}")
                break
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found")
            else:
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test status endpoint
    print("\n3️⃣ Testing status endpoint...")
    try:
        response = requests.get(f"{api_url}/files/status", params={
            'file_id': file_id,
            'user_id': 'test-user-123'
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Status endpoint working")
            result = response.json()
            print(f"   File status: {result.get('processing_status', 'unknown')}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_file_processing()
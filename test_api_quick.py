#!/usr/bin/env python3
"""
Quick API test script
"""

import boto3
import json
import requests
import time

def test_lambda_direct():
    """Test Lambda function directly"""
    
    lambda_client = boto3.client('lambda')
    
    # Test GET files
    test_event = {
        'httpMethod': 'GET',
        'path': '/files',
        'queryStringParameters': {'user_id': 'test-user-123'},
        'body': None,
        'headers': {'Content-Type': 'application/json'},
        'requestContext': {'requestId': 'test-123'}
    }
    
    print("🧪 Testing Lambda function directly...")
    
    try:
        response = lambda_client.invoke(
            FunctionName='lms-enhanced-file-processing',
            Payload=json.dumps(test_event)
        )
        
        result = json.loads(response['Payload'].read())
        print("✅ Lambda Response:")
        print(json.dumps(result, indent=2))
        return True
        
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")
        return False

def test_api_gateway():
    """Test API Gateway endpoint"""
    
    api_url = "https://q1ox8qhf97.execute-api.us-east-1.amazonaws.com/prod"
    
    print(f"🌐 Testing API Gateway: {api_url}")
    
    try:
        # Test GET request
        response = requests.get(f"{api_url}/files", params={'user_id': 'test-user-123'})
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API Gateway working!")
            return True
        else:
            print(f"❌ API Gateway returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API Gateway test failed: {e}")
        return False

def fix_api_gateway():
    """Fix API Gateway configuration"""
    
    print("🔧 Fixing API Gateway configuration...")
    
    apigateway = boto3.client('apigateway')
    api_id = 'q1ox8qhf97'
    
    try:
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        # Find files resource
        files_resource_id = None
        for resource in resources['items']:
            if resource.get('pathPart') == 'files':
                files_resource_id = resource['id']
                break
        
        if not files_resource_id:
            print("❌ Files resource not found")
            return False
        
        # Check if integration exists
        try:
            integration = apigateway.get_integration(
                restApiId=api_id,
                resourceId=files_resource_id,
                httpMethod='GET'
            )
            print("✅ Integration exists")
        except:
            print("❌ No integration found, creating...")
            
            # Create integration
            lambda_arn = "arn:aws:lambda:us-east-1:145023137830:function:lms-enhanced-file-processing"
            
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=files_resource_id,
                httpMethod='GET',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
            )
            
            print("✅ Integration created")
        
        # Deploy API
        apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Fixed deployment'
        )
        
        print("✅ API deployed")
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Quick API Test")
    print("=" * 50)
    
    # Test Lambda directly
    lambda_ok = test_lambda_direct()
    
    print("\n" + "=" * 50)
    
    # Test API Gateway
    api_ok = test_api_gateway()
    
    if not api_ok and lambda_ok:
        print("\n🔧 Lambda works but API Gateway doesn't. Fixing...")
        fix_api_gateway()
        
        print("\n🔄 Retesting API Gateway...")
        time.sleep(5)  # Wait for deployment
        api_ok = test_api_gateway()
    
    print("\n📋 Test Results:")
    print(f"✅ Lambda Function: {'Working' if lambda_ok else 'Failed'}")
    print(f"🌐 API Gateway: {'Working' if api_ok else 'Failed'}")
    
    if api_ok:
        print("\n🎉 API is ready! You can now:")
        print("1. Open test_enhanced_file_processing.html")
        print("2. Upload files and test processing")
        print("3. See Textract and Comprehend results")

if __name__ == "__main__":
    main()
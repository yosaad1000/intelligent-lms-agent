#!/usr/bin/env python3
"""
Quick test of the deployed Lambda function
"""

import boto3
import json
import time

def test_lambda_function():
    """Test the deployed Lambda function directly"""
    
    lambda_client = boto3.client('lambda')
    function_name = 'lms-enhanced-file-processing'
    
    # Test event
    test_event = {
        'httpMethod': 'GET',
        'path': '/files',
        'queryStringParameters': {
            'user_id': 'test-user-123'
        },
        'body': None,
        'headers': {
            'Content-Type': 'application/json'
        },
        'requestContext': {
            'requestId': 'test-request-123'
        }
    }
    
    print(f"🚀 Testing Lambda function: {function_name}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print("✅ Lambda function response:")
        print(json.dumps(payload, indent=2))
        
        # Check if function is working
        if response['StatusCode'] == 200:
            print("✅ Lambda function is working!")
            return True
        else:
            print(f"❌ Lambda function returned status: {response['StatusCode']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {str(e)}")
        return False

def get_api_url():
    """Get the API Gateway URL"""
    
    apigateway = boto3.client('apigateway')
    
    try:
        # Get API details
        apis = apigateway.get_rest_apis()
        
        for api in apis['items']:
            if api['name'] == 'lms-enhanced-file-api':
                api_id = api['id']
                region = boto3.Session().region_name or 'us-east-1'
                api_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod"
                
                print(f"🔗 API Gateway URL: {api_url}")
                return api_url
        
        print("❌ API Gateway not found")
        return None
        
    except Exception as e:
        print(f"❌ Error getting API URL: {str(e)}")
        return None

def main():
    """Main test function"""
    
    print("🚀 Quick Lambda Function Test")
    print("=" * 50)
    
    # Test Lambda function directly
    lambda_working = test_lambda_function()
    
    print("\n" + "=" * 50)
    
    # Get API URL
    api_url = get_api_url()
    
    print("\n📋 Summary:")
    print(f"✅ Lambda Function: {'Working' if lambda_working else 'Failed'}")
    print(f"🔗 API Gateway: {api_url if api_url else 'Not available'}")
    
    if api_url:
        print(f"\n🧪 Test the API with:")
        print(f"curl -X GET '{api_url}/files?user_id=test-user-123'")
    
    print("\n🎯 Next steps:")
    print("1. Use the test interface: test_enhanced_file_processing.html")
    print("2. Run integration tests: python test_textract_comprehend_integration.py")
    print("3. Upload files and test Textract/Comprehend processing")

if __name__ == "__main__":
    main()
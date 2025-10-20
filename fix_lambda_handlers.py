#!/usr/bin/env python3
"""
Fix Lambda function handlers and redeploy with correct structure
"""

import boto3
import zipfile
import os
import shutil
from pathlib import Path

def create_simple_lambda_package(handler_file, output_zip):
    """Create a simple Lambda package with correct structure"""
    
    print(f"📦 Creating package: {output_zip}")
    
    # Create temp directory
    temp_dir = Path("temp_lambda_fix")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # Copy the main handler file to root
        handler_path = Path(handler_file)
        if handler_path.exists():
            shutil.copy2(handler_path, temp_dir / handler_path.name)
            print(f"   Added: {handler_path.name}")
        
        # Copy shared directory if needed
        shared_dir = Path("src/shared")
        if shared_dir.exists():
            shutil.copytree(shared_dir, temp_dir / "shared")
            print(f"   Added: shared/")
        
        # Copy file_processing directory if needed for chat
        if "chat" in handler_file:
            fp_dir = Path("src/file_processing")
            if fp_dir.exists():
                shutil.copytree(fp_dir, temp_dir / "file_processing")
                print(f"   Added: file_processing/")
        
        # Create ZIP
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file() and not file_path.name.endswith('.pyc'):
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Package created: {output_zip}")
        return True
        
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def update_lambda_function(function_name, zip_file, handler):
    """Update Lambda function with correct handler"""
    
    lambda_client = boto3.client('lambda')
    
    print(f"🔄 Updating {function_name}...")
    
    try:
        # Update code
        with open(zip_file, 'rb') as f:
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=f.read()
            )
        
        # Update configuration with correct handler
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=handler,
            Timeout=60,
            MemorySize=512
        )
        
        print(f"✅ Updated {function_name} with handler {handler}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {function_name}: {e}")
        return False

def test_lambda_function(function_name, test_payload):
    """Test Lambda function directly"""
    
    lambda_client = boto3.client('lambda')
    
    print(f"🧪 Testing {function_name}...")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=test_payload
        )
        
        result = response['Payload'].read().decode()
        
        if response['StatusCode'] == 200:
            if 'errorMessage' in result:
                print(f"   ❌ Function error: {result}")
                return False
            else:
                print(f"   ✅ Function working: {result[:100]}...")
                return True
        else:
            print(f"   ❌ Invoke failed: {response['StatusCode']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Fix all Lambda functions"""
    
    print("🔧 Fixing Lambda Function Handlers")
    print("=" * 50)
    
    # Define functions to fix
    functions = [
        {
            'name': 'lms-health-function',
            'handler_file': 'src/health/health.py',
            'handler': 'health.lambda_handler',
            'zip': 'health-fixed.zip',
            'test_payload': '{}'
        },
        {
            'name': 'lms-chat-function', 
            'handler_file': 'src/chat/chat_handler.py',
            'handler': 'chat_handler.lambda_handler',
            'zip': 'chat-fixed.zip',
            'test_payload': '{"httpMethod": "POST", "path": "/api/chat", "body": "{\\"user_id\\": \\"test\\", \\"message\\": \\"hello\\"}"}'
        }
    ]
    
    success_count = 0
    
    for func in functions:
        print(f"\n📦 Processing {func['name']}...")
        
        # Create package
        if create_simple_lambda_package(func['handler_file'], func['zip']):
            # Update function
            if update_lambda_function(func['name'], func['zip'], func['handler']):
                # Test function
                if test_lambda_function(func['name'], func['test_payload']):
                    success_count += 1
        
        # Cleanup
        if os.path.exists(func['zip']):
            os.remove(func['zip'])
    
    print(f"\n🎯 Results: {success_count}/{len(functions)} functions fixed")
    
    if success_count > 0:
        print(f"\n🧪 Testing API endpoints...")
        test_api_endpoints()

def test_api_endpoints():
    """Test the API endpoints"""
    
    import requests
    
    api_url = "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test health
    try:
        response = requests.get(f"{api_url}/api/health", timeout=10)
        print(f"Health: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"Health test failed: {e}")
    
    # Test chat
    try:
        response = requests.post(
            f"{api_url}/api/chat",
            json={"user_id": "test", "message": "hello"},
            timeout=30
        )
        print(f"Chat: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"Chat test failed: {e}")

if __name__ == "__main__":
    main()
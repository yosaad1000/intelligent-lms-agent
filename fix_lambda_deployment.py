#!/usr/bin/env python3
"""
Fix Lambda deployment by creating proper packages with correct structure
"""

import boto3
import zipfile
import os
import tempfile
import shutil
from pathlib import Path

def create_lambda_package(source_files, handler_name, output_zip):
    """Create Lambda package with correct structure"""
    
    print(f"📦 Creating {output_zip}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy files to temp directory with correct structure
        for src_file in source_files:
            src_path = Path(src_file)
            if src_path.exists():
                if src_path.is_file():
                    # Copy file to root of package
                    dest_path = temp_path / src_path.name
                    shutil.copy2(src_path, dest_path)
                    print(f"   Added: {src_path.name}")
                elif src_path.is_dir():
                    # Copy directory
                    dest_path = temp_path / src_path.name
                    shutil.copytree(src_path, dest_path, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    print(f"   Added directory: {src_path.name}")
        
        # Create ZIP file
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file() and not file_path.name.endswith('.pyc'):
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
    
    print(f"✅ Created: {output_zip}")
    return output_zip

def update_lambda_function(function_name, zip_file, handler):
    """Update Lambda function"""
    
    lambda_client = boto3.client('lambda')
    
    print(f"🔄 Updating {function_name}...")
    
    try:
        with open(zip_file, 'rb') as f:
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=f.read()
            )
        
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=handler,
            Timeout=60,
            MemorySize=512
        )
        
        print(f"✅ Updated {function_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {function_name}: {e}")
        return False

def main():
    """Fix Lambda deployments"""
    
    print("🔧 Fixing Lambda Deployments")
    print("=" * 40)
    
    # Health function
    print("\n1. Health Function")
    health_zip = create_lambda_package(
        ['src/health/health.py', 'src/shared'],
        'health.lambda_handler',
        'health.zip'
    )
    
    update_lambda_function('lms-health-function', health_zip, 'health.lambda_handler')
    os.remove(health_zip)
    
    # Chat function  
    print("\n2. Chat Function")
    chat_zip = create_lambda_package(
        ['src/chat/chat_handler.py', 'src/shared', 'src/file_processing'],
        'chat_handler.lambda_handler', 
        'chat.zip'
    )
    
    update_lambda_function('lms-chat-function', chat_zip, 'chat_handler.lambda_handler')
    os.remove(chat_zip)
    
    # File function
    print("\n3. File Function")
    file_zip = create_lambda_package(
        ['src/file_processing/file_handler.py', 'src/file_processing/text_extractor.py', 'src/file_processing/vector_storage.py', 'src/shared'],
        'file_handler.lambda_handler',
        'file.zip'
    )
    
    update_lambda_function('lms-file-function', file_zip, 'file_handler.lambda_handler')
    os.remove(file_zip)
    
    print(f"\n🎉 Lambda functions updated!")
    
    # Test the API
    print(f"\n🧪 Testing API...")
    import time
    time.sleep(10)  # Wait for deployment
    
    import requests
    
    api_url = "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test health
    try:
        response = requests.get(f"{api_url}/api/health", timeout=10)
        print(f"Health: {response.status_code}")
    except Exception as e:
        print(f"Health test failed: {e}")
    
    # Test chat
    try:
        response = requests.post(
            f"{api_url}/api/chat",
            json={"user_id": "test", "message": "hello"},
            timeout=30
        )
        print(f"Chat: {response.status_code}")
        if response.status_code != 502:
            print("✅ Chat endpoint working!")
    except Exception as e:
        print(f"Chat test failed: {e}")

if __name__ == "__main__":
    main()
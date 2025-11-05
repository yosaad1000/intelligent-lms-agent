#!/usr/bin/env python3
"""
Fix Lambda dependencies by installing required packages
"""

import boto3
import zipfile
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def install_dependencies(temp_dir):
    """Install required dependencies"""
    
    print("📦 Installing dependencies...")
    
    # Create requirements.txt for Lambda
    requirements = """
python-dotenv==1.0.0
boto3
botocore
pinecone-client
"""
    
    req_file = Path(temp_dir) / "requirements.txt"
    with open(req_file, 'w') as f:
        f.write(requirements.strip())
    
    # Install dependencies
    try:
        subprocess.run([
            'pip', 'install', '-r', str(req_file), '-t', temp_dir
        ], check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_working_lambda_package(source_files, output_zip):
    """Create Lambda package with dependencies"""
    
    print(f"📦 Creating {output_zip}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Install dependencies first
        if not install_dependencies(temp_dir):
            return None
        
        # Copy source files
        for src_file in source_files:
            src_path = Path(src_file)
            if src_path.exists():
                if src_path.is_file():
                    dest_path = temp_path / src_path.name
                    shutil.copy2(src_path, dest_path)
                    print(f"   Added: {src_path.name}")
                elif src_path.is_dir():
                    dest_path = temp_path / src_path.name
                    shutil.copytree(src_path, dest_path, 
                                  ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
                                  dirs_exist_ok=True)
                    print(f"   Added directory: {src_path.name}")
        
        # Create ZIP file
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file() and not file_path.name.endswith('.pyc'):
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Created: {output_zip}")
        return output_zip

def update_lambda_with_dependencies(function_name, zip_file, handler):
    """Update Lambda function with dependencies"""
    
    lambda_client = boto3.client('lambda')
    
    print(f"🔄 Updating {function_name}...")
    
    try:
        # Update code
        with open(zip_file, 'rb') as f:
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=f.read()
            )
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=handler,
            Timeout=60,
            MemorySize=512,
            Runtime='python3.11'
        )
        
        print(f"✅ Updated {function_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {function_name}: {e}")
        return False

def main():
    """Fix Lambda functions with proper dependencies"""
    
    print("🔧 Fixing Lambda Dependencies")
    print("=" * 40)
    
    # Only fix the chat function for now since health is working
    print("\n📦 Fixing Chat Function...")
    
    chat_zip = create_working_lambda_package(
        ['src/chat/chat_handler.py', 'src/shared', 'src/file_processing'],
        'chat-with-deps.zip'
    )
    
    if chat_zip:
        success = update_lambda_with_dependencies(
            'lms-chat-function', 
            chat_zip, 
            'chat_handler.lambda_handler'
        )
        
        os.remove(chat_zip)
        
        if success:
            print(f"\n⏳ Waiting for deployment...")
            import time
            time.sleep(15)
            
            print(f"\n🧪 Testing fixed function...")
            
            # Test Lambda directly
            lambda_client = boto3.client('lambda')
            try:
                response = lambda_client.invoke(
                    FunctionName='lms-chat-function',
                    Payload='{"httpMethod": "POST", "path": "/api/chat", "body": "{\\"user_id\\": \\"test\\", \\"message\\": \\"hello\\"}"}'
                )
                
                result = response['Payload'].read().decode()
                print(f"Lambda test: {result[:100]}...")
                
                if 'errorMessage' not in result:
                    print("✅ Lambda function working!")
                    
                    # Test API Gateway
                    import requests
                    api_url = "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod"
                    
                    try:
                        response = requests.post(
                            f"{api_url}/api/chat",
                            json={"user_id": "test", "message": "hello"},
                            timeout=30
                        )
                        print(f"API Gateway test: {response.status_code}")
                        
                        if response.status_code == 200:
                            print("🎉 API Gateway working!")
                            print("✅ Your web interface should now work!")
                        else:
                            print(f"API response: {response.text[:100]}")
                    except Exception as e:
                        print(f"API test failed: {e}")
                else:
                    print(f"❌ Lambda still has errors: {result}")
                    
            except Exception as e:
                print(f"Lambda test failed: {e}")

if __name__ == "__main__":
    main()
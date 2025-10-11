#!/usr/bin/env python3
"""
Update Lambda function code
"""

import boto3
import zipfile
import os
import shutil

def update_lambda_functions():
    """Update Lambda functions with fixed code"""
    print("🔄 Updating Lambda function code...")
    
    lambda_client = boto3.client('lambda')
    
    # Create deployment package
    package_dir = "lambda_package_update"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy updated source files
    shutil.copy("src/hello_world.py", package_dir)
    shutil.copy("src/auth.py", package_dir)
    
    # Create zip file
    zip_file = "lambda_update.zip"
    if os.path.exists(zip_file):
        os.remove(zip_file)
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    # Update Lambda functions
    functions = ['lms-hello-world', 'lms-auth']
    
    for function_name in functions:
        print(f"📦 Updating {function_name}...")
        
        try:
            with open(zip_file, 'rb') as f:
                zip_content = f.read()
            
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            print(f"✅ {function_name} updated successfully")
            
        except Exception as e:
            print(f"❌ Failed to update {function_name}: {e}")
    
    # Clean up
    shutil.rmtree(package_dir)
    os.remove(zip_file)
    
    print("✅ All Lambda functions updated")

if __name__ == "__main__":
    update_lambda_functions()
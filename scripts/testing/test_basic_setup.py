#!/usr/bin/env python3
"""
Test basic setup without problematic imports
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_setup():
    """Test basic setup"""
    
    print("🧪 Testing Basic Setup")
    print("=" * 50)
    
    # Test environment variables
    required_vars = [
        'PINECONE_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_ANON_KEY'
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 20}...{value[-4:]}")
        else:
            print(f"❌ {var}: Missing")
            all_good = False
    
    # Test imports
    print("\n📦 Testing Package Imports")
    print("=" * 50)
    
    try:
        import boto3
        print("✅ boto3")
    except ImportError:
        print("❌ boto3")
        all_good = False
    
    try:
        import pinecone
        print("✅ pinecone")
    except ImportError:
        print("❌ pinecone")
        all_good = False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv")
        all_good = False
    
    try:
        import fastapi
        print("✅ fastapi")
    except ImportError:
        print("❌ fastapi")
        all_good = False
    
    # Test AWS CLI
    print("\n🔧 Testing AWS CLI")
    print("=" * 50)
    
    try:
        import subprocess
        result = subprocess.run("aws sts get-caller-identity", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AWS CLI configured")
        else:
            print("❌ AWS CLI not configured")
            all_good = False
    except:
        print("❌ AWS CLI test failed")
        all_good = False
    
    return all_good

if __name__ == "__main__":
    if test_basic_setup():
        print("\n✅ Basic setup complete!")
        print("\n🚀 Ready to start implementation!")
        print("\n📋 Next Steps:")
        print("1. Start Task 1: Serverless Project Setup")
        print("2. Create AWS SAM template")
        print("3. Implement Lambda functions")
    else:
        print("\n❌ Some issues found. Please fix them before proceeding.")
#!/usr/bin/env python3
"""
Deployment script for LMS API Backend
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr}")
        return False

def deploy_sam_application():
    """Deploy SAM application"""
    
    print("🚀 Deploying LMS API Backend")
    print("=" * 50)
    
    # Get environment variables
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not all([pinecone_api_key, supabase_url, supabase_anon_key]):
        print("❌ Missing required environment variables")
        print("   Please check your .env file")
        return False
    
    # Build SAM application
    if not run_command("sam build", "Building SAM application"):
        return False
    
    # Deploy with parameters
    deploy_command = f"""sam deploy --guided --parameter-overrides ParameterKey=PineconeApiKey,ParameterValue="{pinecone_api_key}" ParameterKey=SupabaseUrl,ParameterValue="{supabase_url}" ParameterKey=SupabaseAnonKey,ParameterValue="{supabase_anon_key}" """
    
    print("🔄 Deploying to AWS...")
    print("   This will prompt you for deployment configuration")
    
    # Run deployment interactively
    try:
        subprocess.run(deploy_command, shell=True, check=True)
        print("✅ Deployment completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        return False

def test_deployment():
    """Test the deployed API"""
    
    print("\n🧪 Testing Deployed API")
    print("=" * 50)
    
    # Get API URL from SAM outputs
    try:
        result = subprocess.run(
            "sam list stack-outputs --stack-name lms-api-backend --output json",
            shell=True, capture_output=True, text=True, check=True
        )
        
        import json
        outputs = json.loads(result.stdout)
        
        api_url = None
        for output in outputs:
            if output['OutputKey'] == 'LMSApiUrl':
                api_url = output['OutputValue']
                break
        
        if api_url:
            print(f"✅ API URL: {api_url}")
            
            # Test health endpoint
            health_url = f"{api_url}/api/health"
            print(f"🔄 Testing health endpoint: {health_url}")
            
            import requests
            response = requests.get(health_url)
            
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False

def main():
    """Main deployment function"""
    
    # Check prerequisites
    print("🔍 Checking Prerequisites")
    print("=" * 50)
    
    # Check SAM CLI
    try:
        subprocess.run("sam --version", shell=True, check=True, capture_output=True)
        print("✅ SAM CLI available")
    except:
        print("❌ SAM CLI not found. Please install it first.")
        return
    
    # Check AWS CLI
    try:
        subprocess.run("aws sts get-caller-identity", shell=True, check=True, capture_output=True)
        print("✅ AWS CLI configured")
    except:
        print("❌ AWS CLI not configured. Please configure it first.")
        return
    
    # Deploy application
    if deploy_sam_application():
        print("\n🎉 Deployment Summary")
        print("=" * 50)
        print("✅ LMS API Backend deployed successfully!")
        print("\n📋 Next Steps:")
        print("1. Test the API endpoints with your React frontend")
        print("2. Continue with Task 2: Lambda Authentication")
        print("3. Implement RAG processing in Task 5")
        
        # Test deployment
        test_deployment()
    else:
        print("\n❌ Deployment failed. Please check the errors above.")

if __name__ == "__main__":
    main()
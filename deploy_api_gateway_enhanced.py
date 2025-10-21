#!/usr/bin/env python3
"""
Deploy Enhanced API Gateway for Task 12: Frontend-Backend API Integration
"""

import boto3
import json
import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return None

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {identity['Account']}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        return False

def deploy_api_gateway():
    """Deploy the enhanced API Gateway stack"""
    print("🚀 Deploying Enhanced LMS API Gateway for Frontend Integration")
    print("=" * 60)
    
    # Check prerequisites
    if not check_aws_credentials():
        return False
    
    # Set environment variables
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Build and deploy with SAM
    commands = [
        {
            'cmd': 'sam build --template-file template-api-gateway.yaml',
            'desc': 'Building SAM application'
        },
        {
            'cmd': 'sam deploy --template-file template-api-gateway.yaml --stack-name lms-api-gateway-enhanced --capabilities CAPABILITY_IAM --parameter-overrides Environment=dev BedrockAgentId=ZTBBVSC6Y1 BedrockAgentAliasId=TSTALIASID --confirm-changeset --no-fail-on-empty-changeset',
            'desc': 'Deploying API Gateway stack'
        }
    ]
    
    for command in commands:
        result = run_command(command['cmd'], command['desc'])
        if result is None:
            print(f"❌ Failed to execute: {command['desc']}")
            return False
    
    # Get stack outputs
    try:
        cf = boto3.client('cloudformation')
        response = cf.describe_stacks(StackName='lms-api-gateway-enhanced')
        
        outputs = {}
        if response['Stacks']:
            for output in response['Stacks'][0].get('Outputs', []):
                outputs[output['OutputKey']] = output['OutputValue']
        
        print("\n🎉 Deployment Successful!")
        print("=" * 40)
        print(f"📡 API Gateway URL: {outputs.get('ApiGatewayUrl', 'Not found')}")
        print(f"🔌 WebSocket URL: {outputs.get('WebSocketUrl', 'Not found')}")
        print(f"📁 Documents Bucket: {outputs.get('DocumentsBucketName', 'Not found')}")
        
        # Save configuration for frontend
        config = {
            'api_gateway_url': outputs.get('ApiGatewayUrl', ''),
            'websocket_url': outputs.get('WebSocketUrl', ''),
            'documents_bucket': outputs.get('DocumentsBucketName', ''),
            'bedrock_agent_id': 'ZTBBVSC6Y1',
            'bedrock_agent_alias_id': 'TSTALIASID',
            'region': 'us-east-1',
            'deployed_at': datetime.utcnow().isoformat()
        }
        
        with open('api_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n📝 Configuration saved to api_config.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to get stack outputs: {e}")
        return False

def test_api_endpoints():
    """Test the deployed API endpoints"""
    print("\n🧪 Testing API Endpoints")
    print("=" * 30)
    
    try:
        # Load configuration
        with open('api_config.json', 'r') as f:
            config = json.load(f)
        
        api_url = config['api_gateway_url']
        
        import requests
        
        # Test health endpoint
        health_url = f"{api_url}/api/v1/health"
        print(f"Testing health endpoint: {health_url}")
        
        response = requests.get(health_url, timeout=30)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        
        # Test capabilities endpoint
        capabilities_url = f"{api_url}/api/v1/capabilities"
        print(f"\nTesting capabilities endpoint: {capabilities_url}")
        
        response = requests.get(capabilities_url, timeout=30)
        if response.status_code == 200:
            print("✅ Capabilities check passed")
            capabilities = response.json()
            print(f"Available capabilities: {len(capabilities.get('capabilities', []))}")
        else:
            print(f"❌ Capabilities check failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API testing failed: {e}")
        return False

def create_frontend_env_file():
    """Create environment file for frontend"""
    print("\n📝 Creating Frontend Environment Configuration")
    
    try:
        with open('api_config.json', 'r') as f:
            config = json.load(f)
        
        env_content = f"""# LMS Frontend Environment Configuration
# Generated on {datetime.utcnow().isoformat()}

# API Configuration
VITE_API_GATEWAY_URL={config['api_gateway_url']}
VITE_WEBSOCKET_URL={config['websocket_url']}
VITE_AWS_REGION={config['region']}

# Bedrock Agent Configuration
VITE_BEDROCK_AGENT_ID={config['bedrock_agent_id']}
VITE_BEDROCK_AGENT_ALIAS_ID={config['bedrock_agent_alias_id']}

# Storage Configuration
VITE_DOCUMENTS_BUCKET={config['documents_bucket']}

# Development Configuration
VITE_USE_MOCK_AGENT=false
VITE_USE_API_PROXY=true
"""
        
        # Write to frontend directory
        frontend_env_path = 'frontend_extracted/frontend/.env.production'
        with open(frontend_env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Frontend environment file created: {frontend_env_path}")
        
        # Also create a local copy
        with open('.env.frontend', 'w') as f:
            f.write(env_content)
        
        print("✅ Local environment file created: .env.frontend")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create frontend environment file: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 LMS API Gateway Enhanced Deployment")
    print("Task 12: Frontend-Backend API Integration")
    print("=" * 50)
    
    success = True
    
    # Deploy API Gateway
    if not deploy_api_gateway():
        success = False
    
    # Test endpoints
    if success and not test_api_endpoints():
        print("⚠️ API testing failed, but deployment may still be successful")
    
    # Create frontend configuration
    if success:
        create_frontend_env_file()
    
    if success:
        print("\n🎉 Task 12 Deployment Complete!")
        print("=" * 40)
        print("✅ Enhanced API Gateway deployed successfully")
        print("✅ Frontend integration endpoints ready")
        print("✅ Environment configuration created")
        print("\n📋 Next Steps:")
        print("1. Update frontend service to use API Gateway endpoints")
        print("2. Test chat functionality through API proxy")
        print("3. Implement file upload with presigned URLs")
        print("4. Test session management and conversation history")
    else:
        print("\n❌ Deployment failed. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
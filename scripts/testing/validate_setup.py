#!/usr/bin/env python3
"""
Validate the serverless setup without SAM build
"""

import os
import yaml
import json
from pathlib import Path

def validate_template():
    """Validate SAM template structure"""
    
    print("🧪 Validating SAM Template")
    print("=" * 50)
    
    try:
        # Read template-simple.yaml
        with open('template-simple.yaml', 'r') as f:
            template = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['AWSTemplateFormatVersion', 'Transform', 'Resources']
        for section in required_sections:
            if section not in template:
                print(f"❌ Missing section: {section}")
                return False
            else:
                print(f"✅ Found section: {section}")
        
        # Check Lambda functions
        resources = template['Resources']
        lambda_functions = [name for name, resource in resources.items() 
                          if resource.get('Type') == 'AWS::Serverless::Function']
        
        print(f"✅ Found {len(lambda_functions)} Lambda functions:")
        for func in lambda_functions:
            print(f"   - {func}")
        
        # Check DynamoDB tables
        dynamodb_tables = [name for name, resource in resources.items() 
                          if resource.get('Type') == 'AWS::DynamoDB::Table']
        
        print(f"✅ Found {len(dynamodb_tables)} DynamoDB tables:")
        for table in dynamodb_tables:
            print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template validation failed: {e}")
        return False

def validate_lambda_code():
    """Validate Lambda function code structure"""
    
    print("\n🧪 Validating Lambda Code Structure")
    print("=" * 50)
    
    lambda_dirs = [
        'src/auth',
        'src/health', 
        'src/file_processing',
        'src/chat'
    ]
    
    all_good = True
    
    for lambda_dir in lambda_dirs:
        if Path(lambda_dir).exists():
            print(f"✅ Directory exists: {lambda_dir}")
            
            # Check for handler file
            handler_files = list(Path(lambda_dir).glob('*.py'))
            if handler_files:
                print(f"   - Found Python files: {[f.name for f in handler_files]}")
            else:
                print(f"   ❌ No Python files found")
                all_good = False
                
            # Check for requirements.txt
            req_file = Path(lambda_dir) / 'requirements.txt'
            if req_file.exists():
                print(f"   - Found requirements.txt")
            else:
                print(f"   ❌ Missing requirements.txt")
                all_good = False
        else:
            print(f"❌ Directory missing: {lambda_dir}")
            all_good = False
    
    return all_good

def validate_environment():
    """Validate environment configuration"""
    
    print("\n🧪 Validating Environment Configuration")
    print("=" * 50)
    
    required_env_vars = [
        'PINECONE_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    all_good = True
    
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 20}...{value[-4:]}")
        else:
            print(f"❌ {var}: Missing")
            all_good = False
    
    return all_good

def create_deployment_summary():
    """Create deployment summary"""
    
    print("\n📋 Deployment Summary")
    print("=" * 50)
    
    summary = {
        "project_name": "LMS API Backend",
        "architecture": "Serverless Lambda Functions",
        "services": {
            "api_gateway": "REST API with CORS",
            "lambda_functions": [
                "AuthorizerFunction - JWT validation",
                "HealthFunction - Health checks", 
                "FileProcessingFunction - File uploads",
                "ChatFunction - AI chat with RAG"
            ],
            "dynamodb_tables": [
                "lms-user-files - File metadata",
                "lms-chat-conversations - Chat conversations",
                "lms-chat-messages - Chat messages"
            ],
            "s3_bucket": "lms-documents - File storage"
        },
        "integrations": {
            "pinecone": "Vector database for RAG",
            "supabase": "Authentication and existing data",
            "bedrock": "AI agents and embeddings"
        }
    }
    
    print(json.dumps(summary, indent=2))
    
    return summary

def main():
    """Main validation function"""
    
    print("🚀 Validating LMS API Backend Setup")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run validations
    template_ok = validate_template()
    code_ok = validate_lambda_code()
    env_ok = validate_environment()
    
    if all([template_ok, code_ok, env_ok]):
        print("\n✅ All validations passed!")
        
        # Create summary
        create_deployment_summary()
        
        print("\n🎉 Task 1 Complete!")
        print("=" * 50)
        print("✅ Serverless project setup complete")
        print("✅ AWS SAM template configured")
        print("✅ Lambda functions structured")
        print("✅ DynamoDB tables defined")
        print("✅ Environment variables configured")
        
        print("\n📋 Next Steps:")
        print("1. Deploy to AWS: sam deploy --guided")
        print("2. Test API endpoints")
        print("3. Continue with Task 2: Lambda Authentication")
        
        return True
    else:
        print("\n❌ Some validations failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    main()
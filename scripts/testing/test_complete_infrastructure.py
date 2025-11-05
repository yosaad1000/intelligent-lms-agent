#!/usr/bin/env python3
"""
Complete Infrastructure Test Script

This script tests all infrastructure components for the file processor microservice:
- S3 bucket setup and configuration
- DynamoDB table setup and operations
- Bedrock Knowledge Base setup (partial in demo environment)
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from file_processor.s3_setup import S3BucketSetup
from file_processor.dynamodb_setup import DynamoDBSetup
from file_processor.bedrock_kb_setup import BedrockKnowledgeBaseSetup
from shared.config import config

def test_complete_infrastructure():
    """Test complete infrastructure setup"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 COMPLETE FILE PROCESSOR INFRASTRUCTURE TEST")
    print("=" * 70)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    missing_config = config.validate_config()
    if missing_config:
        print(f"❌ Missing configuration: {', '.join(missing_config)}")
        print("Please set up your .env file with AWS credentials")
        return False
    else:
        print("✅ Configuration is complete")
    
    print(f"📦 S3 Bucket: {config.S3_BUCKET_NAME}")
    print(f"🗄️  DynamoDB Table: {config.FILE_METADATA_TABLE}")
    print(f"🌍 Region: {config.AWS_DEFAULT_REGION}")
    
    # Track overall results
    overall_results = {
        's3_success': False,
        'dynamodb_success': False,
        'bedrock_partial': False,
        'errors': []
    }
    
    # Test 1: S3 Infrastructure
    print("\n" + "="*70)
    print("🗂️  TESTING S3 INFRASTRUCTURE")
    print("="*70)
    
    try:
        s3_setup = S3BucketSetup()
        s3_results = s3_setup.setup_complete_s3_infrastructure()
        
        s3_success = all([
            s3_results['bucket_created'],
            s3_results['policies_configured'],
            s3_results['folders_created'],
            s3_results['lifecycle_configured']
        ]) and all(s3_results['tests_passed'].values())
        
        overall_results['s3_success'] = s3_success
        
        if s3_success:
            print("✅ S3 Infrastructure: FULLY OPERATIONAL")
        else:
            print("❌ S3 Infrastructure: FAILED")
            overall_results['errors'].extend(s3_results['errors'])
            
    except Exception as e:
        print(f"❌ S3 Infrastructure: EXCEPTION - {e}")
        overall_results['errors'].append(f"S3 Exception: {e}")
    
    # Test 2: DynamoDB Infrastructure
    print("\n" + "="*70)
    print("🗃️  TESTING DYNAMODB INFRASTRUCTURE")
    print("="*70)
    
    try:
        dynamodb_setup = DynamoDBSetup()
        dynamodb_results = dynamodb_setup.setup_complete_dynamodb_infrastructure()
        
        dynamodb_success = all([
            dynamodb_results['table_created'],
            dynamodb_results['backup_configured'],
            dynamodb_results['sample_data_created']
        ]) and all(dynamodb_results['tests_passed'].values())
        
        overall_results['dynamodb_success'] = dynamodb_success
        
        if dynamodb_success:
            print("✅ DynamoDB Infrastructure: FULLY OPERATIONAL")
        else:
            print("❌ DynamoDB Infrastructure: FAILED")
            overall_results['errors'].extend(dynamodb_results['errors'])
            
    except Exception as e:
        print(f"❌ DynamoDB Infrastructure: EXCEPTION - {e}")
        overall_results['errors'].append(f"DynamoDB Exception: {e}")
    
    # Test 3: Bedrock Knowledge Base Infrastructure
    print("\n" + "="*70)
    print("🧠 TESTING BEDROCK KNOWLEDGE BASE INFRASTRUCTURE")
    print("="*70)
    
    try:
        kb_setup = BedrockKnowledgeBaseSetup()
        kb_results = kb_setup.setup_complete_bedrock_infrastructure()
        
        # For Bedrock, we consider partial success acceptable in demo environment
        bedrock_partial = kb_results['iam_role_created']
        overall_results['bedrock_partial'] = bedrock_partial
        
        if bedrock_partial:
            print("⚠️  Bedrock Infrastructure: PARTIAL SUCCESS (Expected in demo)")
            if kb_results['knowledge_base_id']:
                print(f"📋 Knowledge Base ID: {kb_results['knowledge_base_id']}")
        else:
            print("❌ Bedrock Infrastructure: FAILED")
            overall_results['errors'].extend(kb_results['errors'])
            
    except Exception as e:
        print(f"❌ Bedrock Infrastructure: EXCEPTION - {e}")
        overall_results['errors'].append(f"Bedrock Exception: {e}")
    
    # Final Results Summary
    print("\n" + "="*70)
    print("📊 FINAL INFRASTRUCTURE STATUS")
    print("="*70)
    
    print(f"✅ S3 Infrastructure: {'OPERATIONAL' if overall_results['s3_success'] else 'FAILED'}")
    print(f"✅ DynamoDB Infrastructure: {'OPERATIONAL' if overall_results['dynamodb_success'] else 'FAILED'}")
    print(f"⚠️  Bedrock Infrastructure: {'PARTIAL' if overall_results['bedrock_partial'] else 'FAILED'}")
    
    # Critical components check
    critical_success = overall_results['s3_success'] and overall_results['dynamodb_success']
    
    if critical_success:
        print("\n🎉 INFRASTRUCTURE READY FOR FILE PROCESSING!")
        print("✅ All critical components are operational")
        print("✅ File upload and metadata management ready")
        print("⚠️  Knowledge Base requires manual OpenSearch setup for full functionality")
        
        print("\n📝 NEXT STEPS:")
        print("1. ✅ S3 bucket ready for file uploads")
        print("2. ✅ DynamoDB ready for metadata storage")
        print("3. ⚠️  Manual OpenSearch Serverless setup needed for Knowledge Base")
        print("4. 🚀 Ready to implement file upload and processing logic")
        
        return True
    else:
        print("\n❌ CRITICAL INFRASTRUCTURE COMPONENTS FAILED")
        print("Cannot proceed with file processing implementation")
        
        if overall_results['errors']:
            print("\n🔍 Error Details:")
            for error in overall_results['errors']:
                print(f"  • {error}")
        
        return False

if __name__ == "__main__":
    success = test_complete_infrastructure()
    sys.exit(0 if success else 1)
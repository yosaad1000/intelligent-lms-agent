#!/usr/bin/env python3
"""
Test script for Bedrock Knowledge Base setup

This script tests the Bedrock Knowledge Base infrastructure setup for the file processor microservice.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from file_processor.bedrock_kb_setup import BedrockKnowledgeBaseSetup
from shared.config import config

def test_bedrock_kb_setup():
    """Test Bedrock Knowledge Base setup functionality"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 Testing Bedrock Knowledge Base Infrastructure Setup")
    print("=" * 60)
    
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
    print(f"🌍 Region: {config.AWS_DEFAULT_REGION}")
    
    # Initialize Bedrock KB setup
    try:
        kb_setup = BedrockKnowledgeBaseSetup()
        print("✅ Bedrock Knowledge Base client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Bedrock client: {e}")
        return False
    
    # Run complete setup
    print("\n🚀 Running Bedrock Knowledge Base Infrastructure Setup...")
    print("⚠️  Note: This may take several minutes...")
    
    results = kb_setup.setup_complete_bedrock_infrastructure()
    
    # Display results
    print("\n📊 Setup Results:")
    print("-" * 40)
    
    setup_items = [
        ("IAM Role Created", results['iam_role_created']),
        ("OpenSearch Collection", results['opensearch_collection_created']),
        ("Knowledge Base Created", results['knowledge_base_created']),
        ("Data Source Created", results['data_source_created'])
    ]
    
    for item, success in setup_items:
        status = "✅" if success else "❌"
        print(f"{status} {item}")
    
    # Display IDs if available
    if results['knowledge_base_id']:
        print(f"\n📋 Knowledge Base ID: {results['knowledge_base_id']}")
    
    if results['data_source_id']:
        print(f"📋 Data Source ID: {results['data_source_id']}")
    
    # Display test results
    print("\n🧪 Operation Test Results:")
    print("-" * 40)
    
    test_results = results['tests_passed']
    for test_name, passed in test_results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    # Display errors if any
    if results['errors']:
        print("\n❌ Errors Encountered:")
        print("-" * 40)
        for error in results['errors']:
            print(f"  • {error}")
    
    # Overall success check
    critical_components = [
        results['iam_role_created'],
        results['knowledge_base_created']
    ]
    
    all_tests_success = all(test_results.values()) if test_results else True
    
    print("\n" + "=" * 60)
    if all(critical_components) and all_tests_success:
        print("🎉 Bedrock Knowledge Base Setup: SUCCESSFUL")
        print("✅ Critical components configured and tested")
        
        # Update .env with Knowledge Base ID if created
        if results['knowledge_base_id']:
            print(f"\n💡 Add this to your .env file:")
            print(f"KNOWLEDGE_BASE_ID={results['knowledge_base_id']}")
        
        return True
    else:
        print("⚠️  Bedrock Knowledge Base Setup: PARTIAL SUCCESS")
        if not all(critical_components):
            print("❌ Some critical components failed")
        if not all_tests_success:
            print("❌ Some operation tests failed")
        
        print("\n💡 Note: Some failures are expected in demo environments")
        print("   - OpenSearch Serverless requires manual setup")
        print("   - IAM permissions may be limited")
        
        return False

if __name__ == "__main__":
    success = test_bedrock_kb_setup()
    sys.exit(0 if success else 1)
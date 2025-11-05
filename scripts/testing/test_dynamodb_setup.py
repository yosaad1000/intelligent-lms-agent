#!/usr/bin/env python3
"""
Test script for DynamoDB setup

This script tests the DynamoDB infrastructure setup for the file processor microservice.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from file_processor.dynamodb_setup import DynamoDBSetup
from shared.config import config

def test_dynamodb_setup():
    """Test DynamoDB setup functionality"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 Testing DynamoDB Infrastructure Setup")
    print("=" * 50)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    missing_config = config.validate_config()
    if missing_config:
        print(f"❌ Missing configuration: {', '.join(missing_config)}")
        print("Please set up your .env file with AWS credentials")
        return False
    else:
        print("✅ Configuration is complete")
    
    print(f"📦 Table Name: {config.FILE_METADATA_TABLE}")
    print(f"🌍 Region: {config.AWS_DEFAULT_REGION}")
    
    # Initialize DynamoDB setup
    try:
        dynamodb_setup = DynamoDBSetup()
        print("✅ DynamoDB client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize DynamoDB client: {e}")
        return False
    
    # Run complete setup
    print("\n🚀 Running DynamoDB Infrastructure Setup...")
    results = dynamodb_setup.setup_complete_dynamodb_infrastructure()
    
    # Display results
    print("\n📊 Setup Results:")
    print("-" * 30)
    
    setup_items = [
        ("Table Created", results['table_created']),
        ("Backup Configured", results['backup_configured']),
        ("Sample Data Created", results['sample_data_created'])
    ]
    
    for item, success in setup_items:
        status = "✅" if success else "❌"
        print(f"{status} {item}")
    
    # Display test results
    print("\n🧪 CRUD Test Results:")
    print("-" * 30)
    
    test_results = results['tests_passed']
    for test_name, passed in test_results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name.upper()} Test")
    
    # Display errors if any
    if results['errors']:
        print("\n❌ Errors Encountered:")
        print("-" * 30)
        for error in results['errors']:
            print(f"  • {error}")
    
    # Overall success check
    all_setup_success = all([
        results['table_created'],
        results['backup_configured'],
        results['sample_data_created']
    ])
    
    all_tests_success = all(test_results.values())
    
    print("\n" + "=" * 50)
    if all_setup_success and all_tests_success:
        print("🎉 DynamoDB Infrastructure Setup: SUCCESSFUL")
        print("✅ All components configured and tested")
        return True
    else:
        print("⚠️  DynamoDB Infrastructure Setup: PARTIAL SUCCESS")
        if not all_setup_success:
            print("❌ Some setup components failed")
        if not all_tests_success:
            print("❌ Some CRUD tests failed")
        return False

if __name__ == "__main__":
    success = test_dynamodb_setup()
    sys.exit(0 if success else 1)
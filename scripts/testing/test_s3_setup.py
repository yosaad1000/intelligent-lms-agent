#!/usr/bin/env python3
"""
Test script for S3 bucket setup

This script tests the S3 infrastructure setup for the file processor microservice.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from file_processor.s3_setup import S3BucketSetup
from shared.config import config

def test_s3_setup():
    """Test S3 setup functionality"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 Testing S3 Infrastructure Setup")
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
    
    print(f"📦 Bucket Name: {config.S3_BUCKET_NAME}")
    print(f"🌍 Region: {config.AWS_DEFAULT_REGION}")
    
    # Initialize S3 setup
    try:
        s3_setup = S3BucketSetup()
        print("✅ S3 client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize S3 client: {e}")
        return False
    
    # Run complete setup
    print("\n🚀 Running S3 Infrastructure Setup...")
    results = s3_setup.setup_complete_s3_infrastructure()
    
    # Display results
    print("\n📊 Setup Results:")
    print("-" * 30)
    
    setup_items = [
        ("Bucket Created", results['bucket_created']),
        ("Policies Configured", results['policies_configured']),
        ("Folders Created", results['folders_created']),
        ("Lifecycle Configured", results['lifecycle_configured'])
    ]
    
    for item, success in setup_items:
        status = "✅" if success else "❌"
        print(f"{status} {item}")
    
    # Display test results
    print("\n🧪 Operation Tests:")
    print("-" * 30)
    
    test_results = results['tests_passed']
    for test_name, passed in test_results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name.capitalize()} Test")
    
    # Display errors if any
    if results['errors']:
        print("\n❌ Errors Encountered:")
        print("-" * 30)
        for error in results['errors']:
            print(f"  • {error}")
    
    # Overall success check
    all_setup_success = all([
        results['bucket_created'],
        results['policies_configured'],
        results['folders_created'],
        results['lifecycle_configured']
    ])
    
    all_tests_success = all(test_results.values())
    
    print("\n" + "=" * 50)
    if all_setup_success and all_tests_success:
        print("🎉 S3 Infrastructure Setup: SUCCESSFUL")
        print("✅ All components configured and tested")
        return True
    else:
        print("⚠️  S3 Infrastructure Setup: PARTIAL SUCCESS")
        if not all_setup_success:
            print("❌ Some setup components failed")
        if not all_tests_success:
            print("❌ Some operation tests failed")
        return False

if __name__ == "__main__":
    success = test_s3_setup()
    sys.exit(0 if success else 1)
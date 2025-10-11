"""
S3 Bucket Setup and Configuration for File Processor Microservice

This module handles the creation and configuration of S3 bucket structure
for the LMS file processing system.
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from src.shared.config import config

logger = logging.getLogger(__name__)

class S3BucketSetup:
    """Handles S3 bucket setup and configuration for file processing"""
    
    def __init__(self):
        """Initialize S3 client with configuration"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            self.bucket_name = config.S3_BUCKET_NAME or "lms-files-bucket"
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def create_bucket_if_not_exists(self) -> bool:
        """Create S3 bucket if it doesn't exist"""
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if config.AWS_DEFAULT_REGION == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': config.AWS_DEFAULT_REGION
                            }
                        )
                    logger.info(f"Created bucket: {self.bucket_name}")
                    return True
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    return False
            else:
                logger.error(f"Error checking bucket: {e}")
                return False
    
    def setup_bucket_policies(self) -> bool:
        """Configure bucket policies and CORS"""
        try:
            # Set up CORS configuration
            cors_configuration = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                        'AllowedOrigins': ['*'],
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3000
                    }
                ]
            }
            
            self.s3_client.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration=cors_configuration
            )
            logger.info("CORS configuration applied successfully")
            
            # Set up bucket policy for secure access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowAuthenticatedAccess",
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{self._get_account_id()}:root"},
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:DeleteObject"
                        ],
                        "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                    },
                    {
                        "Sid": "AllowListBucket",
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{self._get_account_id()}:root"},
                        "Action": "s3:ListBucket",
                        "Resource": f"arn:aws:s3:::{self.bucket_name}"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            logger.info("Bucket policy applied successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to set bucket policies: {e}")
            return False
    
    def create_folder_structure(self) -> bool:
        """Create the folder structure for organized file storage"""
        try:
            # Define folder structure
            folders = [
                "users/",
                "shared/sample_documents/",
                "temp/uploads/",
                "processed/knowledge_base/"
            ]
            
            # Create folders by uploading empty objects with trailing slash
            for folder in folders:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder,
                    Body=b''
                )
                logger.info(f"Created folder: {folder}")
            
            # Create a sample user folder structure
            sample_user_folders = [
                "users/demo_user/raw/",
                "users/demo_user/processed/",
                "users/demo_user/metadata/"
            ]
            
            for folder in sample_user_folders:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder,
                    Body=b''
                )
                logger.info(f"Created sample user folder: {folder}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create folder structure: {e}")
            return False
    
    def setup_lifecycle_policies(self) -> bool:
        """Set up lifecycle policies for cost optimization"""
        try:
            lifecycle_configuration = {
                'Rules': [
                    {
                        'ID': 'TempFilesCleanup',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'temp/'},
                        'Expiration': {'Days': 1}
                    },
                    {
                        'ID': 'ProcessedFilesTransition',
                        'Status': 'Enabled',
                        'Filter': {'Prefix': 'users/'},
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            },
                            {
                                'Days': 90,
                                'StorageClass': 'GLACIER'
                            }
                        ]
                    }
                ]
            }
            
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_configuration
            )
            logger.info("Lifecycle policies configured successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to set lifecycle policies: {e}")
            return False
    
    def test_bucket_operations(self) -> Dict[str, bool]:
        """Test basic bucket operations"""
        test_results = {
            'upload': False,
            'download': False,
            'delete': False,
            'list': False
        }
        
        test_key = "test/test_file.txt"
        test_content = b"This is a test file for S3 operations"
        
        try:
            # Test upload
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=test_content
            )
            test_results['upload'] = True
            logger.info("Upload test passed")
            
            # Test download
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            downloaded_content = response['Body'].read()
            if downloaded_content == test_content:
                test_results['download'] = True
                logger.info("Download test passed")
            
            # Test list
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="test/"
            )
            if 'Contents' in response and len(response['Contents']) > 0:
                test_results['list'] = True
                logger.info("List test passed")
            
            # Test delete
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            test_results['delete'] = True
            logger.info("Delete test passed")
            
        except ClientError as e:
            logger.error(f"Bucket operation test failed: {e}")
        
        return test_results
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            return sts_client.get_caller_identity()['Account']
        except Exception as e:
            logger.error(f"Failed to get account ID: {e}")
            return "unknown"
    
    def setup_complete_s3_infrastructure(self) -> Dict[str, Any]:
        """Complete S3 infrastructure setup"""
        results = {
            'bucket_created': False,
            'policies_configured': False,
            'folders_created': False,
            'lifecycle_configured': False,
            'tests_passed': {},
            'errors': []
        }
        
        try:
            # Step 1: Create bucket
            if self.create_bucket_if_not_exists():
                results['bucket_created'] = True
            else:
                results['errors'].append("Failed to create bucket")
            
            # Step 2: Configure policies
            if self.setup_bucket_policies():
                results['policies_configured'] = True
            else:
                results['errors'].append("Failed to configure policies")
            
            # Step 3: Create folder structure
            if self.create_folder_structure():
                results['folders_created'] = True
            else:
                results['errors'].append("Failed to create folders")
            
            # Step 4: Set up lifecycle policies
            if self.setup_lifecycle_policies():
                results['lifecycle_configured'] = True
            else:
                results['errors'].append("Failed to configure lifecycle")
            
            # Step 5: Test operations
            results['tests_passed'] = self.test_bucket_operations()
            
            logger.info("S3 infrastructure setup completed")
            
        except Exception as e:
            logger.error(f"S3 infrastructure setup failed: {e}")
            results['errors'].append(str(e))
        
        return results

def main():
    """Main function to run S3 setup"""
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Setting up S3 infrastructure for File Processor...")
    
    s3_setup = S3BucketSetup()
    results = s3_setup.setup_complete_s3_infrastructure()
    
    print("\n📊 Setup Results:")
    print(f"✅ Bucket Created: {results['bucket_created']}")
    print(f"✅ Policies Configured: {results['policies_configured']}")
    print(f"✅ Folders Created: {results['folders_created']}")
    print(f"✅ Lifecycle Configured: {results['lifecycle_configured']}")
    
    print("\n🧪 Test Results:")
    for test, passed in results['tests_passed'].items():
        status = "✅" if passed else "❌"
        print(f"{status} {test.capitalize()}: {passed}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print("\n🎉 S3 infrastructure setup completed successfully!")

if __name__ == "__main__":
    main()
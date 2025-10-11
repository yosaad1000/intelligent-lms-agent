"""
DynamoDB Setup and Configuration for File Processor Microservice

This module handles the creation and configuration of DynamoDB tables
for file metadata management in the LMS system.
"""

import boto3
import logging
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
from src.shared.config import config

logger = logging.getLogger(__name__)

class DynamoDBSetup:
    """Handles DynamoDB table setup and configuration for file metadata"""
    
    def __init__(self):
        """Initialize DynamoDB client with configuration"""
        try:
            self.dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            self.dynamodb_client = boto3.client(
                'dynamodb',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            self.table_name = config.FILE_METADATA_TABLE
            logger.info(f"DynamoDB client initialized for table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB client: {e}")
            raise
    
    def create_file_metadata_table(self) -> bool:
        """Create the file metadata table with proper schema"""
        try:
            # Check if table already exists
            existing_tables = self.dynamodb_client.list_tables()['TableNames']
            if self.table_name in existing_tables:
                logger.info(f"Table {self.table_name} already exists")
                return True
            
            # Create table with optimized schema for file metadata
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'file_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'file_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'upload_timestamp',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'processing_status',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'user-id-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'upload_timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'status-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'processing_status',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'upload_timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            logger.info(f"Created table: {self.table_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table: {e}")
            return False
    
    def configure_backup_and_recovery(self) -> bool:
        """Configure backup and point-in-time recovery"""
        try:
            # Enable point-in-time recovery
            self.dynamodb_client.update_continuous_backups(
                TableName=self.table_name,
                PointInTimeRecoverySpecification={
                    'PointInTimeRecoveryEnabled': True
                }
            )
            logger.info("Point-in-time recovery enabled")
            
            # Note: Automatic backups are enabled by default in DynamoDB
            # We could also set up scheduled backups here if needed
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to configure backup: {e}")
            return False
    
    def test_crud_operations(self) -> Dict[str, bool]:
        """Test CRUD operations on the metadata table"""
        test_results = {
            'create': False,
            'read': False,
            'update': False,
            'delete': False,
            'query': False
        }
        
        table = self.dynamodb.Table(self.table_name)
        test_file_id = "test-file-123"
        test_user_id = "test-user-456"
        
        try:
            # Test CREATE
            test_item = {
                'file_id': test_file_id,
                'user_id': test_user_id,
                'original_filename': 'test_document.pdf',
                's3_key': f'users/{test_user_id}/raw/test_document.pdf',
                'file_size': 1024,
                'file_type': 'application/pdf',
                'upload_timestamp': '2024-10-11T19:00:00Z',
                'processing_status': 'uploaded',
                'text_extraction_status': 'pending',
                'kb_indexing_status': 'pending'
            }
            
            table.put_item(Item=test_item)
            test_results['create'] = True
            logger.info("CREATE test passed")
            
            # Test READ
            response = table.get_item(Key={'file_id': test_file_id})
            if 'Item' in response and response['Item']['user_id'] == test_user_id:
                test_results['read'] = True
                logger.info("READ test passed")
            
            # Test UPDATE
            table.update_item(
                Key={'file_id': test_file_id},
                UpdateExpression='SET processing_status = :status',
                ExpressionAttributeValues={':status': 'processing'}
            )
            
            # Verify update
            response = table.get_item(Key={'file_id': test_file_id})
            if response['Item']['processing_status'] == 'processing':
                test_results['update'] = True
                logger.info("UPDATE test passed")
            
            # Test QUERY (using GSI)
            response = table.query(
                IndexName='user-id-index',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': test_user_id}
            )
            
            if response['Items'] and len(response['Items']) > 0:
                test_results['query'] = True
                logger.info("QUERY test passed")
            
            # Test DELETE
            table.delete_item(Key={'file_id': test_file_id})
            
            # Verify deletion
            response = table.get_item(Key={'file_id': test_file_id})
            if 'Item' not in response:
                test_results['delete'] = True
                logger.info("DELETE test passed")
            
        except ClientError as e:
            logger.error(f"CRUD operation test failed: {e}")
        
        return test_results
    
    def create_sample_data(self) -> bool:
        """Create sample data for testing"""
        try:
            table = self.dynamodb.Table(self.table_name)
            
            sample_files = [
                {
                    'file_id': 'demo-file-001',
                    'user_id': 'demo_user',
                    'original_filename': 'physics_notes.pdf',
                    's3_key': 'users/demo_user/raw/physics_notes.pdf',
                    'file_size': 2048576,
                    'file_type': 'application/pdf',
                    'upload_timestamp': '2024-10-11T18:00:00Z',
                    'processing_status': 'completed',
                    'text_extraction_status': 'success',
                    'kb_indexing_status': 'indexed',
                    'content_preview': 'Physics notes covering thermodynamics and mechanics...',
                    'extracted_concepts': ['thermodynamics', 'mechanics', 'energy']
                },
                {
                    'file_id': 'demo-file-002',
                    'user_id': 'demo_user',
                    'original_filename': 'math_formulas.docx',
                    's3_key': 'users/demo_user/raw/math_formulas.docx',
                    'file_size': 512000,
                    'file_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'upload_timestamp': '2024-10-11T18:30:00Z',
                    'processing_status': 'completed',
                    'text_extraction_status': 'success',
                    'kb_indexing_status': 'indexed',
                    'content_preview': 'Mathematical formulas for calculus and algebra...',
                    'extracted_concepts': ['calculus', 'algebra', 'derivatives']
                }
            ]
            
            for item in sample_files:
                table.put_item(Item=item)
            
            logger.info(f"Created {len(sample_files)} sample file records")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create sample data: {e}")
            return False
    
    def setup_complete_dynamodb_infrastructure(self) -> Dict[str, Any]:
        """Complete DynamoDB infrastructure setup"""
        results = {
            'table_created': False,
            'backup_configured': False,
            'tests_passed': {},
            'sample_data_created': False,
            'errors': []
        }
        
        try:
            # Step 1: Create table
            if self.create_file_metadata_table():
                results['table_created'] = True
            else:
                results['errors'].append("Failed to create table")
            
            # Step 2: Configure backup and recovery
            if self.configure_backup_and_recovery():
                results['backup_configured'] = True
            else:
                results['errors'].append("Failed to configure backup")
            
            # Step 3: Test CRUD operations
            results['tests_passed'] = self.test_crud_operations()
            
            # Step 4: Create sample data
            if self.create_sample_data():
                results['sample_data_created'] = True
            else:
                results['errors'].append("Failed to create sample data")
            
            logger.info("DynamoDB infrastructure setup completed")
            
        except Exception as e:
            logger.error(f"DynamoDB infrastructure setup failed: {e}")
            results['errors'].append(str(e))
        
        return results

def main():
    """Main function to run DynamoDB setup"""
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Setting up DynamoDB infrastructure for File Processor...")
    
    dynamodb_setup = DynamoDBSetup()
    results = dynamodb_setup.setup_complete_dynamodb_infrastructure()
    
    print("\n📊 Setup Results:")
    print(f"✅ Table Created: {results['table_created']}")
    print(f"✅ Backup Configured: {results['backup_configured']}")
    print(f"✅ Sample Data Created: {results['sample_data_created']}")
    
    print("\n🧪 CRUD Test Results:")
    for test, passed in results['tests_passed'].items():
        status = "✅" if passed else "❌"
        print(f"{status} {test.upper()}: {passed}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print("\n🎉 DynamoDB infrastructure setup completed successfully!")

if __name__ == "__main__":
    main()
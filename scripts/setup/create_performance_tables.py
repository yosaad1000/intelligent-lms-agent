#!/usr/bin/env python3
"""
Create Performance Optimization DynamoDB Tables
Creates tables for caching, metrics, and async task management
"""

import boto3
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTableCreator:
    """Create DynamoDB tables for performance optimization"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.region = 'us-east-1'
    
    def create_all_tables(self):
        """Create all performance-related tables"""
        
        print("🚀 Creating Performance Optimization DynamoDB Tables")
        print("=" * 50)
        
        tables_created = []
        
        try:
            # Create performance cache table
            if self.create_performance_cache_table():
                tables_created.append('lms-performance-cache')
            
            # Create performance metrics table
            if self.create_performance_metrics_table():
                tables_created.append('lms-performance-metrics')
            
            # Create async tasks table
            if self.create_async_tasks_table():
                tables_created.append('lms-async-tasks')
            
            # Create background queue table (for SQS alternative)
            if self.create_background_queue_table():
                tables_created.append('lms-background-queue')
            
            print(f"\n✅ Successfully created {len(tables_created)} performance tables:")
            for table in tables_created:
                print(f"  - {table}")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance table creation failed: {e}")
            return False
    
    def create_performance_cache_table(self):
        """Create performance cache table"""
        
        table_name = 'lms-performance-cache'
        
        try:
            # Check if table exists
            try:
                table = self.dynamodb.Table(table_name)
                table.load()
                print(f"✅ Table {table_name} already exists")
                return True
            except:
                pass
            
            # Create table
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'cache_key',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'cache_key',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Performance'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Response Caching'
                    }
                ]
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            
            # Enable TTL after table creation
            try:
                dynamodb_client = boto3.client('dynamodb')
                dynamodb_client.update_time_to_live(
                    TableName=table_name,
                    TimeToLiveSpecification={
                        'AttributeName': 'ttl',
                        'Enabled': True
                    }
                )
                print(f"✅ TTL enabled for {table_name}")
            except Exception as ttl_error:
                print(f"⚠️ TTL configuration failed for {table_name}: {ttl_error}")
            
            # Wait for table to be created
            table.wait_until_exists()
            print(f"✅ Created table: {table_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create {table_name}: {e}")
            return False
    
    def create_performance_metrics_table(self):
        """Create performance metrics table"""
        
        table_name = 'lms-performance-metrics'
        
        try:
            # Check if table exists
            try:
                table = self.dynamodb.Table(table_name)
                table.load()
                print(f"✅ Table {table_name} already exists")
                return True
            except:
                pass
            
            # Create table
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'request_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'request_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'endpoint',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'endpoint-timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'endpoint',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'user-timestamp-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                },
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Performance'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Performance Metrics'
                    }
                ]
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            print(f"✅ Created table: {table_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create {table_name}: {e}")
            return False
    
    def create_async_tasks_table(self):
        """Create async tasks table"""
        
        table_name = 'lms-async-tasks'
        
        try:
            # Check if table exists
            try:
                table = self.dynamodb.Table(table_name)
                table.load()
                print(f"✅ Table {table_name} already exists")
                return True
            except:
                pass
            
            # Create table
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'task_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'task_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'created_at',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'status',
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
                                'AttributeName': 'created_at',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'user-status-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'status',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                },
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Performance'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Async Task Management'
                    }
                ]
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            print(f"✅ Created table: {table_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create {table_name}: {e}")
            return False
    
    def create_background_queue_table(self):
        """Create background queue table (alternative to SQS)"""
        
        table_name = 'lms-background-queue'
        
        try:
            # Check if table exists
            try:
                table = self.dynamodb.Table(table_name)
                table.load()
                print(f"✅ Table {table_name} already exists")
                return True
            except:
                pass
            
            # Create table
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'message_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'message_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'task_type',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'scheduled_time',
                        'AttributeType': 'N'
                    },
                    {
                        'AttributeName': 'status',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'task-type-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'task_type',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'scheduled_time',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    },
                    {
                        'IndexName': 'status-scheduled-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'status',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'scheduled_time',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                },
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Performance'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Background Task Queue'
                    }
                ]
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            print(f"✅ Created table: {table_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create {table_name}: {e}")
            return False
    
    def verify_tables(self):
        """Verify all performance tables are created and accessible"""
        
        print("\n🔍 Verifying Performance Tables")
        print("=" * 30)
        
        tables_to_check = [
            'lms-performance-cache',
            'lms-performance-metrics',
            'lms-async-tasks',
            'lms-background-queue'
        ]
        
        verified_tables = []
        
        for table_name in tables_to_check:
            try:
                table = self.dynamodb.Table(table_name)
                table.load()
                
                # Get table status
                status = table.table_status
                item_count = table.item_count
                
                # Check TTL configuration
                ttl_status = "Enabled" if hasattr(table, 'time_to_live_description') else "Not configured"
                
                print(f"✅ {table_name}: {status} ({item_count} items, TTL: {ttl_status})")
                verified_tables.append(table_name)
                
            except Exception as e:
                print(f"❌ {table_name}: Not accessible - {e}")
        
        print(f"\n📊 Performance Tables Summary:")
        print(f"  Total tables: {len(tables_to_check)}")
        print(f"  Verified: {len(verified_tables)}")
        print(f"  Failed: {len(tables_to_check) - len(verified_tables)}")
        
        return len(verified_tables) == len(tables_to_check)
    
    def create_sample_data(self):
        """Create sample data for testing performance features"""
        
        print("\n📝 Creating Sample Performance Data")
        print("=" * 35)
        
        try:
            # Sample cache data
            cache_table = self.dynamodb.Table('lms-performance-cache')
            cache_table.put_item(
                Item={
                    'cache_key': 'test_cache_key',
                    'value': json.dumps({'message': 'Test cache value', 'timestamp': datetime.utcnow().isoformat()}),
                    'ttl': int(datetime.utcnow().timestamp()) + 3600,  # 1 hour TTL
                    'created_at': datetime.utcnow().isoformat()
                }
            )
            print("✅ Created sample cache data")
            
            # Sample metrics data
            metrics_table = self.dynamodb.Table('lms-performance-metrics')
            metrics_table.put_item(
                Item={
                    'request_id': 'test_req_123',
                    'timestamp': datetime.utcnow().isoformat(),
                    'endpoint': '/api/test',
                    'method': 'POST',
                    'user_id': 'test_user',
                    'duration_ms': 150.5,
                    'status_code': 200,
                    'response_size': 1024,
                    'memory_usage_mb': 128.0,
                    'cpu_usage_percent': 25.5,
                    'db_queries': 2,
                    'cache_hits': 1,
                    'cache_misses': 0,
                    'aws_service_calls': 1,
                    'error_count': 0,
                    'ttl': int(datetime.utcnow().timestamp()) + (30 * 24 * 3600)  # 30 days TTL
                }
            )
            print("✅ Created sample metrics data")
            
            # Sample async task data
            tasks_table = self.dynamodb.Table('lms-async-tasks')
            tasks_table.put_item(
                Item={
                    'task_id': 'test_task_456',
                    'task_type': 'file_processing',
                    'user_id': 'test_user',
                    'status': 'completed',
                    'created_at': datetime.utcnow().isoformat(),
                    'started_at': datetime.utcnow().isoformat(),
                    'completed_at': datetime.utcnow().isoformat(),
                    'progress': 100.0,
                    'result': json.dumps({'processed_files': 1, 'success': True}),
                    'ttl': int(datetime.utcnow().timestamp()) + (7 * 24 * 3600)  # 7 days TTL
                }
            )
            print("✅ Created sample async task data")
            
            # Sample background queue data
            queue_table = self.dynamodb.Table('lms-background-queue')
            queue_table.put_item(
                Item={
                    'message_id': 'test_msg_789',
                    'task_type': 'cache_warming',
                    'user_id': 'test_user',
                    'status': 'pending',
                    'scheduled_time': int(datetime.utcnow().timestamp()),
                    'task_data': json.dumps({'cache_types': ['user_files', 'chat_history']}),
                    'created_at': datetime.utcnow().isoformat(),
                    'retry_count': 0,
                    'ttl': int(datetime.utcnow().timestamp()) + (24 * 3600)  # 24 hours TTL
                }
            )
            print("✅ Created sample background queue data")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create sample data: {e}")
            return False


def main():
    """Main performance table creation"""
    
    creator = PerformanceTableCreator()
    
    # Create tables
    success = creator.create_all_tables()
    
    if success:
        # Verify tables
        verification_success = creator.verify_tables()
        
        if verification_success:
            # Create sample data
            sample_success = creator.create_sample_data()
            
            print(f"\n🎉 Performance Optimization Tables Ready!")
            print(f"✅ All tables created and verified")
            print(f"✅ Sample data created: {sample_success}")
            print(f"\n📋 Available Performance Features:")
            print(f"  - Multi-tier response caching (Memory + DynamoDB + Redis)")
            print(f"  - Connection pooling for AWS services")
            print(f"  - Async task processing and tracking")
            print(f"  - Background task queue management")
            print(f"  - Comprehensive performance monitoring")
            print(f"  - Load testing and metrics collection")
            
        else:
            print(f"\n⚠️ Some tables may not be fully ready. Check AWS Console.")
        
        return verification_success
    else:
        print(f"\n❌ Performance Table Creation Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
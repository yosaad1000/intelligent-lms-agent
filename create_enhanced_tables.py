#!/usr/bin/env python3
"""
Create Enhanced DynamoDB Tables
Creates tables for quiz storage, translations, and analytics
"""

import boto3
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTableCreator:
    """Create DynamoDB tables for enhanced functionality"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.region = 'us-east-1'
    
    def create_all_tables(self):
        """Create all required tables"""
        
        print("🗄️ Creating Enhanced DynamoDB Tables")
        print("=" * 40)
        
        tables_created = []
        
        try:
            # Create quiz tables
            if self.create_quizzes_table():
                tables_created.append('lms-quizzes')
            
            if self.create_quiz_submissions_table():
                tables_created.append('lms-quiz-submissions')
            
            # Create translation table
            if self.create_translations_table():
                tables_created.append('lms-translations')
            
            # Create analytics table
            if self.create_analytics_table():
                tables_created.append('lms-analytics')
            
            # Create chat history table (if not exists)
            if self.create_chat_history_table():
                tables_created.append('lms-chat-history')
            
            print(f"\n✅ Successfully created {len(tables_created)} tables:")
            for table in tables_created:
                print(f"  - {table}")
            
            return True
            
        except Exception as e:
            print(f"❌ Table creation failed: {e}")
            return False
    
    def create_quizzes_table(self):
        """Create quizzes table"""
        
        table_name = 'lms-quizzes'
        
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
                        'AttributeName': 'quiz_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'quiz_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'created_at',
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
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Enhanced'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Quiz Storage'
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
    
    def create_quiz_submissions_table(self):
        """Create quiz submissions table"""
        
        table_name = 'lms-quiz-submissions'
        
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
                        'AttributeName': 'submission_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'submission_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'quiz_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'submitted_at',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'quiz-id-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'quiz_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'submitted_at',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'user-id-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'user_id',
                                'KeyType': 'HASH'
                            },
                            {
                                'AttributeName': 'submitted_at',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Enhanced'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Quiz Submissions'
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
    
    def create_translations_table(self):
        """Create translations table"""
        
        table_name = 'lms-translations'
        
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
                        'AttributeName': 'translation_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'translation_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'created_at',
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
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Enhanced'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Translation History'
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
    
    def create_analytics_table(self):
        """Create learning analytics table"""
        
        table_name = 'lms-analytics'
        
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
                        'AttributeName': 'analytics_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'analytics_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'last_updated',
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
                                'AttributeName': 'last_updated',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Enhanced'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Learning Analytics'
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
    
    def create_chat_history_table(self):
        """Create chat history table"""
        
        table_name = 'lms-chat-history'
        
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
                        'AttributeName': 'session_id',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'KeyType': 'RANGE'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'session_id',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'timestamp',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'user_id',
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
                                'AttributeName': 'timestamp',
                                'KeyType': 'RANGE'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'LMS-Enhanced'
                    },
                    {
                        'Key': 'Purpose',
                        'Value': 'Chat History'
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
        """Verify all tables are created and accessible"""
        
        print("\n🔍 Verifying Tables")
        print("=" * 20)
        
        tables_to_check = [
            'lms-quizzes',
            'lms-quiz-submissions', 
            'lms-translations',
            'lms-analytics',
            'lms-chat-history'
        ]
        
        verified_tables = []
        
        for table_name in tables_to_check:
            try:
                table = self.dynamodb.Table(table_name)
                table.load()
                
                # Get table status
                status = table.table_status
                item_count = table.item_count
                
                print(f"✅ {table_name}: {status} ({item_count} items)")
                verified_tables.append(table_name)
                
            except Exception as e:
                print(f"❌ {table_name}: Not accessible - {e}")
        
        print(f"\n📊 Verification Summary:")
        print(f"  Total tables: {len(tables_to_check)}")
        print(f"  Verified: {len(verified_tables)}")
        print(f"  Failed: {len(tables_to_check) - len(verified_tables)}")
        
        return len(verified_tables) == len(tables_to_check)


def main():
    """Main table creation"""
    
    creator = EnhancedTableCreator()
    
    # Create tables
    success = creator.create_all_tables()
    
    if success:
        # Verify tables
        verification_success = creator.verify_tables()
        
        if verification_success:
            print(f"\n🎉 All Enhanced Tables Created Successfully!")
            print(f"Ready for enhanced agent deployment.")
        else:
            print(f"\n⚠️ Some tables may not be fully ready. Check AWS Console.")
        
        return verification_success
    else:
        print(f"\n❌ Table Creation Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
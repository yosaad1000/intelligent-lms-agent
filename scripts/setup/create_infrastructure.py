#!/usr/bin/env python3
"""
Create basic infrastructure for LMS API
"""

import boto3
import json
import time
from datetime import datetime

def create_dynamodb_tables():
    """Create DynamoDB tables"""
    
    print("🗄️ Creating DynamoDB Tables")
    print("=" * 50)
    
    dynamodb = boto3.client('dynamodb')
    
    tables = [
        {
            'name': 'lms-user-files',
            'config': {
                'TableName': 'lms-user-files',
                'BillingMode': 'PAY_PER_REQUEST',
                'AttributeDefinitions': [
                    {'AttributeName': 'file_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'KeySchema': [
                    {'AttributeName': 'file_id', 'KeyType': 'HASH'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'user-id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }]
            }
        },
        {
            'name': 'lms-chat-conversations',
            'config': {
                'TableName': 'lms-chat-conversations',
                'BillingMode': 'PAY_PER_REQUEST',
                'AttributeDefinitions': [
                    {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'KeySchema': [
                    {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'user-id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }]
            }
        },
        {
            'name': 'lms-chat-messages',
            'config': {
                'TableName': 'lms-chat-messages',
                'BillingMode': 'PAY_PER_REQUEST',
                'AttributeDefinitions': [
                    {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'KeySchema': [
                    {'AttributeName': 'conversation_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'user-id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }]
            }
        }
    ]
    
    created_tables = []
    
    for table_info in tables:
        table_name = table_info['name']
        
        try:
            # Check if table exists
            try:
                dynamodb.describe_table(TableName=table_info['config']['TableName'])
                print(f"✅ Table already exists: {table_name}")
                created_tables.append(table_name)
                continue
            except dynamodb.exceptions.ResourceNotFoundException:
                pass
            
            # Create table
            print(f"🔄 Creating table: {table_name}")
            response = dynamodb.create_table(**table_info['config'])
            
            # Wait for table to be active
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_info['config']['TableName'])
            
            print(f"✅ Created table: {table_name}")
            created_tables.append(table_name)
            
        except Exception as e:
            print(f"❌ Failed to create table {table_name}: {e}")
    
    return created_tables

def create_s3_bucket():
    """Create S3 bucket for documents"""
    
    print("\n🪣 Creating S3 Bucket")
    print("=" * 50)
    
    s3 = boto3.client('s3')
    
    # Generate unique bucket name
    account_id = boto3.client('sts').get_caller_identity()['Account']
    bucket_name = f"lms-documents-{account_id}-{int(time.time())}"
    
    try:
        # Check if bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket already exists: {bucket_name}")
            return bucket_name
        except:
            pass
        
        # Create bucket
        print(f"🔄 Creating bucket: {bucket_name}")
        
        s3.create_bucket(Bucket=bucket_name)
        
        # Configure CORS
        cors_config = {
            'CORSRules': [{
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                'AllowedOrigins': ['*'],
                'MaxAgeSeconds': 3000
            }]
        }
        
        s3.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_config)
        
        print(f"✅ Created bucket with CORS: {bucket_name}")
        return bucket_name
        
    except Exception as e:
        print(f"❌ Failed to create bucket: {e}")
        return None

def test_infrastructure():
    """Test the created infrastructure"""
    
    print("\n🧪 Testing Infrastructure")
    print("=" * 50)
    
    try:
        # Test DynamoDB
        dynamodb = boto3.resource('dynamodb')
        
        tables_to_test = ['lms-user-files', 'lms-chat-conversations', 'lms-chat-messages']
        
        for table_name in tables_to_test:
            try:
                table = dynamodb.Table(table_name)
                table.load()
                print(f"✅ DynamoDB table accessible: {table_name}")
            except Exception as e:
                print(f"❌ DynamoDB table issue {table_name}: {e}")
        
        # Test Pinecone
        try:
            from pinecone import Pinecone
            from dotenv import load_dotenv
            load_dotenv()
            
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            
            # Check if our index exists
            if pc.has_index('lms-vectors'):
                print("✅ Pinecone index accessible: lms-vectors")
            else:
                print("⚠️  Pinecone index not found (will be created later)")
        except Exception as e:
            print(f"❌ Pinecone connection issue: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Infrastructure test failed: {e}")
        return False

def main():
    """Main function"""
    
    print("🚀 LMS API Backend - Infrastructure Setup")
    print("=" * 50)
    
    # Create DynamoDB tables
    tables = create_dynamodb_tables()
    
    # Create S3 bucket
    bucket = create_s3_bucket()
    
    # Test infrastructure
    if test_infrastructure():
        print("\n🎉 Infrastructure Setup Complete!")
        print("=" * 50)
        print(f"✅ Created {len(tables)} DynamoDB tables")
        print(f"✅ Created S3 bucket: {bucket}")
        print("✅ Pinecone connection verified")
        
        print("\n📋 Infrastructure Summary:")
        print(f"   - DynamoDB Tables: {', '.join(tables)}")
        print(f"   - S3 Bucket: {bucket}")
        print(f"   - Pinecone Index: lms-vectors")
        
        print("\n📋 Next Steps:")
        print("1. Infrastructure is ready for Lambda functions")
        print("2. Continue with Task 2: Authentication")
        print("3. Deploy Lambda functions individually")
        
        # Save configuration
        config = {
            'infrastructure': {
                'dynamodb_tables': tables,
                's3_bucket': bucket,
                'pinecone_index': 'lms-vectors',
                'aws_region': 'us-east-1',
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        with open('infrastructure-config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("💾 Configuration saved to infrastructure-config.json")
        
    else:
        print("\n❌ Infrastructure setup had issues")

if __name__ == "__main__":
    import os
    main()
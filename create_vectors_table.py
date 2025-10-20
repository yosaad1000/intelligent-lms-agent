#!/usr/bin/env python3
"""
Create the vectors table for RAG
"""

import boto3

def create_vectors_table():
    """Create DynamoDB table for document vectors"""
    
    print("📊 Creating vectors table...")
    
    dynamodb = boto3.resource('dynamodb')
    
    try:
        table = dynamodb.create_table(
            TableName='lms-document-vectors',
            KeySchema=[
                {'AttributeName': 'vector_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'vector_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user-id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print("✅ Table creation initiated")
        
        # Wait for table to be ready
        print("⏳ Waiting for table to be ready...")
        table.wait_until_exists()
        
        print("✅ Vectors table ready!")
        
        # Add test data
        print("📝 Adding test vectors...")
        
        test_vectors = [
            {
                'vector_id': 'test_ml_chunk_1',
                'user_id': 'test-user',
                'file_id': 'test-ml-file',
                'filename': 'ml-basics.txt',
                'chunk_index': 0,
                'chunk_text': 'Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.',
                'chunk_hash': 'hash1',
                'created_at': '2025-10-19T19:00:00Z'
            },
            {
                'vector_id': 'test_ml_chunk_2',
                'user_id': 'test-user', 
                'file_id': 'test-ml-file',
                'filename': 'ml-basics.txt',
                'chunk_index': 1,
                'chunk_text': 'There are three main types of machine learning: supervised learning uses labeled training data for classification and regression, unsupervised learning finds hidden patterns in unlabeled data, and reinforcement learning learns through rewards and penalties.',
                'chunk_hash': 'hash2',
                'created_at': '2025-10-19T19:00:00Z'
            },
            {
                'vector_id': 'test_ml_chunk_3',
                'user_id': 'test-user',
                'file_id': 'test-ml-file', 
                'filename': 'ml-basics.txt',
                'chunk_index': 2,
                'chunk_text': 'Machine learning applications include image recognition, natural language processing, recommendation systems, autonomous vehicles, medical diagnosis, and financial fraud detection.',
                'chunk_hash': 'hash3',
                'created_at': '2025-10-19T19:00:00Z'
            }
        ]
        
        for vector in test_vectors:
            table.put_item(Item=vector)
        
        print(f"✅ Added {len(test_vectors)} test vectors")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    create_vectors_table()
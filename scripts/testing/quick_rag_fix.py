#!/usr/bin/env python3
"""
Quick fix to enable RAG functionality
"""

import boto3
import json

def test_and_fix_rag():
    """Test current system and apply quick fixes"""
    
    print("🔧 Quick RAG Fix")
    print("=" * 30)
    
    # Test what we have
    print("\n1. Testing current file upload...")
    
    import requests
    
    api_url = "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod"
    
    # Upload test document
    upload_data = {
        "user_id": "test-user",
        "filename": "ml-basics.txt", 
        "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. There are three main types of machine learning: supervised learning uses labeled training data for classification and regression, unsupervised learning finds hidden patterns in unlabeled data through clustering and dimensionality reduction, and reinforcement learning learns optimal actions through trial and error with rewards and penalties."
    }
    
    try:
        response = requests.post(f"{api_url}/api/files", json=upload_data, timeout=30)
        print(f"Upload status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ File processed: {data}")
        else:
            print(f"❌ Upload failed: {response.text}")
            
    except Exception as e:
        print(f"Upload error: {e}")
    
    # Check DynamoDB for stored vectors
    print("\n2. Checking stored data...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        
        # Check if vectors table exists
        try:
            vectors_table = dynamodb.Table('lms-document-vectors')
            response = vectors_table.scan(Limit=5)
            items = response.get('Items', [])
            print(f"✅ Found {len(items)} vectors in database")
            
            if items:
                print(f"Sample vector: {items[0].get('chunk_text', '')[:100]}...")
            
        except Exception as e:
            print(f"⚠️  Vectors table issue: {e}")
        
        # Check files table
        try:
            files_table = dynamodb.Table('lms-user-files')
            response = files_table.scan(Limit=5)
            items = response.get('Items', [])
            print(f"✅ Found {len(items)} files in database")
            
        except Exception as e:
            print(f"⚠️  Files table issue: {e}")
            
    except Exception as e:
        print(f"Database check error: {e}")
    
    # Test chat with uploaded content
    print("\n3. Testing RAG chat...")
    
    chat_data = {
        "user_id": "test-user",
        "message": "What is machine learning according to my documents?"
    }
    
    try:
        response = requests.post(f"{api_url}/api/chat", json=chat_data, timeout=30)
        print(f"Chat status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"RAG Enhanced: {data.get('rag_enhanced', False)}")
            print(f"Documents Used: {data.get('rag_documents_used', 0)}")
            print(f"Response: {data.get('response', '')[:150]}...")
            
            if data.get('citations'):
                print(f"Citations: {data.get('citations')}")
        else:
            print(f"❌ Chat failed: {response.text}")
            
    except Exception as e:
        print(f"Chat error: {e}")
    
    # Manual DynamoDB vector creation for testing
    print("\n4. Creating test vectors manually...")
    
    try:
        dynamodb = boto3.resource('dynamodb')
        
        # Create vectors table if it doesn't exist
        try:
            vectors_table = dynamodb.create_table(
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
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            print("✅ Created vectors table")
            
            # Wait for table to be ready
            import time
            time.sleep(10)
            
        except Exception as e:
            print(f"Table creation: {e}")
            vectors_table = dynamodb.Table('lms-document-vectors')
        
        # Add test vectors
        test_vectors = [
            {
                'vector_id': 'test_chunk_1',
                'user_id': 'test-user',
                'file_id': 'test-file-1',
                'filename': 'ml-basics.txt',
                'chunk_index': 0,
                'chunk_text': 'Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.',
                'chunk_hash': 'hash1',
                'created_at': '2025-10-19T19:00:00Z'
            },
            {
                'vector_id': 'test_chunk_2', 
                'user_id': 'test-user',
                'file_id': 'test-file-1',
                'filename': 'ml-basics.txt',
                'chunk_index': 1,
                'chunk_text': 'There are three main types of machine learning: supervised learning uses labeled training data, unsupervised learning finds patterns in unlabeled data, and reinforcement learning learns through rewards.',
                'chunk_hash': 'hash2',
                'created_at': '2025-10-19T19:00:00Z'
            }
        ]
        
        for vector in test_vectors:
            vectors_table.put_item(Item=vector)
        
        print(f"✅ Added {len(test_vectors)} test vectors")
        
    except Exception as e:
        print(f"Manual vector creation error: {e}")
    
    # Test RAG again
    print("\n5. Testing RAG with manual vectors...")
    
    import time
    time.sleep(5)
    
    try:
        response = requests.post(f"{api_url}/api/chat", json=chat_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ RAG Enhanced: {data.get('rag_enhanced', False)}")
            print(f"📚 Documents Used: {data.get('rag_documents_used', 0)}")
            print(f"🤖 Response: {data.get('response', '')[:200]}...")
            
            if data.get('citations'):
                print(f"📖 Citations: {data.get('citations')}")
                
            if data.get('rag_enhanced'):
                print("\n🎉 RAG is working!")
            else:
                print("\n⚠️  RAG still not working - check Lambda function")
        else:
            print(f"❌ Chat still failing: {response.text}")
            
    except Exception as e:
        print(f"Final test error: {e}")

if __name__ == "__main__":
    test_and_fix_rag()
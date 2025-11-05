#!/usr/bin/env python3
"""
Test vectors table
"""

import boto3

def test_vectors():
    """Test the vectors table"""
    
    print("🔍 Testing vectors table...")
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('lms-document-vectors')
    
    try:
        response = table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': 'test-user'}
        )
        
        items = response.get('Items', [])
        print(f"✅ Found {len(items)} vectors for test-user")
        
        for item in items:
            print(f"   - {item['filename']} chunk {item['chunk_index']}: {item['chunk_text'][:60]}...")
        
        return len(items) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_vectors()
#!/usr/bin/env python3
"""
Setup Pinecone indexes for LMS system
"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_lms_pinecone():
    """Setup Pinecone indexes for LMS system"""
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    
    # LMS Vector Index Configuration
    index_name = "lms-vectors"
    
    print(f"Setting up Pinecone index: {index_name}")
    
    # Check if index exists
    if not pc.has_index(index_name):
        print("Creating new index...")
        
        # Create index for Bedrock Titan embeddings (1536 dimensions)
        pc.create_index(
            name=index_name,
            dimension=1536,  # Bedrock Titan embedding dimension
            metric="cosine",
            spec={
                "serverless": {
                    "cloud": "aws",
                    "region": "us-east-1"
                }
            }
        )
        print(f"✅ Created index: {index_name}")
    else:
        print(f"✅ Index already exists: {index_name}")
    
    # Get index info
    index = pc.Index(index_name)
    stats = index.describe_index_stats()
    
    print(f"📊 Index Stats:")
    print(f"   - Dimension: {stats.get('dimension', 'N/A')}")
    print(f"   - Total Vectors: {stats.get('total_vector_count', 0)}")
    print(f"   - Namespaces: {list(stats.get('namespaces', {}).keys()) or ['None']}")
    
    return index_name

def test_pinecone_connection():
    """Test Pinecone connection and basic operations"""
    
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index_name = "lms-vectors"
    
    try:
        index = pc.Index(index_name)
        
        # Test upsert with sample data
        test_vectors = [
            {
                "id": "test_vector_1",
                "values": [0.1] * 1536,  # 1536-dimensional vector
                "metadata": {
                    "user_id": "test_user",
                    "subject_id": "test_subject",
                    "text": "This is a test document chunk",
                    "document_type": "test"
                }
            }
        ]
        
        # Upsert to documents namespace
        index.upsert(
            vectors=test_vectors,
            namespace="documents"
        )
        
        print("✅ Test upsert successful")
        
        # Test query
        query_result = index.query(
            namespace="documents",
            vector=[0.1] * 1536,
            filter={"user_id": "test_user"},
            top_k=1,
            include_metadata=True
        )
        
        if query_result['matches']:
            print("✅ Test query successful")
            print(f"   - Found {len(query_result['matches'])} matches")
        
        # Clean up test data
        index.delete(ids=["test_vector_1"], namespace="documents")
        print("✅ Test cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Pinecone test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up LMS Pinecone Configuration")
    print("=" * 50)
    
    # Setup index
    index_name = setup_lms_pinecone()
    
    print("\n🧪 Testing Pinecone Connection")
    print("=" * 50)
    
    # Test connection
    if test_pinecone_connection():
        print("\n✅ Pinecone setup complete and tested!")
        print(f"📝 Index '{index_name}' is ready for LMS system")
        print("\n📋 Next Steps:")
        print("1. Provide your Supabase URL and Anon Key in .env file")
        print("2. Run: sam build && sam deploy --guided")
        print("3. Start implementing Task 1: Serverless Project Setup")
    else:
        print("\n❌ Pinecone setup failed. Please check your API key and try again.")
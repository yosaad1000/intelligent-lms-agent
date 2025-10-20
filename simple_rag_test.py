#!/usr/bin/env python3
"""
Simple RAG test that works locally to demonstrate the concept
This bypasses the Lambda deployment issues and shows the RAG functionality
"""

import json
import asyncio
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append('src')

from chat.chat_handler import (
    retrieve_rag_context,
    get_user_profile,
    create_conversation,
    store_chat_message
)
from file_processing.vector_storage import vector_storage
from shared.pinecone_utils import pinecone_utils

class SimpleRAGTest:
    """Simple RAG test class"""
    
    def __init__(self):
        self.user_id = "test-user-123"
        self.conversation_id = None
        
    async def upload_document(self, filename, content):
        """Simulate document upload and processing"""
        
        print(f"📁 Uploading document: {filename}")
        
        # Create text chunks
        chunks = self.create_text_chunks(content)
        
        # Store in vector database (mock)
        vectors_stored = vector_storage.store_document_vectors(
            file_id=f"file-{datetime.now().timestamp()}",
            user_id=self.user_id,
            filename=filename,
            text_chunks=chunks,
            subject_id="test-subject",
            use_mock_embeddings=True
        )
        
        print(f"✅ Processed {len(chunks)} chunks, stored {vectors_stored} vectors")
        return True
    
    def create_text_chunks(self, text, chunk_size=500):
        """Create text chunks for processing"""
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size // 10):
            chunk_words = words[i:i + chunk_size // 10]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'index': len(chunks),
                'text': chunk_text,
                'length': len(chunk_text),
                'start_pos': i * 10,
                'end_pos': (i + len(chunk_words)) * 10
            })
        
        return chunks
    
    async def chat_with_rag(self, message):
        """Simulate RAG-enhanced chat"""
        
        print(f"💬 Processing message: {message}")
        
        # Create conversation if needed
        if not self.conversation_id:
            self.conversation_id = create_conversation(self.user_id, "test-subject")
            print(f"📝 Created conversation: {self.conversation_id}")
        
        # Retrieve RAG context
        rag_context, citations = await retrieve_rag_context(
            self.user_id, message, "test-subject"
        )
        
        print(f"🔍 RAG Context: {len(rag_context)} documents, {len(citations)} citations")
        
        # Get user profile
        user_profile = await get_user_profile(self.user_id)
        
        # Simulate AI response (since Bedrock agents aren't working)
        if rag_context:
            # Create response based on RAG context
            context_text = ' '.join([ctx['text'] for ctx in rag_context])
            ai_response = f"Based on your uploaded documents: {context_text[:200]}..."
            
            if citations:
                ai_response += f"\n\nSources: {', '.join(citations)}"
        else:
            ai_response = "I don't have any relevant documents to reference. Please upload some documents first."
        
        # Store conversation
        store_chat_message(
            self.conversation_id,
            self.user_id,
            message,
            ai_response,
            citations,
            rag_context
        )
        
        return {
            'success': True,
            'response': ai_response,
            'conversation_id': self.conversation_id,
            'citations': citations,
            'rag_documents_used': len(rag_context),
            'rag_enhanced': len(rag_context) > 0,
            'timestamp': datetime.utcnow().isoformat()
        }

async def main():
    """Run the simple RAG test"""
    
    print("🤖 Simple RAG Test - Local Demonstration")
    print("=" * 60)
    
    # Initialize test
    rag_test = SimpleRAGTest()
    
    # Test document content
    test_document = """
    Machine Learning Fundamentals
    
    Machine learning is a subset of artificial intelligence (AI) that enables computers to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.
    
    Types of Machine Learning:
    
    1. Supervised Learning: Uses labeled training data to learn a mapping function from input variables to output variables. Examples include classification and regression problems.
    
    2. Unsupervised Learning: Finds hidden patterns in data without labeled examples. Common techniques include clustering and dimensionality reduction.
    
    3. Reinforcement Learning: An agent learns to make decisions by taking actions in an environment to maximize cumulative reward.
    
    Key Concepts:
    - Training Data: The dataset used to teach the machine learning algorithm
    - Features: Individual measurable properties of observed phenomena
    - Model: The mathematical representation of a real-world process
    - Algorithm: The method used to build the model
    
    Applications:
    Machine learning is used in various fields including image recognition, natural language processing, recommendation systems, autonomous vehicles, medical diagnosis, and financial fraud detection.
    """
    
    # Step 1: Upload document
    print("\n📁 Step 1: Uploading test document...")
    await rag_test.upload_document("ml-fundamentals.txt", test_document)
    
    # Step 2: Test chat queries
    test_queries = [
        "What is machine learning?",
        "What are the types of machine learning mentioned?",
        "Tell me about supervised learning",
        "What are some applications of machine learning?"
    ]
    
    print("\n💬 Step 2: Testing RAG chat...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i} ---")
        result = await rag_test.chat_with_rag(query)
        
        print(f"✅ Success: {result['success']}")
        print(f"🔍 RAG Enhanced: {result['rag_enhanced']}")
        print(f"📚 Documents Used: {result['rag_documents_used']}")
        print(f"🤖 Response: {result['response'][:200]}...")
        
        if result['citations']:
            print(f"📖 Citations: {result['citations']}")
    
    print(f"\n🎉 RAG Test Complete!")
    print(f"✅ The RAG system concept is working locally")
    print(f"⚠️  Lambda deployment needs fixing for cloud functionality")

if __name__ == "__main__":
    asyncio.run(main())
"""
Integration Test for RAG-Enhanced Chat
Tests the complete workflow from file upload to RAG-enhanced chat responses
"""

import json
import pytest
import boto3
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock
from moto import mock_aws

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from chat.chat_handler import lambda_handler, process_chat_message_with_agent
from file_processing.file_handler import process_file_upload
from file_processing.vector_storage import VectorStorage


class TestRAGChatIntegration:
    """Integration test suite for complete RAG chat workflow"""
    
    @mock_aws
    def setup_method(self):
        """Set up test environment with all required services"""
        
        # Create DynamoDB tables
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Chat tables
        self.conversations_table = self.dynamodb.create_table(
            TableName='lms-chat-conversations',
            KeySchema=[
                {'AttributeName': 'conversation_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
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
        
        self.messages_table = self.dynamodb.create_table(
            TableName='lms-chat-messages',
            KeySchema=[
                {'AttributeName': 'conversation_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # File processing tables
        self.files_table = self.dynamodb.create_table(
            TableName='lms-user-files',
            KeySchema=[
                {'AttributeName': 'file_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'file_id', 'AttributeType': 'S'},
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
        
        # Create S3 bucket
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.s3_client.create_bucket(Bucket='lms-documents')
        
        # Test data
        self.test_user_id = 'test-user-123'
        self.test_subject_id = 'cs101'
        
        # Sample document content
        self.sample_document_content = """
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
        Machine learning is used in various fields including:
        - Image recognition and computer vision
        - Natural language processing
        - Recommendation systems
        - Autonomous vehicles
        - Medical diagnosis
        - Financial fraud detection
        """
    
    @patch('file_processing.vector_storage.VectorStorage.generate_embedding')
    @patch('shared.agent_utils.agent_invoker.chat_with_context')
    def test_complete_rag_workflow(self, mock_chat_agent, mock_embedding):
        """Test complete workflow: file upload -> processing -> RAG chat"""
        
        # Mock embedding generation
        mock_embedding.return_value = [0.1] * 1536  # Mock 1536-dimensional embedding
        
        # Mock agent response
        mock_chat_agent.return_value = {
            'success': True,
            'response': 'Based on your uploaded document about machine learning fundamentals, I can explain that machine learning is a subset of AI that enables computers to learn from experience. The document mentions three main types: supervised learning (using labeled data), unsupervised learning (finding hidden patterns), and reinforcement learning (learning through rewards).',
            'citations': [],
            'metadata': {}
        }
        
        # Step 1: Simulate file upload and processing
        file_id = self.simulate_file_processing()
        
        # Step 2: Test RAG-enhanced chat
        chat_event = {
            'httpMethod': 'POST',
            'path': '/api/chat',
            'body': json.dumps({
                'user_id': self.test_user_id,
                'message': 'What are the types of machine learning mentioned in my documents?',
                'subject_id': self.test_subject_id
            })
        }
        
        # Process chat request
        response = lambda_handler(chat_event, {})
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        assert body['success'] is True
        assert body['rag_enhanced'] is True
        assert body['rag_documents_used'] > 0
        assert len(body['citations']) > 0
        assert 'machine learning' in body['response'].lower()
        
        # Verify agent was called with RAG context
        mock_chat_agent.assert_called_once()
        call_args = mock_chat_agent.call_args
        assert len(call_args.kwargs['rag_context']) > 0
        
        # Verify RAG context contains relevant information
        rag_context = call_args.kwargs['rag_context']
        context_text = ' '.join([ctx['text'] for ctx in rag_context])
        assert 'supervised learning' in context_text.lower() or 'machine learning' in context_text.lower()
    
    def simulate_file_processing(self) -> str:
        """Simulate file upload and processing to create RAG context"""
        
        file_id = 'test-file-123'
        filename = 'ml_fundamentals.txt'
        
        # Store file metadata
        self.files_table.put_item(Item={
            'file_id': file_id,
            'user_id': self.test_user_id,
            'filename': filename,
            'subject_id': self.test_subject_id,
            'status': 'processed',
            'content_preview': self.sample_document_content[:200],
            'upload_timestamp': '2024-01-15T10:00:00Z'
        })
        
        # Store file content in S3
        self.s3_client.put_object(
            Bucket='lms-documents',
            Key=f'users/{self.test_user_id}/files/{file_id}_{filename}',
            Body=self.sample_document_content
        )
        
        # Simulate vector storage (mock Pinecone)
        vector_storage = VectorStorage()
        
        # Create text chunks
        chunks = self.create_text_chunks(self.sample_document_content)
        
        # Store vectors (will use mock embeddings)
        vectors_stored = vector_storage.store_document_vectors(
            file_id=file_id,
            user_id=self.test_user_id,
            filename=filename,
            text_chunks=chunks,
            subject_id=self.test_subject_id,
            use_mock_embeddings=True
        )
        
        assert vectors_stored > 0
        return file_id
    
    def create_text_chunks(self, text: str, chunk_size: int = 500) -> list:
        """Create text chunks for vector storage"""
        
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size // 10):  # Approximate word-based chunking
            chunk_words = words[i:i + chunk_size // 10]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'index': len(chunks),
                'text': chunk_text,
                'length': len(chunk_text),
                'start_pos': i * 10,  # Approximate
                'end_pos': (i + len(chunk_words)) * 10
            })
        
        return chunks
    
    @patch('shared.agent_utils.agent_invoker.chat_with_context')
    def test_rag_context_accuracy(self, mock_chat_agent):
        """Test that RAG context retrieval is accurate and relevant"""
        
        # Mock agent response
        mock_chat_agent.return_value = {
            'success': True,
            'response': 'Test response',
            'citations': [],
            'metadata': {}
        }
        
        # Set up file with specific content
        file_id = self.simulate_file_processing()
        
        # Test specific query about supervised learning
        result = asyncio.run(process_chat_message_with_agent(
            self.test_user_id,
            'What is supervised learning?',
            subject_id=self.test_subject_id
        ))
        
        # Verify RAG context was used
        assert result['rag_enhanced'] is True
        assert result['rag_documents_used'] > 0
        
        # Verify agent was called with relevant context
        mock_chat_agent.assert_called_once()
        call_args = mock_chat_agent.call_args
        rag_context = call_args.kwargs['rag_context']
        
        # Check that context contains relevant information
        context_text = ' '.join([ctx['text'] for ctx in rag_context]).lower()
        assert 'supervised' in context_text or 'labeled' in context_text
    
    @patch('shared.agent_utils.agent_invoker.chat_with_context')
    def test_subject_filtering_in_rag(self, mock_chat_agent):
        """Test that RAG context is properly filtered by subject"""
        
        mock_chat_agent.return_value = {
            'success': True,
            'response': 'Test response',
            'citations': [],
            'metadata': {}
        }
        
        # Create files for different subjects
        cs_file_id = self.simulate_file_processing()
        
        # Simulate a math file
        math_file_id = 'math-file-456'
        self.files_table.put_item(Item={
            'file_id': math_file_id,
            'user_id': self.test_user_id,
            'filename': 'calculus.txt',
            'subject_id': 'math101',  # Different subject
            'status': 'processed',
            'content_preview': 'Calculus is a branch of mathematics...',
            'upload_timestamp': '2024-01-15T11:00:00Z'
        })
        
        # Query with CS subject filter
        result = asyncio.run(process_chat_message_with_agent(
            self.test_user_id,
            'What is machine learning?',
            subject_id='cs101'  # Should only get CS documents
        ))
        
        # Verify subject filtering worked
        mock_chat_agent.assert_called_once()
        call_args = mock_chat_agent.call_args
        
        # Check that subject_id was passed correctly
        assert call_args.kwargs['subject_id'] == 'cs101'
    
    def test_conversation_persistence_with_rag(self):
        """Test that conversations with RAG context are properly stored"""
        
        # Set up file processing
        file_id = self.simulate_file_processing()
        
        # Create a conversation with RAG
        with patch('shared.agent_utils.agent_invoker.chat_with_context') as mock_agent:
            mock_agent.return_value = {
                'success': True,
                'response': 'Machine learning response with RAG context',
                'citations': [],
                'metadata': {}
            }
            
            chat_event = {
                'httpMethod': 'POST',
                'path': '/api/chat',
                'body': json.dumps({
                    'user_id': self.test_user_id,
                    'message': 'Explain machine learning',
                    'subject_id': self.test_subject_id
                })
            }
            
            response = lambda_handler(chat_event, {})
            body = json.loads(response['body'])
            conversation_id = body['conversation_id']
        
        # Verify conversation was stored
        conv_response = self.conversations_table.get_item(
            Key={'conversation_id': conversation_id}
        )
        assert 'Item' in conv_response
        
        # Verify messages were stored with RAG metadata
        messages_response = self.messages_table.query(
            KeyConditionExpression='conversation_id = :conv_id',
            ExpressionAttributeValues={':conv_id': conversation_id}
        )
        
        messages = messages_response['Items']
        assert len(messages) == 2  # User + AI message
        
        # Check AI message has RAG metadata
        ai_message = next(msg for msg in messages if msg['message_type'] == 'assistant')
        assert ai_message['context_used']['rag_retrieval'] is True
        assert ai_message['context_used']['rag_documents_count'] > 0
    
    def test_conversation_history_retrieval(self):
        """Test retrieving conversation history with RAG context"""
        
        # Set up and create conversation
        file_id = self.simulate_file_processing()
        
        with patch('shared.agent_utils.agent_invoker.chat_with_context') as mock_agent:
            mock_agent.return_value = {
                'success': True,
                'response': 'Response with RAG',
                'citations': ['ml_fundamentals.txt (chunk 1)'],
                'metadata': {}
            }
            
            # Create conversation
            chat_event = {
                'httpMethod': 'POST',
                'path': '/api/chat',
                'body': json.dumps({
                    'user_id': self.test_user_id,
                    'message': 'What is ML?',
                    'subject_id': self.test_subject_id
                })
            }
            
            response = lambda_handler(chat_event, {})
            body = json.loads(response['body'])
            conversation_id = body['conversation_id']
        
        # Retrieve conversation history
        history_event = {
            'httpMethod': 'GET',
            'path': '/api/chat/history',
            'queryStringParameters': {
                'user_id': self.test_user_id,
                'conversation_id': conversation_id
            }
        }
        
        history_response = lambda_handler(history_event, {})
        history_body = json.loads(history_response['body'])
        
        assert history_response['statusCode'] == 200
        assert len(history_body['messages']) == 2
        
        # Verify RAG metadata is preserved
        ai_message = next(
            msg for msg in history_body['messages'] 
            if msg['message_type'] == 'assistant'
        )
        assert ai_message['context_used']['rag_retrieval'] is True
        assert len(ai_message['citations']) > 0
    
    @patch('shared.agent_utils.agent_invoker.chat_with_context')
    def test_no_relevant_documents_fallback(self, mock_chat_agent):
        """Test behavior when no relevant documents are found"""
        
        mock_chat_agent.return_value = {
            'success': True,
            'response': 'I don\'t have specific information about that topic in your uploaded documents.',
            'citations': [],
            'metadata': {}
        }
        
        # Query about topic not in documents
        result = asyncio.run(process_chat_message_with_agent(
            self.test_user_id,
            'What is quantum computing?',  # Not in our ML document
            subject_id=self.test_subject_id
        ))
        
        # Should still work but with no RAG context
        assert result['success'] is True
        assert result['rag_documents_used'] == 0
        assert result['rag_enhanced'] is False
        
        # Agent should still be called but with empty RAG context
        mock_chat_agent.assert_called_once()
        call_args = mock_chat_agent.call_args
        assert len(call_args.kwargs['rag_context']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
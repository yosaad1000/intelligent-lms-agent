"""
Test RAG-Enhanced AI Chat Lambda Function
Tests the complete RAG chat functionality including vector retrieval and context accuracy
"""

import json
import pytest
import boto3
import asyncio
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from chat.chat_handler import (
    lambda_handler,
    handle_chat_message,
    handle_conversation_history,
    process_chat_message_with_agent,
    retrieve_rag_context,
    get_user_profile,
    create_conversation,
    store_chat_message,
    get_conversation_history,
    get_conversation_messages,
    get_user_conversations
)


class TestRAGChatFunctionality:
    """Test suite for RAG-enhanced chat functionality"""
    
    @mock_aws
    def setup_method(self):
        """Set up test environment"""
        
        # Create mock DynamoDB tables
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create conversations table
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
        
        # Create messages table
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
        
        # Test data
        self.test_user_id = 'test-user-123'
        self.test_message = 'What is machine learning?'
        self.test_conversation_id = 'conv-123'
        
        # Mock RAG context
        self.mock_rag_context = [
            {
                'text': 'Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.',
                'source': 'ml_basics.pdf',
                'chunk_index': 0,
                'score': 0.95,
                'file_id': 'file-123',
                'subject_id': 'cs101'
            },
            {
                'text': 'There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.',
                'source': 'ml_types.pdf',
                'chunk_index': 1,
                'score': 0.88,
                'file_id': 'file-456',
                'subject_id': 'cs101'
            }
        ]
        
        self.mock_citations = [
            'ml_basics.pdf (chunk 1)',
            'ml_types.pdf (chunk 2)'
        ]
    
    def test_lambda_handler_chat_message(self):
        """Test lambda handler for chat message"""
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/chat',
            'body': json.dumps({
                'user_id': self.test_user_id,
                'message': self.test_message,
                'subject_id': 'cs101'
            })
        }
        
        with patch('chat.chat_handler.process_chat_message_with_agent') as mock_process:
            mock_process.return_value = {
                'success': True,
                'response': 'Machine learning is a powerful AI technique...',
                'conversation_id': self.test_conversation_id,
                'citations': self.mock_citations,
                'rag_documents_used': 2,
                'rag_enhanced': True
            }
            
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert body['rag_enhanced'] is True
            assert body['rag_documents_used'] == 2
            assert len(body['citations']) == 2
    
    def test_lambda_handler_conversation_history(self):
        """Test lambda handler for conversation history"""
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/chat/history',
            'queryStringParameters': {
                'user_id': self.test_user_id,
                'conversation_id': self.test_conversation_id
            }
        }
        
        with patch('chat.chat_handler.get_conversation_messages') as mock_get_messages:
            mock_get_messages.return_value = [
                {
                    'message_id': 'msg-1',
                    'message_type': 'user',
                    'content': 'What is ML?',
                    'timestamp': 1234567890,
                    'citations': [],
                    'context_used': {}
                },
                {
                    'message_id': 'msg-2',
                    'message_type': 'assistant',
                    'content': 'Machine learning is...',
                    'timestamp': 1234567891,
                    'citations': self.mock_citations,
                    'context_used': {'rag_retrieval': True}
                }
            ]
            
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['conversation_id'] == self.test_conversation_id
            assert len(body['messages']) == 2
            assert body['messages'][1]['citations'] == self.mock_citations
    
    @patch('chat.chat_handler.vector_storage')
    @patch('chat.chat_handler.agent_invoker')
    def test_process_chat_message_with_rag(self, mock_agent_invoker, mock_vector_storage):
        """Test processing chat message with RAG context"""
        
        # Mock vector storage response
        mock_vector_storage.query_similar_vectors.return_value = [
            {
                'id': 'vec-1',
                'score': 0.95,
                'text': self.mock_rag_context[0]['text'],
                'metadata': {
                    'filename': 'ml_basics.pdf',
                    'chunk_index': 0,
                    'file_id': 'file-123',
                    'subject_id': 'cs101'
                }
            }
        ]
        
        # Mock agent response
        mock_agent_invoker.chat_with_context.return_value = {
            'success': True,
            'response': 'Based on your documents, machine learning is...',
            'citations': [],
            'metadata': {}
        }
        
        # Test the function
        result = asyncio.run(process_chat_message_with_agent(
            self.test_user_id,
            self.test_message,
            subject_id='cs101'
        ))
        
        assert result['success'] is True
        assert result['rag_enhanced'] is True
        assert result['rag_documents_used'] == 1
        assert len(result['citations']) > 0
        
        # Verify agent was called with RAG context
        mock_agent_invoker.chat_with_context.assert_called_once()
        call_args = mock_agent_invoker.chat_with_context.call_args
        assert len(call_args.kwargs['rag_context']) == 1
    
    @patch('chat.chat_handler.vector_storage')
    def test_retrieve_rag_context(self, mock_vector_storage):
        """Test RAG context retrieval"""
        
        # Mock vector storage response
        mock_vector_storage.query_similar_vectors.return_value = [
            {
                'id': 'vec-1',
                'score': 0.95,
                'text': self.mock_rag_context[0]['text'],
                'metadata': {
                    'filename': 'ml_basics.pdf',
                    'chunk_index': 0,
                    'file_id': 'file-123',
                    'subject_id': 'cs101'
                }
            },
            {
                'id': 'vec-2',
                'score': 0.88,
                'text': self.mock_rag_context[1]['text'],
                'metadata': {
                    'filename': 'ml_types.pdf',
                    'chunk_index': 1,
                    'file_id': 'file-456',
                    'subject_id': 'cs101'
                }
            }
        ]
        
        # Test RAG context retrieval
        rag_context, citations = asyncio.run(retrieve_rag_context(
            self.test_user_id,
            self.test_message,
            subject_id='cs101'
        ))
        
        assert len(rag_context) == 2
        assert len(citations) == 2
        assert rag_context[0]['text'] == self.mock_rag_context[0]['text']
        assert rag_context[0]['score'] == 0.95
        assert 'ml_basics.pdf (chunk 1)' in citations
        assert 'ml_types.pdf (chunk 2)' in citations
        
        # Verify vector storage was called correctly
        mock_vector_storage.query_similar_vectors.assert_called_once_with(
            query_text=self.test_message,
            user_id=self.test_user_id,
            top_k=5,
            subject_id='cs101',
            use_mock=True  # Should use mock when not available
        )
    
    @patch('chat.chat_handler.vector_storage')
    def test_retrieve_rag_context_low_scores(self, mock_vector_storage):
        """Test RAG context retrieval with low confidence scores"""
        
        # Mock vector storage response with low scores
        mock_vector_storage.query_similar_vectors.return_value = [
            {
                'id': 'vec-1',
                'score': 0.5,  # Below threshold
                'text': 'Some irrelevant text',
                'metadata': {
                    'filename': 'irrelevant.pdf',
                    'chunk_index': 0,
                    'file_id': 'file-999'
                }
            }
        ]
        
        # Test RAG context retrieval
        rag_context, citations = asyncio.run(retrieve_rag_context(
            self.test_user_id,
            self.test_message
        ))
        
        # Should filter out low-confidence matches
        assert len(rag_context) == 0
        assert len(citations) == 0
    
    def test_get_user_profile(self):
        """Test user profile retrieval"""
        
        profile = asyncio.run(get_user_profile(self.test_user_id))
        
        assert isinstance(profile, dict)
        assert 'mastery_levels' in profile
        assert 'difficulty_preference' in profile
        assert 'learning_style' in profile
        assert profile['difficulty_preference'] == 'intermediate'
    
    def test_create_conversation(self):
        """Test conversation creation"""
        
        conversation_id = create_conversation(self.test_user_id, subject_id='cs101')
        
        assert conversation_id is not None
        assert len(conversation_id) > 0
        
        # Verify conversation was stored in DynamoDB
        response = self.conversations_table.get_item(
            Key={'conversation_id': conversation_id}
        )
        
        assert 'Item' in response
        item = response['Item']
        assert item['user_id'] == self.test_user_id
        assert item['subject_id'] == 'cs101'
        assert item['conversation_type'] == 'subject'
        assert item['message_count'] == 0
    
    def test_store_chat_message_with_rag(self):
        """Test storing chat message with RAG context"""
        
        # Create conversation first
        conversation_id = create_conversation(self.test_user_id)
        
        # Store message with RAG context
        store_chat_message(
            conversation_id,
            self.test_user_id,
            self.test_message,
            'AI response with RAG context',
            self.mock_citations,
            self.mock_rag_context
        )
        
        # Verify messages were stored
        response = self.messages_table.query(
            KeyConditionExpression='conversation_id = :conv_id',
            ExpressionAttributeValues={':conv_id': conversation_id}
        )
        
        assert len(response['Items']) == 2  # User message + AI response
        
        # Check AI response message
        ai_message = next(
            item for item in response['Items'] 
            if item['message_type'] == 'assistant'
        )
        
        assert ai_message['citations'] == self.mock_citations
        assert ai_message['context_used']['rag_retrieval'] is True
        assert ai_message['context_used']['rag_documents_count'] == 2
        assert ai_message['context_used']['citations_count'] == 2
    
    def test_get_conversation_messages(self):
        """Test getting conversation messages"""
        
        # Create conversation and add messages
        conversation_id = create_conversation(self.test_user_id)
        store_chat_message(
            conversation_id,
            self.test_user_id,
            'Test question',
            'Test answer',
            ['source.pdf'],
            [{'text': 'context'}]
        )
        
        # Get messages
        messages = get_conversation_messages(conversation_id)
        
        assert len(messages) == 2
        assert messages[0]['message_type'] == 'user'
        assert messages[1]['message_type'] == 'assistant'
        assert messages[1]['citations'] == ['source.pdf']
    
    def test_get_user_conversations(self):
        """Test getting user conversations"""
        
        # Create multiple conversations
        conv1 = create_conversation(self.test_user_id, subject_id='cs101')
        conv2 = create_conversation(self.test_user_id, subject_id='math101')
        
        # Get conversations
        conversations = get_user_conversations(self.test_user_id)
        
        assert len(conversations) == 2
        conversation_ids = [conv['conversation_id'] for conv in conversations]
        assert conv1 in conversation_ids
        assert conv2 in conversation_ids
    
    def test_error_handling_no_message(self):
        """Test error handling when no message provided"""
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/chat',
            'body': json.dumps({
                'user_id': self.test_user_id
                # Missing message
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Message is required' in body['error']
    
    def test_error_handling_invalid_method(self):
        """Test error handling for invalid HTTP method"""
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/api/chat',
            'body': json.dumps({})
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 405
        body = json.loads(response['body'])
        assert 'Method not allowed' in body['error']
    
    @patch('chat.chat_handler.vector_storage')
    def test_rag_context_with_subject_filter(self, mock_vector_storage):
        """Test RAG context retrieval with subject filtering"""
        
        mock_vector_storage.query_similar_vectors.return_value = []
        
        asyncio.run(retrieve_rag_context(
            self.test_user_id,
            self.test_message,
            subject_id='physics101'
        ))
        
        # Verify subject filter was passed
        mock_vector_storage.query_similar_vectors.assert_called_once()
        call_args = mock_vector_storage.query_similar_vectors.call_args
        assert call_args.kwargs['subject_id'] == 'physics101'
    
    @patch('chat.chat_handler.agent_invoker')
    def test_fallback_response_on_agent_failure(self, mock_agent_invoker):
        """Test fallback response when Bedrock Agent fails"""
        
        # Mock agent failure
        mock_agent_invoker.chat_with_context.return_value = {
            'success': False,
            'error': 'Agent timeout'
        }
        
        result = asyncio.run(process_chat_message_with_agent(
            self.test_user_id,
            self.test_message
        ))
        
        assert result['success'] is False
        assert 'trouble processing' in result['response']
        assert result['bedrock_agent_used'] is False
        assert 'Agent timeout' in result['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
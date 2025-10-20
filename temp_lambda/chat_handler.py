"""
Chat Lambda function
Handles AI chat with RAG integration using Bedrock Agents
"""

import json
import boto3
import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from decimal import Decimal

# Import shared services
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.agent_utils import agent_invoker
from shared.bedrock_agent_service import BedrockAgentError, BedrockAgentService, AgentContext
from file_processing.vector_storage import vector_storage, format_rag_context
from shared.pinecone_utils import pinecone_utils

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle chat requests and conversation history with AI and RAG using Bedrock Agents
    """
    
    try:
        # Get HTTP method and path
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        
        # Handle different endpoints
        if http_method == 'GET' and 'history' in path:
            return handle_conversation_history(event)
        elif http_method == 'POST':
            return handle_chat_message(event)
        else:
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
    except Exception as e:
        logger.error(f"Error in chat handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }


def handle_chat_message(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /api/chat - send chat message"""
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract user info (for testing without auth)
        user_id = body.get('user_id', 'test-user-123')
        message = body.get('message', '').strip()
        conversation_id = body.get('conversation_id')
        subject_id = body.get('subject_id')
        
        if not message:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Process chat message with Bedrock Agent
        response = asyncio.run(process_chat_message_with_agent(user_id, message, conversation_id, subject_id))
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response, default=decimal_to_int)
        }
        
    except Exception as e:
        logger.error(f"Error handling chat message: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }


def handle_conversation_history(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /api/chat/history - get conversation history"""
    
    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id', 'test-user-123')
        conversation_id = query_params.get('conversation_id')
        limit = int(query_params.get('limit', '20'))
        
        if conversation_id:
            # Get specific conversation history
            messages = get_conversation_messages(conversation_id, limit)
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'conversation_id': conversation_id,
                    'messages': messages,
                    'total_messages': len(messages)
                }, default=decimal_to_int)
            }
        else:
            # Get all conversations for user
            conversations = get_user_conversations(user_id, limit)
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'conversations': conversations,
                    'total_conversations': len(conversations)
                }, default=decimal_to_int)
            }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }


async def process_chat_message_with_agent(user_id: str, message: str, conversation_id: str = None, subject_id: str = None) -> Dict[str, Any]:
    """Process chat message with Bedrock Agent and RAG"""
    
    try:
        # Create or get conversation
        if not conversation_id:
            conversation_id = create_conversation(user_id, subject_id)
        
        # Get conversation history for context
        conversation_history = get_conversation_history(conversation_id)
        
        # Retrieve RAG context from user's documents
        rag_context, citations = await retrieve_rag_context(user_id, message, subject_id)
        
        # Get user profile for personalization (basic implementation)
        user_profile = await get_user_profile(user_id)
        
        # Invoke Bedrock Chat Agent with enhanced context
        agent_response = await agent_invoker.chat_with_context(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            subject_id=subject_id,
            rag_context=rag_context,
            user_profile=user_profile
        )
        
        if agent_response['success']:
            ai_response = agent_response['response']
            agent_citations = agent_response.get('citations', [])
            
            # Combine RAG citations with agent citations
            all_citations = citations + agent_citations
            
            # Store conversation message with RAG metadata
            store_chat_message(conversation_id, user_id, message, ai_response, all_citations, rag_context)
            
            return {
                'success': True,
                'response': ai_response,
                'conversation_id': conversation_id,
                'timestamp': datetime.utcnow().isoformat(),
                'citations': all_citations,
                'rag_documents_used': len(rag_context),
                'subject_context': subject_id,
                'agent_metadata': agent_response.get('metadata', {}),
                'bedrock_agent_used': True,
                'rag_enhanced': len(rag_context) > 0
            }
        else:
            # Fallback response if agent fails
            fallback_response = "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
            
            store_chat_message(conversation_id, user_id, message, fallback_response, citations, rag_context)
            
            return {
                'success': False,
                'response': fallback_response,
                'conversation_id': conversation_id,
                'timestamp': datetime.utcnow().isoformat(),
                'citations': citations,
                'rag_documents_used': len(rag_context),
                'subject_context': subject_id,
                'error': agent_response.get('error', 'Unknown error'),
                'bedrock_agent_used': False,
                'rag_enhanced': len(rag_context) > 0
            }
        
    except BedrockAgentError as e:
        logger.error(f"Bedrock Agent error: {str(e)}")
        
        # Store error and provide fallback
        fallback_response = "I'm experiencing technical difficulties. Please try again later."
        if conversation_id:
            store_chat_message(conversation_id, user_id, message, fallback_response, [], [])
        
        return {
            'success': False,
            'response': fallback_response,
            'conversation_id': conversation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'citations': [],
            'rag_documents_used': 0,
            'error': f"Bedrock Agent error: {str(e)}",
            'bedrock_agent_used': False,
            'rag_enhanced': False
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise


def create_conversation(user_id: str, subject_id: str = None) -> str:
    """Create a new conversation"""
    
    conversation_id = str(uuid.uuid4())
    
    # Determine conversation type and title
    if subject_id:
        conversation_type = 'subject'
        title = f"Subject Chat - {subject_id}"
    else:
        conversation_type = 'general'
        title = "General Chat"
    
    # Store conversation in DynamoDB
    dynamodb = boto3.resource('dynamodb')
    conversations_table = dynamodb.Table('lms-chat-conversations')
    
    conversation_data = {
        'conversation_id': conversation_id,
        'user_id': user_id,
        'subject_id': subject_id,
        'conversation_type': conversation_type,
        'title': title,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'message_count': 0
    }
    
    conversations_table.put_item(Item=conversation_data)
    
    return conversation_id


def store_chat_message(conversation_id: str, user_id: str, user_message: str, ai_response: str, citations: list = None, rag_context: list = None):
    """Store chat messages in DynamoDB with Bedrock Agent and RAG metadata"""
    
    dynamodb = boto3.resource('dynamodb')
    messages_table = dynamodb.Table('lms-chat-messages')
    conversations_table = dynamodb.Table('lms-chat-conversations')
    
    timestamp = int(datetime.utcnow().timestamp() * 1000)  # Milliseconds
    citations = citations or []
    rag_context = rag_context or []
    
    # Store user message
    user_message_data = {
        'conversation_id': conversation_id,
        'timestamp': timestamp,
        'message_id': str(uuid.uuid4()),
        'user_id': user_id,
        'message_type': 'user',
        'content': user_message,
        'citations': [],
        'context_used': {}
    }
    
    messages_table.put_item(Item=user_message_data)
    
    # Store AI response
    ai_message_data = {
        'conversation_id': conversation_id,
        'timestamp': timestamp + 1,  # Slightly later timestamp
        'message_id': str(uuid.uuid4()),
        'user_id': user_id,
        'message_type': 'assistant',
        'content': ai_response,
        'citations': citations,
        'context_used': {
            'rag_retrieval': len(rag_context) > 0,  # True if RAG context used
            'rag_documents_count': len(rag_context),
            'citations_count': len(citations),
            'bedrock_agent': True,  # Now using Bedrock Agent
            'agent_type': 'chat'
        }
    }
    
    messages_table.put_item(Item=ai_message_data)
    
    # Update conversation metadata
    conversations_table.update_item(
        Key={'conversation_id': conversation_id},
        UpdateExpression='SET updated_at = :updated_at, message_count = message_count + :inc',
        ExpressionAttributeValues={
            ':updated_at': datetime.utcnow().isoformat(),
            ':inc': 2  # User message + AI response
        }
    )


def get_conversation_history(conversation_id: str, limit: int = 10) -> list:
    """Get recent conversation history for context"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        messages_table = dynamodb.Table('lms-chat-messages')
        
        response = messages_table.query(
            KeyConditionExpression='conversation_id = :conv_id',
            ExpressionAttributeValues={':conv_id': conversation_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit * 2  # Get both user and assistant messages
        )
        
        # Format for agent context
        history = []
        for item in reversed(response['Items']):  # Reverse to chronological order
            history.append({
                'role': item['message_type'],
                'content': item['content']
            })
        
        return history[-limit:] if len(history) > limit else history
        
    except Exception as e:
        logger.warning(f"Error getting conversation history: {str(e)}")
        return []


def get_conversation_messages(conversation_id: str, limit: int = 20) -> list:
    """Get conversation messages for API response"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        messages_table = dynamodb.Table('lms-chat-messages')
        
        response = messages_table.query(
            KeyConditionExpression='conversation_id = :conv_id',
            ExpressionAttributeValues={':conv_id': conversation_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        
        # Format for API response
        messages = []
        for item in reversed(response['Items']):  # Reverse to chronological order
            messages.append({
                'message_id': item['message_id'],
                'message_type': item['message_type'],
                'content': item['content'],
                'timestamp': int(item['timestamp']) if isinstance(item['timestamp'], Decimal) else item['timestamp'],
                'citations': item.get('citations', []),
                'context_used': item.get('context_used', {})
            })
        
        return messages
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        return []


def get_user_conversations(user_id: str, limit: int = 20) -> list:
    """Get all conversations for a user"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        conversations_table = dynamodb.Table('lms-chat-conversations')
        
        response = conversations_table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        
        # Format for API response
        conversations = []
        for item in response['Items']:
            conversations.append({
                'conversation_id': item['conversation_id'],
                'title': item['title'],
                'conversation_type': item['conversation_type'],
                'subject_id': item.get('subject_id'),
                'message_count': int(item.get('message_count', 0)) if isinstance(item.get('message_count', 0), Decimal) else item.get('message_count', 0),
                'created_at': item['created_at'],
                'updated_at': item['updated_at']
            })
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        return []


async def retrieve_rag_context(user_id: str, query: str, subject_id: str = None, top_k: int = 5) -> tuple:
    """
    Retrieve relevant document context using RAG (Retrieval-Augmented Generation)
    
    Args:
        user_id: User identifier for filtering documents
        query: User's chat message/query
        subject_id: Optional subject filter
        top_k: Number of relevant chunks to retrieve
        
    Returns:
        Tuple of (rag_context_list, citations_list)
    """
    
    try:
        logger.info(f"Retrieving RAG context for user {user_id}, query: {query[:100]}...")
        
        # Query similar vectors from Pinecone
        similar_documents = vector_storage.query_similar_vectors(
            query_text=query,
            user_id=user_id,
            top_k=top_k,
            subject_id=subject_id,
            use_mock=not vector_storage.is_available()  # Use mock if Pinecone unavailable
        )
        
        if not similar_documents:
            logger.info("No relevant documents found for RAG context")
            return [], []
        
        # Format RAG context and extract citations
        rag_context = []
        citations = []
        
        for doc in similar_documents:
            metadata = doc.get('metadata', {})
            text = doc.get('text', '')
            score = doc.get('score', 0)
            
            # Only include high-confidence matches
            if score < 0.7:
                continue
            
            # Add to RAG context
            rag_context.append({
                'text': text,
                'source': metadata.get('filename', 'Unknown'),
                'chunk_index': metadata.get('chunk_index', 0),
                'score': score,
                'file_id': metadata.get('file_id', ''),
                'subject_id': metadata.get('subject_id')
            })
            
            # Create citation
            filename = metadata.get('filename', 'Unknown')
            chunk_index = metadata.get('chunk_index', 0)
            citation = f"{filename} (chunk {chunk_index + 1})"
            if citation not in citations:
                citations.append(citation)
        
        logger.info(f"Retrieved {len(rag_context)} relevant documents for RAG context")
        return rag_context, citations
        
    except Exception as e:
        logger.error(f"Error retrieving RAG context: {str(e)}")
        return [], []


async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user learning profile for personalization
    
    Args:
        user_id: User identifier
        
    Returns:
        Dictionary with user profile information
    """
    
    try:
        # Basic user profile implementation
        # In a full implementation, this would query user intelligence from Pinecone
        # For now, return a basic profile
        
        profile = {
            'mastery_levels': {},
            'difficulty_preference': 'intermediate',
            'learning_style': 'balanced',
            'interaction_count': 0
        }
        
        # TODO: Implement full user intelligence retrieval from Pinecone
        # This would be enhanced in Task 8 (Personalization and Analytics)
        
        return profile
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return {
            'mastery_levels': {},
            'difficulty_preference': 'intermediate',
            'learning_style': 'balanced',
            'interaction_count': 0
        }


def decimal_to_int(obj):
    """Convert DynamoDB Decimal to int for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }
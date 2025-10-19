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

# Import shared services
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.agent_utils import agent_invoker
from shared.bedrock_agent_service import BedrockAgentError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle chat requests with AI and RAG using Bedrock Agents
    """
    
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
            'body': json.dumps(response)
        }
        
    except Exception as e:
        logger.error(f"Error in chat handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


async def process_chat_message_with_agent(user_id: str, message: str, conversation_id: str = None, subject_id: str = None) -> Dict[str, Any]:
    """Process chat message with Bedrock Agent and RAG"""
    
    try:
        # Create or get conversation
        if not conversation_id:
            conversation_id = create_conversation(user_id, subject_id)
        
        # Get conversation history for context
        conversation_history = get_conversation_history(conversation_id)
        
        # TODO: Retrieve RAG context (will be implemented in Task 4)
        rag_context = []  # Placeholder for RAG retrieval
        
        # TODO: Get user profile (will be implemented in Task 8)
        user_profile = {}  # Placeholder for user personalization
        
        # Invoke Bedrock Chat Agent
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
            citations = agent_response.get('citations', [])
            
            # Store conversation message
            store_chat_message(conversation_id, user_id, message, ai_response, citations)
            
            return {
                'success': True,
                'response': ai_response,
                'conversation_id': conversation_id,
                'timestamp': datetime.utcnow().isoformat(),
                'citations': citations,
                'subject_context': subject_id,
                'agent_metadata': agent_response.get('metadata', {}),
                'bedrock_agent_used': True
            }
        else:
            # Fallback response if agent fails
            fallback_response = "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
            
            store_chat_message(conversation_id, user_id, message, fallback_response, [])
            
            return {
                'success': False,
                'response': fallback_response,
                'conversation_id': conversation_id,
                'timestamp': datetime.utcnow().isoformat(),
                'citations': [],
                'subject_context': subject_id,
                'error': agent_response.get('error', 'Unknown error'),
                'bedrock_agent_used': False
            }
        
    except BedrockAgentError as e:
        logger.error(f"Bedrock Agent error: {str(e)}")
        
        # Store error and provide fallback
        fallback_response = "I'm experiencing technical difficulties. Please try again later."
        if conversation_id:
            store_chat_message(conversation_id, user_id, message, fallback_response, [])
        
        return {
            'success': False,
            'response': fallback_response,
            'conversation_id': conversation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'citations': [],
            'error': f"Bedrock Agent error: {str(e)}",
            'bedrock_agent_used': False
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


def store_chat_message(conversation_id: str, user_id: str, user_message: str, ai_response: str, citations: list = None):
    """Store chat messages in DynamoDB with Bedrock Agent metadata"""
    
    dynamodb = boto3.resource('dynamodb')
    messages_table = dynamodb.Table('lms-chat-messages')
    conversations_table = dynamodb.Table('lms-chat-conversations')
    
    timestamp = int(datetime.utcnow().timestamp() * 1000)  # Milliseconds
    citations = citations or []
    
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
            'rag_retrieval': len(citations) > 0,  # True if citations provided
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


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }
"""
Voice Interview Lambda function
Handles AI-powered voice interviews using Bedrock Agents and WebSocket
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
    Handle voice interview WebSocket connections and messages
    """
    
    try:
        # Get connection info
        connection_id = event.get('requestContext', {}).get('connectionId')
        route_key = event.get('requestContext', {}).get('routeKey')
        
        if route_key == '$connect':
            return handle_connect(connection_id, event)
        elif route_key == '$disconnect':
            return handle_disconnect(connection_id, event)
        elif route_key == 'start_interview':
            return handle_start_interview(connection_id, event)
        elif route_key == 'audio_chunk':
            return handle_audio_chunk(connection_id, event)
        elif route_key == 'end_interview':
            return handle_end_interview(connection_id, event)
        else:
            logger.warning(f"Unknown route: {route_key}")
            return {'statusCode': 400}
        
    except Exception as e:
        logger.error(f"Error in interview handler: {str(e)}")
        return {'statusCode': 500}


def handle_connect(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle WebSocket connection"""
    
    try:
        # Store connection info
        dynamodb = boto3.resource('dynamodb')
        connections_table = dynamodb.Table('lms-websocket-connections')
        
        # Extract user info from query parameters
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id', 'anonymous')
        
        connection_data = {
            'connection_id': connection_id,
            'user_id': user_id,
            'connected_at': datetime.utcnow().isoformat(),
            'status': 'connected',
            'interview_session_id': None
        }
        
        connections_table.put_item(Item=connection_data)
        
        logger.info(f"WebSocket connected: {connection_id} for user: {user_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling connect: {str(e)}")
        return {'statusCode': 500}


def handle_disconnect(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle WebSocket disconnection"""
    
    try:
        # Clean up connection
        dynamodb = boto3.resource('dynamodb')
        connections_table = dynamodb.Table('lms-websocket-connections')
        
        # Get connection info before deleting
        response = connections_table.get_item(Key={'connection_id': connection_id})
        
        if 'Item' in response:
            connection_data = response['Item']
            interview_session_id = connection_data.get('interview_session_id')
            
            # End any active interview session
            if interview_session_id:
                end_interview_session(interview_session_id, 'disconnected')
        
        # Delete connection record
        connections_table.delete_item(Key={'connection_id': connection_id})
        
        logger.info(f"WebSocket disconnected: {connection_id}")
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error handling disconnect: {str(e)}")
        return {'statusCode': 500}


def handle_start_interview(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Start a new interview session"""
    
    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id', 'anonymous')
        interview_type = body.get('interview_type', 'general')
        topic = body.get('topic')
        subject_id = body.get('subject_id')
        
        # Start interview session
        response = asyncio.run(start_interview_session(
            connection_id, user_id, interview_type, topic, subject_id
        ))
        
        # Send response back through WebSocket
        send_websocket_message(connection_id, {
            'type': 'interview_started',
            'session_id': response['session_id'],
            'initial_question': response['question'],
            'metadata': response['metadata']
        })
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        
        # Send error message
        send_websocket_message(connection_id, {
            'type': 'error',
            'message': 'Failed to start interview session'
        })
        
        return {'statusCode': 500}


def handle_audio_chunk(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming audio chunk for transcription"""
    
    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        audio_data = body.get('audio_data')  # Base64 encoded audio
        session_id = body.get('session_id')
        is_final = body.get('is_final', False)
        
        if not audio_data or not session_id:
            return {'statusCode': 400}
        
        # Process audio chunk
        response = asyncio.run(process_audio_chunk(
            connection_id, session_id, audio_data, is_final
        ))
        
        # Send transcription result
        if response:
            send_websocket_message(connection_id, response)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error processing audio chunk: {str(e)}")
        return {'statusCode': 500}


def handle_end_interview(connection_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """End interview session"""
    
    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('session_id')
        
        if session_id:
            # End interview session
            summary = end_interview_session(session_id, 'completed')
            
            # Send summary back
            send_websocket_message(connection_id, {
                'type': 'interview_ended',
                'session_id': session_id,
                'summary': summary
            })
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error ending interview: {str(e)}")
        return {'statusCode': 500}


async def start_interview_session(
    connection_id: str,
    user_id: str,
    interview_type: str,
    topic: str = None,
    subject_id: str = None
) -> Dict[str, Any]:
    """Start new interview session using Bedrock Agent"""
    
    try:
        # Create interview session
        session_id = str(uuid.uuid4())
        
        # TODO: Get user profile for personalization (will be implemented in Task 8)
        user_profile = {}  # Placeholder for user personalization
        
        # Start interview with Bedrock Agent
        agent_response = await agent_invoker.conduct_interview(
            user_id=user_id,
            interview_type=interview_type,
            topic=topic,
            session_id=session_id,
            user_profile=user_profile
        )
        
        if agent_response['success']:
            # Store interview session
            store_interview_session(session_id, user_id, connection_id, interview_type, topic, subject_id)
            
            # Update connection with session ID
            update_connection_session(connection_id, session_id)
            
            return {
                'session_id': session_id,
                'question': agent_response['question'],
                'metadata': agent_response.get('metadata', {})
            }
        else:
            raise Exception(f"Failed to start interview: {agent_response.get('error')}")
        
    except Exception as e:
        logger.error(f"Error starting interview session: {str(e)}")
        raise


async def process_audio_chunk(
    connection_id: str,
    session_id: str,
    audio_data: str,
    is_final: bool
) -> Dict[str, Any]:
    """Process audio chunk with AWS Transcribe"""
    
    try:
        # TODO: Implement AWS Transcribe streaming integration (will be enhanced in Task 7)
        # For now, simulate transcription
        
        if is_final:
            # Simulate transcribed text
            transcribed_text = "This is a simulated transcription of the user's speech."
            
            # Get interview session
            session_data = get_interview_session(session_id)
            if not session_data:
                return None
            
            # Get conversation history
            conversation_history = get_interview_history(session_id)
            
            # Generate AI response using Bedrock Agent
            agent_response = await agent_invoker.conduct_interview(
                user_id=session_data['user_id'],
                interview_type=session_data['interview_type'],
                topic=session_data.get('topic'),
                session_id=session_id,
                conversation_history=conversation_history
            )
            
            if agent_response['success']:
                # Store conversation turn
                store_interview_turn(session_id, transcribed_text, agent_response['question'])
                
                return {
                    'type': 'transcription_complete',
                    'transcribed_text': transcribed_text,
                    'ai_response': agent_response['question'],
                    'session_id': session_id
                }
            else:
                return {
                    'type': 'error',
                    'message': 'Failed to generate AI response'
                }
        else:
            # Interim transcription result
            return {
                'type': 'transcription_interim',
                'partial_text': "Processing audio...",
                'session_id': session_id
            }
        
    except Exception as e:
        logger.error(f"Error processing audio chunk: {str(e)}")
        return {
            'type': 'error',
            'message': 'Audio processing failed'
        }


def store_interview_session(
    session_id: str,
    user_id: str,
    connection_id: str,
    interview_type: str,
    topic: str = None,
    subject_id: str = None
):
    """Store interview session in DynamoDB"""
    
    dynamodb = boto3.resource('dynamodb')
    sessions_table = dynamodb.Table('lms-interview-sessions')
    
    session_data = {
        'session_id': session_id,
        'user_id': user_id,
        'connection_id': connection_id,
        'interview_type': interview_type,
        'topic': topic,
        'subject_id': subject_id,
        'status': 'active',
        'started_at': datetime.utcnow().isoformat(),
        'turn_count': 0,
        'bedrock_agent_used': True
    }
    
    sessions_table.put_item(Item=session_data)


def store_interview_turn(session_id: str, user_input: str, ai_response: str):
    """Store interview conversation turn"""
    
    dynamodb = boto3.resource('dynamodb')
    turns_table = dynamodb.Table('lms-interview-turns')
    sessions_table = dynamodb.Table('lms-interview-sessions')
    
    turn_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Store turn
    turn_data = {
        'turn_id': turn_id,
        'session_id': session_id,
        'timestamp': timestamp,
        'user_input': user_input,
        'ai_response': ai_response,
        'turn_number': None  # Will be set by update
    }
    
    turns_table.put_item(Item=turn_data)
    
    # Update session turn count
    sessions_table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET turn_count = turn_count + :inc, last_activity = :timestamp',
        ExpressionAttributeValues={
            ':inc': 1,
            ':timestamp': timestamp
        }
    )


def get_interview_session(session_id: str) -> Dict[str, Any]:
    """Get interview session data"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        response = sessions_table.get_item(Key={'session_id': session_id})
        return response.get('Item')
        
    except Exception as e:
        logger.error(f"Error getting interview session: {str(e)}")
        return None


def get_interview_history(session_id: str, limit: int = 10) -> list:
    """Get interview conversation history"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        turns_table = dynamodb.Table('lms-interview-turns')
        
        response = turns_table.query(
            KeyConditionExpression='session_id = :session_id',
            ExpressionAttributeValues={':session_id': session_id},
            ScanIndexForward=True,  # Chronological order
            Limit=limit
        )
        
        # Format for agent context
        history = []
        for item in response['Items']:
            history.extend([
                {'role': 'user', 'content': item['user_input']},
                {'role': 'assistant', 'content': item['ai_response']}
            ])
        
        return history
        
    except Exception as e:
        logger.warning(f"Error getting interview history: {str(e)}")
        return []


def update_connection_session(connection_id: str, session_id: str):
    """Update connection with session ID"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        connections_table = dynamodb.Table('lms-websocket-connections')
        
        connections_table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET interview_session_id = :session_id, status = :status',
            ExpressionAttributeValues={
                ':session_id': session_id,
                ':status': 'interviewing'
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating connection session: {str(e)}")


def end_interview_session(session_id: str, end_reason: str) -> Dict[str, Any]:
    """End interview session and generate summary"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        # Update session status
        sessions_table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET #status = :status, ended_at = :ended_at, end_reason = :end_reason',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':ended_at': datetime.utcnow().isoformat(),
                ':end_reason': end_reason
            }
        )
        
        # TODO: Generate interview summary using Analysis Agent (will be implemented in Task 8)
        summary = {
            'session_id': session_id,
            'end_reason': end_reason,
            'summary': 'Interview session completed. Detailed analysis will be available soon.'
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error ending interview session: {str(e)}")
        return {'error': str(e)}


def send_websocket_message(connection_id: str, message: Dict[str, Any]):
    """Send message through WebSocket"""
    
    try:
        # Get API Gateway management API endpoint
        api_gateway_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=f"https://{os.environ.get('API_GATEWAY_ID')}.execute-api.{os.environ.get('AWS_REGION')}.amazonaws.com/{os.environ.get('STAGE', 'dev')}"
        )
        
        api_gateway_management.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        
    except Exception as e:
        logger.error(f"Error sending WebSocket message: {str(e)}")
        # Connection might be closed, clean up
        try:
            dynamodb = boto3.resource('dynamodb')
            connections_table = dynamodb.Table('lms-websocket-connections')
            connections_table.delete_item(Key={'connection_id': connection_id})
        except:
            pass
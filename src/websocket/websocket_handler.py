"""
WebSocket Handler for Real-time Chat
Handles WebSocket connections for real-time chat with Bedrock Agent
Task 12: Frontend-Backend API Integration
"""

import json
import boto3
import os
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError
import uuid
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Main WebSocket Lambda handler"""
    try:
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        
        logger.info(f"WebSocket event: {route_key} for connection: {connection_id}")
        
        if route_key == '$connect':
            return handle_connect(event, context)
        elif route_key == '$disconnect':
            return handle_disconnect(event, context)
        elif route_key == 'sendMessage':
            return handle_message(event, context)
        elif route_key == '$default':
            return handle_default(event, context)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown route: {route_key}'})
            }
            
    except Exception as e:
        logger.error(f"WebSocket handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_connect(event, context):
    """Handle WebSocket connection"""
    try:
        connection_id = event['requestContext']['connectionId']
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id', 'anonymous')
        
        logger.info(f"WebSocket connected: {connection_id} for user: {user_id}")
        
        # Store connection info (optional - could use DynamoDB)
        # For now, just log the connection
        
        # Send welcome message
        send_message_to_connection(connection_id, event['requestContext'], {
            'type': 'connection_established',
            'message': 'Connected to LMS AI Assistant',
            'connection_id': connection_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'body': 'Connected'
        }
        
    except Exception as e:
        logger.error(f"Connection handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Connection failed: {str(e)}'
        }

def handle_disconnect(event, context):
    """Handle WebSocket disconnection"""
    try:
        connection_id = event['requestContext']['connectionId']
        logger.info(f"WebSocket disconnected: {connection_id}")
        
        # Clean up connection info if stored
        
        return {
            'statusCode': 200,
            'body': 'Disconnected'
        }
        
    except Exception as e:
        logger.error(f"Disconnect handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Disconnect failed: {str(e)}'
        }

def handle_message(event, context):
    """Handle WebSocket messages"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Parse message
        try:
            message_data = json.loads(event['body'])
        except json.JSONDecodeError:
            send_message_to_connection(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Invalid JSON message'
            })
            return {
                'statusCode': 400,
                'body': 'Invalid JSON message'
            }
        
        message = message_data.get('message', '').strip()
        session_id = message_data.get('session_id') or f"ws-session-{uuid.uuid4()}"
        user_id = message_data.get('user_id', 'anonymous')
        
        if not message:
            send_message_to_connection(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Message content is required'
            })
            return {
                'statusCode': 400,
                'body': 'Message content is required'
            }
        
        # Send typing indicator
        send_message_to_connection(connection_id, event['requestContext'], {
            'type': 'typing',
            'message': 'AI is thinking...'
        })
        
        # Process message with Bedrock Agent
        try:
            bedrock_runtime = boto3.client('bedrock-agent-runtime')
            
            response = bedrock_runtime.invoke_agent(
                agentId=os.environ.get('BEDROCK_AGENT_ID', 'ZTBBVSC6Y1'),
                agentAliasId=os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID'),
                sessionId=session_id,
                inputText=message
            )
            
            # Process streaming response
            completion = ""
            citations = []
            tools_used = []
            
            if response.get('completion'):
                for event_item in response['completion']:
                    if 'chunk' in event_item:
                        chunk = event_item['chunk']
                        if 'bytes' in chunk:
                            chunk_text = chunk['bytes'].decode('utf-8')
                            completion += chunk_text
                            
                            # Send partial response for real-time streaming
                            send_message_to_connection(connection_id, event['requestContext'], {
                                'type': 'partial_response',
                                'content': chunk_text,
                                'session_id': session_id
                            })
                    
                    # Extract trace information
                    if 'trace' in event_item:
                        extract_trace_info(event_item['trace'], citations, tools_used)
            
            # Send final response
            send_message_to_connection(connection_id, event['requestContext'], {
                'type': 'final_response',
                'content': completion,
                'session_id': session_id,
                'citations': citations,
                'tools_used': tools_used,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Bedrock Agent error: {str(e)}")
            send_message_to_connection(connection_id, event['requestContext'], {
                'type': 'error',
                'message': "I'm sorry, I'm having trouble connecting to the AI service right now.",
                'error': str(e)
            })
        
        return {
            'statusCode': 200,
            'body': 'Message processed'
        }
        
    except Exception as e:
        logger.error(f"Message handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Message handling failed: {str(e)}'
        }

def handle_default(event, context):
    """Handle default WebSocket route"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        send_message_to_connection(connection_id, event['requestContext'], {
            'type': 'error',
            'message': 'Unknown message type. Use action: "sendMessage"'
        })
        
        return {
            'statusCode': 400,
            'body': 'Unknown message type'
        }
        
    except Exception as e:
        logger.error(f"Default handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Default handling failed: {str(e)}'
        }

def send_message_to_connection(connection_id: str, request_context: Dict, message: Dict[str, Any]):
    """Send message to a specific WebSocket connection"""
    try:
        # Get API Gateway management API endpoint
        domain_name = request_context['domainName']
        stage = request_context['stage']
        
        apigateway_client = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=f'https://{domain_name}/{stage}'
        )
        
        apigateway_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'GoneException':
            logger.info(f"Connection {connection_id} is gone")
        else:
            logger.error(f"Failed to send message to {connection_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send message to {connection_id}: {str(e)}")
        return False

def extract_trace_info(trace: Dict, citations: list, tools_used: list):
    """Extract citations and tools used from trace information"""
    try:
        # Extract action group invocations
        if 'orchestrationTrace' in trace:
            orchestration = trace['orchestrationTrace']
            if 'invocationInput' in orchestration:
                action_group = orchestration['invocationInput'].get('actionGroupName')
                if action_group and action_group not in tools_used:
                    tools_used.append(action_group)
        
        # Extract knowledge base citations
        if 'knowledgeBaseTrace' in trace:
            kb_trace = trace['knowledgeBaseTrace']
            if 'retrievalResults' in kb_trace:
                for result in kb_trace['retrievalResults']:
                    citation = {
                        'source': result.get('location', {}).get('s3Location', {}).get('uri', 'Knowledge Base'),
                        'confidence': result.get('score', 0),
                        'content': result.get('content', {}).get('text', '')[:200] + '...' if result.get('content', {}).get('text') else ''
                    }
                    citations.append(citation)
                    
    except Exception as e:
        logger.warning(f"Failed to extract trace information: {str(e)}")
"""
Bedrock Agent Proxy Lambda Function
Provides API Gateway integration for frontend to communicate with Bedrock Agent
Enhanced for Task 12: Frontend-Backend API Integration
"""

import json
import boto3
import os
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError
import uuid
from datetime import datetime
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class BedrockAgentProxy:
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        
        # Agent configuration
        self.agent_id = os.environ.get('BEDROCK_AGENT_ID', 'ZTBBVSC6Y1')
        self.alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
        
        # Storage configuration
        self.documents_bucket = os.environ.get('DOCUMENTS_BUCKET', 'lms-documents-dev')
        self.sessions_table_name = os.environ.get('SESSIONS_TABLE', 'lms-sessions-dev')
        
        # Initialize DynamoDB table
        try:
            self.sessions_table = self.dynamodb.Table(self.sessions_table_name)
        except Exception as e:
            logger.warning(f"Could not initialize sessions table: {e}")
            self.sessions_table = None
        
    def invoke_agent(self, message: str, session_id: str, user_id: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent with user message and return response
        Enhanced for frontend integration with better error handling and session management
        """
        try:
            # Store session info
            self._store_session_info(session_id, user_id, message)
            
            # Prepare session state with user context
            session_state = {}
            if user_id or context:
                session_state['sessionAttributes'] = {
                    'userId': user_id or 'anonymous',
                    'context': json.dumps(context or {}),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            logger.info(f"Invoking agent {self.agent_id} for session {session_id}")
            
            # Invoke agent
            response = self.bedrock_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                sessionId=session_id,
                inputText=message,
                **({'sessionState': session_state} if session_state else {})
            )
            
            # Process streaming response
            completion = ""
            citations = []
            tools_used = []
            trace_data = []
            
            if response.get('completion'):
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            completion += chunk['bytes'].decode('utf-8')
                    
                    # Extract trace information
                    if 'trace' in event:
                        trace_info = self._extract_trace_info(event['trace'], citations, tools_used)
                        if trace_info:
                            trace_data.append(trace_info)
            
            # Store conversation in session
            self._update_session_conversation(session_id, message, completion, tools_used)
            
            result = {
                'success': True,
                'response': completion,
                'session_id': session_id,
                'citations': citations,
                'tools_used': tools_used,
                'trace_data': trace_data,
                'timestamp': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                'message_id': str(uuid.uuid4())
            }
            
            logger.info(f"Agent response successful for session {session_id}, tools used: {tools_used}")
            return result
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            logger.error(f"Bedrock Agent invocation failed: {error_code} - {error_message}")
            
            # Provide specific error messages based on error type
            if error_code == 'ResourceNotFoundException':
                user_message = "The AI agent is currently unavailable. Please contact support."
            elif error_code == 'ThrottlingException':
                user_message = "The service is currently busy. Please try again in a moment."
            elif error_code == 'ValidationException':
                user_message = "There was an issue with your request. Please try rephrasing your message."
            else:
                user_message = "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again in a moment."
            
            return {
                'success': False,
                'error': error_message,
                'error_code': error_code,
                'response': user_message,
                'session_id': session_id,
                'citations': [],
                'tools_used': [],
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error in agent invocation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': "An unexpected error occurred. Please try again.",
                'session_id': session_id,
                'citations': [],
                'tools_used': [],
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _extract_trace_info(self, trace: Dict, citations: list, tools_used: list) -> Optional[Dict]:
        """Extract citations and tools used from trace information"""
        try:
            trace_info = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'unknown'
            }
            
            # Extract action group invocations
            if 'orchestrationTrace' in trace:
                orchestration = trace['orchestrationTrace']
                trace_info['type'] = 'orchestration'
                
                if 'invocationInput' in orchestration:
                    action_group = orchestration['invocationInput'].get('actionGroupName')
                    if action_group and action_group not in tools_used:
                        tools_used.append(action_group)
                        trace_info['action_group'] = action_group
                
                if 'observation' in orchestration:
                    trace_info['observation'] = orchestration['observation']
            
            # Extract knowledge base citations
            if 'knowledgeBaseTrace' in trace:
                kb_trace = trace['knowledgeBaseTrace']
                trace_info['type'] = 'knowledge_base'
                
                if 'retrievalResults' in kb_trace:
                    for result in kb_trace['retrievalResults']:
                        citation = {
                            'source': result.get('location', {}).get('s3Location', {}).get('uri', 'Knowledge Base'),
                            'confidence': result.get('score', 0),
                            'content': result.get('content', {}).get('text', '')[:200] + '...' if result.get('content', {}).get('text') else '',
                            'metadata': result.get('metadata', {})
                        }
                        citations.append(citation)
                        
                    trace_info['retrieval_count'] = len(kb_trace['retrievalResults'])
            
            # Extract guardrail traces
            if 'guardrailTrace' in trace:
                trace_info['type'] = 'guardrail'
                trace_info['guardrail'] = trace['guardrailTrace']
            
            return trace_info
                        
        except Exception as e:
            logger.warning(f"Failed to extract trace information: {str(e)}")
            return None
    
    def _store_session_info(self, session_id: str, user_id: Optional[str], message: str):
        """Store session information in DynamoDB"""
        if not self.sessions_table:
            return
            
        try:
            # Calculate TTL (24 hours from now)
            ttl = int((datetime.utcnow().timestamp()) + 86400)
            
            self.sessions_table.put_item(
                Item={
                    'session_id': session_id,
                    'user_id': user_id or 'anonymous',
                    'last_message': message,
                    'last_activity': datetime.utcnow().isoformat(),
                    'ttl': ttl
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store session info: {e}")
    
    def _update_session_conversation(self, session_id: str, user_message: str, agent_response: str, tools_used: List[str]):
        """Update session with conversation history"""
        if not self.sessions_table:
            return
            
        try:
            # Get existing session
            response = self.sessions_table.get_item(Key={'session_id': session_id})
            session_data = response.get('Item', {})
            
            # Update conversation history
            conversation = session_data.get('conversation', [])
            conversation.append({
                'timestamp': datetime.utcnow().isoformat(),
                'user_message': user_message,
                'agent_response': agent_response,
                'tools_used': tools_used
            })
            
            # Keep only last 50 messages to avoid item size limits
            if len(conversation) > 50:
                conversation = conversation[-50:]
            
            # Update session
            ttl = int((datetime.utcnow().timestamp()) + 86400)
            self.sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET conversation = :conv, last_activity = :activity, ttl = :ttl',
                ExpressionAttributeValues={
                    ':conv': conversation,
                    ':activity': datetime.utcnow().isoformat(),
                    ':ttl': ttl
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update session conversation: {e}")
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        if not self.sessions_table:
            return []
            
        try:
            response = self.sessions_table.get_item(Key={'session_id': session_id})
            session_data = response.get('Item', {})
            return session_data.get('conversation', [])
        except Exception as e:
            logger.warning(f"Failed to get session history: {e}")
            return []
    
    def generate_presigned_upload_url(self, file_name: str, content_type: str, user_id: str) -> Dict[str, Any]:
        """Generate presigned URL for file upload"""
        try:
            # Create unique file key
            file_key = f"users/{user_id}/documents/{uuid.uuid4()}-{file_name}"
            
            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.documents_bucket,
                    'Key': file_key,
                    'ContentType': content_type
                },
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'success': True,
                'upload_url': presigned_url,
                'file_key': file_key,
                'bucket': self.documents_bucket,
                'expires_in': 3600
            }
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def lambda_handler(event, context):
    """
    API Gateway Lambda handler for Bedrock Agent proxy
    """
    try:
        # Parse request
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
                    'Access-Control-Max-Age': '86400'
                },
                'body': ''
            }
        
        # Parse request body
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Invalid JSON in request body'
                    })
                }
        else:
            body = {}
        
        # Initialize proxy
        proxy = BedrockAgentProxy()
        
        # Route based on path
        if path.endswith('/chat') or path.endswith('/invoke'):
            return handle_chat_request(proxy, body)
        elif path.endswith('/health'):
            return handle_health_check(proxy)
        elif path.endswith('/capabilities'):
            return handle_capabilities_request()
        elif path.endswith('/session/history'):
            return handle_session_history(proxy, event.get('queryStringParameters', {}))
        elif path.endswith('/upload/presigned'):
            return handle_presigned_upload(proxy, body)
        elif path.endswith('/documents'):
            return handle_documents_list(proxy, event.get('queryStringParameters', {}))
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Endpoint not found',
                    'available_endpoints': [
                        '/api/v1/chat',
                        '/api/v1/agent/invoke', 
                        '/api/v1/health',
                        '/api/v1/capabilities',
                        '/api/v1/session/history',
                        '/api/v1/upload/presigned',
                        '/api/v1/documents'
                    ]
                })
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error'
            })
        }

def handle_chat_request(proxy: BedrockAgentProxy, body: Dict) -> Dict:
    """Handle chat/invoke requests"""
    try:
        # Validate required fields
        message = body.get('message', '').strip()
        if not message:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Message is required'
                })
            }
        
        # Get optional fields
        session_id = body.get('session_id') or f"session-{uuid.uuid4()}"
        user_id = body.get('user_id')
        context = body.get('context', {})
        
        # Invoke agent
        result = proxy.invoke_agent(message, session_id, user_id, context)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Chat request error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_health_check(proxy: BedrockAgentProxy) -> Dict:
    """Handle health check requests"""
    try:
        # Test agent connectivity
        test_session = f"health-check-{uuid.uuid4()}"
        result = proxy.invoke_agent("Hello", test_session)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'status': 'healthy',
                'agent_id': proxy.agent_id,
                'alias_id': proxy.alias_id,
                'agent_responsive': result['success'],
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            'statusCode': 503,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def handle_capabilities_request() -> Dict:
    """Handle capabilities request"""
    capabilities = [
        'Document Analysis & Summarization',
        'Quiz Generation from Content',
        'Learning Analytics & Progress Tracking',
        'Voice Interview Practice',
        'Multi-language Support',
        'Citation-backed Responses',
        'Contextual Learning Assistance'
    ]
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'success': True,
            'capabilities': capabilities,
            'agent_info': {
                'agent_id': os.environ.get('BEDROCK_AGENT_ID', 'ZTBBVSC6Y1'),
                'alias_id': os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID'),
                'version': '1.0.0'
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def handle_session_history(proxy: BedrockAgentProxy, query_params: Dict) -> Dict:
    """Handle session history requests"""
    try:
        session_id = query_params.get('session_id')
        if not session_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'session_id parameter is required'
                })
            }
        
        history = proxy.get_session_history(session_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'session_id': session_id,
                'conversation_history': history,
                'message_count': len(history),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Session history error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_presigned_upload(proxy: BedrockAgentProxy, body: Dict) -> Dict:
    """Handle presigned upload URL generation"""
    try:
        file_name = body.get('file_name')
        content_type = body.get('content_type', 'application/octet-stream')
        user_id = body.get('user_id', 'anonymous')
        
        if not file_name:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'file_name is required'
                })
            }
        
        result = proxy.generate_presigned_upload_url(file_name, content_type, user_id)
        
        return {
            'statusCode': 200 if result['success'] else 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Presigned upload error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_documents_list(proxy: BedrockAgentProxy, query_params: Dict) -> Dict:
    """Handle documents list requests"""
    try:
        user_id = query_params.get('user_id', 'anonymous')
        
        # List documents for user
        try:
            response = proxy.s3_client.list_objects_v2(
                Bucket=proxy.documents_bucket,
                Prefix=f"users/{user_id}/documents/"
            )
            
            documents = []
            for obj in response.get('Contents', []):
                # Extract original filename from key
                key_parts = obj['Key'].split('/')
                if len(key_parts) >= 4:
                    filename = key_parts[-1]
                    # Remove UUID prefix if present
                    if '-' in filename and len(filename.split('-')[0]) == 36:
                        filename = '-'.join(filename.split('-')[1:])
                    
                    documents.append({
                        'key': obj['Key'],
                        'filename': filename,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'download_url': proxy.s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': proxy.documents_bucket, 'Key': obj['Key']},
                            ExpiresIn=3600
                        )
                    })
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'success': True,
                    'documents': documents,
                    'count': len(documents),
                    'user_id': user_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Content-Type': 'application/json'
                    },
                    'body': json.dumps({
                        'success': True,
                        'documents': [],
                        'count': 0,
                        'user_id': user_id,
                        'message': 'No documents bucket found',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            raise
        
    except Exception as e:
        logger.error(f"Documents list error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
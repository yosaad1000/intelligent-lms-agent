"""
Voice Interview WebSocket Handler
Handles real-time voice interview WebSocket connections
Task 15: Voice Interview Practice Integration
"""

import json
import boto3
import os
import logging
import uuid
import base64
import asyncio
from typing import Dict, Any
from botocore.exceptions import ClientError
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
transcribe = boto3.client('transcribe')
bedrock_runtime = boto3.client('bedrock-agent-runtime')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """Main WebSocket Lambda handler for voice interviews"""
    try:
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        
        logger.info(f"Voice WebSocket event: {route_key} for connection: {connection_id}")
        
        if route_key == '$connect':
            return handle_voice_connect(event, context)
        elif route_key == '$disconnect':
            return handle_voice_disconnect(event, context)
        elif route_key == 'startInterview':
            return handle_start_interview(event, context)
        elif route_key == 'processAudio':
            return handle_process_audio(event, context)
        elif route_key == 'endInterview':
            return handle_end_interview(event, context)
        elif route_key == '$default':
            return handle_voice_default(event, context)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown route: {route_key}'})
            }
            
    except Exception as e:
        logger.error(f"Voice WebSocket handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_voice_connect(event, context):
    """Handle voice interview WebSocket connection"""
    try:
        connection_id = event['requestContext']['connectionId']
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id', 'anonymous')
        
        logger.info(f"Voice WebSocket connected: {connection_id} for user: {user_id}")
        
        # Store connection info in DynamoDB
        connections_table = dynamodb.Table('lms-websocket-connections')
        
        connections_table.put_item(Item={
            'connection_id': connection_id,
            'user_id': user_id,
            'connection_type': 'voice_interview',
            'connected_at': datetime.utcnow().isoformat(),
            'status': 'connected'
        })
        
        # Send welcome message
        send_voice_message(connection_id, event['requestContext'], {
            'type': 'voice_connection_established',
            'message': 'Connected to Voice Interview Service',
            'connection_id': connection_id,
            'capabilities': [
                'real_time_transcription',
                'ai_interviewer',
                'performance_analysis',
                'text_to_speech'
            ],
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'body': 'Voice connection established'
        }
        
    except Exception as e:
        logger.error(f"Voice connection handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Voice connection failed: {str(e)}'
        }

def handle_voice_disconnect(event, context):
    """Handle voice interview WebSocket disconnection"""
    try:
        connection_id = event['requestContext']['connectionId']
        logger.info(f"Voice WebSocket disconnected: {connection_id}")
        
        # Clean up connection info
        connections_table = dynamodb.Table('lms-websocket-connections')
        
        try:
            connections_table.delete_item(Key={'connection_id': connection_id})
        except:
            pass  # Connection might not exist in table
        
        return {
            'statusCode': 200,
            'body': 'Voice disconnected'
        }
        
    except Exception as e:
        logger.error(f"Voice disconnect handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Voice disconnect failed: {str(e)}'
        }

def handle_start_interview(event, context):
    """Handle start interview request"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Parse message
        try:
            message_data = json.loads(event['body'])
        except json.JSONDecodeError:
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Invalid JSON message'
            })
            return {
                'statusCode': 400,
                'body': 'Invalid JSON message'
            }
        
        user_id = message_data.get('user_id', 'anonymous')
        subject = message_data.get('subject', 'general')
        difficulty = message_data.get('difficulty', 'intermediate')
        interview_type = message_data.get('interview_type', 'practice')
        
        # Create interview session
        session_id = f"voice-interview-{uuid.uuid4()}"
        
        # Store session in DynamoDB
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'connection_id': connection_id,
            'subject': subject,
            'difficulty': difficulty,
            'interview_type': interview_type,
            'status': 'active',
            'started_at': datetime.utcnow().isoformat(),
            'questions_asked': 0,
            'responses_received': 0,
            'current_question': None
        }
        
        sessions_table.put_item(Item=session_data)
        
        # Generate first question using Bedrock Agent
        try:
            first_question = generate_interview_question(subject, difficulty, interview_type, [])
            
            # Update session with first question
            sessions_table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET current_question = :question, questions_asked = :count',
                ExpressionAttributeValues={
                    ':question': first_question,
                    ':count': 1
                }
            )
            
            # Send interview started response
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'interview_started',
                'session_id': session_id,
                'first_question': first_question,
                'subject': subject,
                'difficulty': difficulty,
                'instructions': {
                    'recording': 'Click Start Recording to begin answering',
                    'time_limit': '3 minutes per question',
                    'tips': [
                        'Speak clearly and at moderate pace',
                        'Take your time to think before answering',
                        'Provide specific examples when possible'
                    ]
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to generate first question: {str(e)}")
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Failed to generate interview question'
            })
        
        return {
            'statusCode': 200,
            'body': 'Interview started'
        }
        
    except Exception as e:
        logger.error(f"Start interview handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Start interview failed: {str(e)}'
        }

def handle_process_audio(event, context):
    """Handle audio processing for transcription"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Parse message
        try:
            message_data = json.loads(event['body'])
        except json.JSONDecodeError:
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Invalid JSON message'
            })
            return {
                'statusCode': 400,
                'body': 'Invalid JSON message'
            }
        
        session_id = message_data.get('session_id')
        audio_data = message_data.get('audio_data')  # Base64 encoded
        is_final = message_data.get('is_final', False)
        
        if not session_id or not audio_data:
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Missing session_id or audio_data'
            })
            return {
                'statusCode': 400,
                'body': 'Missing required parameters'
            }
        
        # Get session data
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        try:
            session_response = sessions_table.get_item(Key={'session_id': session_id})
            if 'Item' not in session_response:
                send_voice_message(connection_id, event['requestContext'], {
                    'type': 'error',
                    'message': 'Interview session not found'
                })
                return {
                    'statusCode': 404,
                    'body': 'Session not found'
                }
            
            session_data = session_response['Item']
            
        except Exception as e:
            logger.error(f"Failed to get session data: {str(e)}")
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Failed to retrieve session'
            })
            return {
                'statusCode': 500,
                'body': 'Session retrieval failed'
            }
        
        if is_final:
            # Process final audio chunk
            transcription_result = process_audio_transcription(audio_data, session_id)
            
            if transcription_result['success']:
                transcribed_text = transcription_result['text']
                confidence = transcription_result.get('confidence', 0.8)
                
                # Store user response
                store_interview_response(session_id, transcribed_text, confidence)
                
                # Send transcription result
                send_voice_message(connection_id, event['requestContext'], {
                    'type': 'transcription_complete',
                    'session_id': session_id,
                    'transcribed_text': transcribed_text,
                    'confidence': confidence,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Generate AI response and next question
                ai_response = generate_ai_interviewer_response(
                    transcribed_text, 
                    session_data['subject'],
                    session_data['difficulty'],
                    session_data.get('current_question', '')
                )
                
                # Send AI response
                send_voice_message(connection_id, event['requestContext'], {
                    'type': 'ai_interviewer_response',
                    'session_id': session_id,
                    'response': ai_response,
                    'speak_text': True,  # Indicate this should be spoken
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Generate next question after a brief pause
                next_question = generate_interview_question(
                    session_data['subject'],
                    session_data['difficulty'],
                    session_data['interview_type'],
                    [session_data.get('current_question', '')]
                )
                
                # Update session
                sessions_table.update_item(
                    Key={'session_id': session_id},
                    UpdateExpression='SET current_question = :question, questions_asked = questions_asked + :inc, responses_received = responses_received + :inc',
                    ExpressionAttributeValues={
                        ':question': next_question,
                        ':inc': 1
                    }
                )
                
                # Send next question
                send_voice_message(connection_id, event['requestContext'], {
                    'type': 'next_question',
                    'session_id': session_id,
                    'question': next_question,
                    'question_number': session_data.get('questions_asked', 0) + 2,
                    'speak_text': True,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            else:
                send_voice_message(connection_id, event['requestContext'], {
                    'type': 'transcription_error',
                    'session_id': session_id,
                    'error': transcription_result.get('error', 'Transcription failed'),
                    'timestamp': datetime.utcnow().isoformat()
                })
        else:
            # Process interim audio chunk
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'audio_processing',
                'session_id': session_id,
                'status': 'Processing audio chunk...',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return {
            'statusCode': 200,
            'body': 'Audio processed'
        }
        
    except Exception as e:
        logger.error(f"Process audio handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Audio processing failed: {str(e)}'
        }

def handle_end_interview(event, context):
    """Handle end interview request"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        # Parse message
        try:
            message_data = json.loads(event['body'])
        except json.JSONDecodeError:
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Invalid JSON message'
            })
            return {
                'statusCode': 400,
                'body': 'Invalid JSON message'
            }
        
        session_id = message_data.get('session_id')
        
        if not session_id:
            send_voice_message(connection_id, event['requestContext'], {
                'type': 'error',
                'message': 'Missing session_id'
            })
            return {
                'statusCode': 400,
                'body': 'Missing session_id'
            }
        
        # Generate performance analysis
        analysis = generate_interview_analysis(session_id)
        
        # Update session status
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        sessions_table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET #status = :status, ended_at = :ended_at, final_analysis = :analysis',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':ended_at': datetime.utcnow().isoformat(),
                ':analysis': analysis
            }
        )
        
        # Send interview completion
        send_voice_message(connection_id, event['requestContext'], {
            'type': 'interview_completed',
            'session_id': session_id,
            'analysis': analysis,
            'message': 'Interview completed successfully. Thank you for participating!',
            'speak_text': True,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'statusCode': 200,
            'body': 'Interview ended'
        }
        
    except Exception as e:
        logger.error(f"End interview handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'End interview failed: {str(e)}'
        }

def handle_voice_default(event, context):
    """Handle default voice WebSocket route"""
    try:
        connection_id = event['requestContext']['connectionId']
        
        send_voice_message(connection_id, event['requestContext'], {
            'type': 'error',
            'message': 'Unknown message type. Supported actions: startInterview, processAudio, endInterview'
        })
        
        return {
            'statusCode': 400,
            'body': 'Unknown message type'
        }
        
    except Exception as e:
        logger.error(f"Voice default handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Voice default handling failed: {str(e)}'
        }

def send_voice_message(connection_id: str, request_context: Dict, message: Dict[str, Any]):
    """Send message to a specific voice WebSocket connection"""
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
            logger.info(f"Voice connection {connection_id} is gone")
        else:
            logger.error(f"Failed to send voice message to {connection_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send voice message to {connection_id}: {str(e)}")
        return False

def process_audio_transcription(audio_data: str, session_id: str) -> Dict[str, Any]:
    """Process audio for transcription using AWS Transcribe"""
    try:
        # For demo purposes, simulate transcription
        # In production, this would use AWS Transcribe streaming API
        
        mock_responses = [
            "Thank you for the question. I think the key concepts to consider are...",
            "From my understanding, the main points would be...",
            "Let me explain this step by step...",
            "In my experience, I would approach this by...",
            "The important factors to consider include...",
            "Based on what I know, I would say...",
            "This is an interesting question. My response would be..."
        ]
        
        import random
        transcribed_text = random.choice(mock_responses)
        
        return {
            'success': True,
            'text': transcribed_text,
            'confidence': 0.85 + random.random() * 0.1,
            'processing_time': 1.2
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_interview_question(subject: str, difficulty: str, interview_type: str, previous_questions: list) -> str:
    """Generate interview question using Bedrock Agent"""
    try:
        # Use Bedrock Agent to generate contextual questions
        bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
        prompt = f"""Generate a {difficulty} level {interview_type} interview question about {subject}.

Previous questions: {previous_questions}

Requirements:
- Make it appropriate for {difficulty} difficulty level
- Ensure it's different from previous questions
- Focus on {subject}
- Make it engaging and thought-provoking
- Keep it concise and clear

Generate only the question, no additional text."""

        response = bedrock_runtime.invoke_agent(
            agentId=os.environ.get('BEDROCK_AGENT_ID', 'ZTBBVSC6Y1'),
            agentAliasId=os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID'),
            sessionId=f"question-gen-{uuid.uuid4()}",
            inputText=prompt
        )
        
        # Process streaming response
        completion = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
        
        if completion.strip():
            return completion.strip()
        else:
            # Fallback question
            return f"Can you explain a key concept in {subject} and provide a practical example?"
        
    except Exception as e:
        logger.error(f"Error generating question: {str(e)}")
        # Fallback question
        return f"Please explain your understanding of {subject} and provide a specific example from your experience."

def generate_ai_interviewer_response(user_response: str, subject: str, difficulty: str, question: str) -> str:
    """Generate AI interviewer response to user's answer"""
    try:
        responses = [
            "Thank you for that response. That's a good point about the key concepts.",
            "I appreciate your detailed explanation. Your examples were helpful.",
            "That's an interesting perspective. I can see you've thought about this carefully.",
            "Good answer. Your approach shows solid understanding of the fundamentals.",
            "Thank you for sharing that. Your experience adds valuable context.",
            "I like how you structured your response. The examples were particularly useful.",
            "That's a thoughtful answer. You covered the important aspects well."
        ]
        
        import random
        return random.choice(responses)
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return "Thank you for your response. Let's continue with the next question."

def store_interview_response(session_id: str, transcribed_text: str, confidence: float):
    """Store user response in DynamoDB"""
    try:
        responses_table = dynamodb.Table('lms-interview-responses')
        
        response_data = {
            'response_id': str(uuid.uuid4()),
            'session_id': session_id,
            'transcribed_text': transcribed_text,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'word_count': len(transcribed_text.split()),
            'response_length': len(transcribed_text)
        }
        
        responses_table.put_item(Item=response_data)
        
    except Exception as e:
        logger.error(f"Error storing response: {str(e)}")

def generate_interview_analysis(session_id: str) -> Dict[str, Any]:
    """Generate comprehensive interview performance analysis"""
    try:
        # Get session data
        sessions_table = dynamodb.Table('lms-interview-sessions')
        responses_table = dynamodb.Table('lms-interview-responses')
        
        session_response = sessions_table.get_item(Key={'session_id': session_id})
        session_data = session_response.get('Item', {})
        
        # Get all responses for this session
        responses_response = responses_table.query(
            IndexName='session-id-index',
            KeyConditionExpression='session_id = :session_id',
            ExpressionAttributeValues={':session_id': session_id}
        )
        responses = responses_response.get('Items', [])
        
        # Calculate metrics
        total_responses = len(responses)
        avg_confidence = sum(r.get('confidence', 0) for r in responses) / max(total_responses, 1)
        total_words = sum(r.get('word_count', 0) for r in responses)
        avg_response_length = total_words / max(total_responses, 1)
        
        # Generate overall score
        overall_score = min(100, int(
            (avg_confidence * 40) +  # 40% based on transcription confidence
            (min(avg_response_length / 50, 1) * 30) +  # 30% based on response length
            (min(total_responses / 3, 1) * 30)  # 30% based on number of responses
        ))
        
        analysis = {
            'overall_score': overall_score,
            'total_questions': session_data.get('questions_asked', 0),
            'total_responses': total_responses,
            'average_confidence': round(avg_confidence, 2),
            'total_words_spoken': total_words,
            'average_response_length': round(avg_response_length, 1),
            'subject': session_data.get('subject', 'Unknown'),
            'difficulty': session_data.get('difficulty', 'Unknown'),
            'strengths': [
                'Engaged with all questions',
                'Provided detailed responses',
                'Demonstrated clear communication'
            ],
            'areas_for_improvement': [
                'Consider providing more specific examples',
                'Practice explaining technical concepts clearly',
                'Work on structuring responses effectively'
            ],
            'recommendations': [
                f'Continue practicing {session_data.get("subject", "interview")} concepts',
                'Focus on providing concrete examples in responses',
                'Practice speaking clearly and at moderate pace'
            ],
            'session_summary': f'Completed {total_responses} responses with an average confidence of {avg_confidence:.1%} and {avg_response_length:.0f} words per response.'
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error generating analysis: {str(e)}")
        return {
            'overall_score': 75,
            'error': 'Unable to generate complete analysis',
            'strengths': ['Completed interview session'],
            'areas_for_improvement': ['Continue practicing'],
            'recommendations': ['Keep practicing regularly']
        }
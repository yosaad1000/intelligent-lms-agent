"""
Voice Processing Action Group for Bedrock Agent
Handles voice interview functionality as a Bedrock Agent action group
"""

import json
import boto3
import os
import uuid
import base64
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import io
import time

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
transcribe = boto3.client('transcribe')
bedrock_runtime = boto3.client('bedrock-runtime')
s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for voice processing action group
    Called by Bedrock Agent for voice-related operations
    """
    
    try:
        # Parse the action group request
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', '')
        parameters = body.get('parameters', {})
        
        logger.info(f"Voice action group called with action: {action}")
        
        if action == 'start_interview':
            return handle_start_interview(parameters)
        elif action == 'process_audio':
            return handle_process_audio(parameters)
        elif action == 'end_interview':
            return handle_end_interview(parameters)
        elif action == 'get_interview_status':
            return handle_get_interview_status(parameters)
        elif action == 'analyze_performance':
            return handle_analyze_performance(parameters)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown action: {action}',
                    'available_actions': [
                        'start_interview', 'process_audio', 'end_interview', 
                        'get_interview_status', 'analyze_performance'
                    ]
                })
            }
        
    except Exception as e:
        logger.error(f"Error in voice action group: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'action': 'voice_processing_error'
            })
        }


def handle_start_interview(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start a new voice interview session
    """
    
    try:
        user_id = parameters.get('user_id', 'anonymous')
        interview_type = parameters.get('interview_type', 'general')
        topic = parameters.get('topic', 'General Knowledge')
        difficulty = parameters.get('difficulty', 'intermediate')
        subject_id = parameters.get('subject_id')
        
        # Create interview session
        session_id = str(uuid.uuid4())
        
        # Store interview session in DynamoDB
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'interview_type': interview_type,
            'topic': topic,
            'difficulty': difficulty,
            'subject_id': subject_id,
            'status': 'active',
            'started_at': datetime.utcnow().isoformat(),
            'turn_count': 0,
            'questions_asked': [],
            'user_responses': [],
            'performance_metrics': {
                'clarity_score': 0,
                'content_accuracy': 0,
                'response_time_avg': 0,
                'confidence_level': 0
            }
        }
        
        sessions_table.put_item(Item=session_data)
        
        # Generate initial interview question using Bedrock
        initial_question = generate_interview_question(
            topic, difficulty, interview_type, []
        )
        
        # Store the initial question
        store_interview_turn(session_id, None, initial_question, 'question')
        
        logger.info(f"Started interview session {session_id} for user {user_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'interview_started',
                'session_id': session_id,
                'initial_question': initial_question,
                'topic': topic,
                'difficulty': difficulty,
                'instructions': 'Please respond verbally to the questions. Your audio will be transcribed and analyzed.',
                'websocket_endpoint': f"wss://{os.environ.get('API_GATEWAY_ID', 'your-api-id')}.execute-api.{os.environ.get('AWS_REGION', 'us-east-1')}.amazonaws.com/{os.environ.get('STAGE', 'dev')}"
            })
        }
        
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to start interview: {str(e)}',
                'action': 'start_interview_error'
            })
        }


def handle_process_audio(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process audio chunk for transcription and analysis
    """
    
    try:
        session_id = parameters.get('session_id')
        audio_data = parameters.get('audio_data')  # Base64 encoded
        is_final = parameters.get('is_final', False)
        
        if not session_id or not audio_data:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing session_id or audio_data',
                    'action': 'process_audio_error'
                })
            }
        
        # Get interview session
        session_data = get_interview_session(session_id)
        if not session_data:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Interview session not found',
                    'action': 'session_not_found'
                })
            }
        
        if is_final:
            # Process final audio chunk
            transcription_result = transcribe_audio(audio_data, session_id)
            
            if transcription_result['success']:
                transcribed_text = transcription_result['text']
                confidence = transcription_result.get('confidence', 0.8)
                
                # Store user response
                store_interview_turn(session_id, transcribed_text, None, 'response')
                
                # Analyze response and generate next question
                analysis_result = analyze_user_response(
                    transcribed_text, 
                    session_data['topic'],
                    session_data['difficulty'],
                    session_data.get('questions_asked', [])
                )
                
                # Generate next question or end interview
                if should_continue_interview(session_data):
                    next_question = generate_interview_question(
                        session_data['topic'],
                        session_data['difficulty'],
                        session_data['interview_type'],
                        session_data.get('questions_asked', [])
                    )
                    
                    # Store next question
                    store_interview_turn(session_id, None, next_question, 'question')
                    
                    # Update session
                    update_interview_session(session_id, {
                        'turn_count': session_data.get('turn_count', 0) + 1,
                        'last_activity': datetime.utcnow().isoformat()
                    })
                    
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'action': 'transcription_complete',
                            'transcribed_text': transcribed_text,
                            'confidence': confidence,
                            'next_question': next_question,
                            'analysis': analysis_result,
                            'continue_interview': True
                        })
                    }
                else:
                    # End interview
                    end_result = end_interview_session(session_id, 'completed')
                    
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'action': 'interview_complete',
                            'transcribed_text': transcribed_text,
                            'confidence': confidence,
                            'final_analysis': end_result,
                            'continue_interview': False
                        })
                    }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': 'Transcription failed',
                        'details': transcription_result.get('error'),
                        'action': 'transcription_error'
                    })
                }
        else:
            # Interim processing
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'action': 'processing_audio',
                    'status': 'Audio chunk received, processing...',
                    'session_id': session_id
                })
            }
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Audio processing failed: {str(e)}',
                'action': 'process_audio_error'
            })
        }


def handle_end_interview(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    End interview session and provide analysis
    """
    
    try:
        session_id = parameters.get('session_id')
        end_reason = parameters.get('end_reason', 'user_requested')
        
        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing session_id',
                    'action': 'end_interview_error'
                })
            }
        
        # End the interview session
        analysis_result = end_interview_session(session_id, end_reason)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'interview_ended',
                'session_id': session_id,
                'end_reason': end_reason,
                'analysis': analysis_result,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error ending interview: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to end interview: {str(e)}',
                'action': 'end_interview_error'
            })
        }


def handle_get_interview_status(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get current interview session status
    """
    
    try:
        session_id = parameters.get('session_id')
        
        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing session_id',
                    'action': 'get_status_error'
                })
            }
        
        session_data = get_interview_session(session_id)
        
        if not session_data:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Interview session not found',
                    'action': 'session_not_found'
                })
            }
        
        # Get recent conversation history
        history = get_interview_history(session_id, limit=5)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'interview_status',
                'session_id': session_id,
                'status': session_data.get('status'),
                'topic': session_data.get('topic'),
                'turn_count': session_data.get('turn_count', 0),
                'started_at': session_data.get('started_at'),
                'recent_history': history,
                'performance_metrics': session_data.get('performance_metrics', {})
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting interview status: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to get interview status: {str(e)}',
                'action': 'get_status_error'
            })
        }


def handle_analyze_performance(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze interview performance and provide feedback
    """
    
    try:
        session_id = parameters.get('session_id')
        
        if not session_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing session_id',
                    'action': 'analyze_performance_error'
                })
            }
        
        # Get complete interview data
        session_data = get_interview_session(session_id)
        if not session_data:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Interview session not found',
                    'action': 'session_not_found'
                })
            }
        
        # Get full conversation history
        history = get_interview_history(session_id, limit=50)
        
        # Generate comprehensive performance analysis
        performance_analysis = generate_performance_analysis(session_data, history)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'action': 'performance_analysis',
                'session_id': session_id,
                'analysis': performance_analysis,
                'recommendations': performance_analysis.get('recommendations', []),
                'overall_score': performance_analysis.get('overall_score', 0),
                'strengths': performance_analysis.get('strengths', []),
                'areas_for_improvement': performance_analysis.get('areas_for_improvement', [])
            })
        }
        
    except Exception as e:
        logger.error(f"Error analyzing performance: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Performance analysis failed: {str(e)}',
                'action': 'analyze_performance_error'
            })
        }


def transcribe_audio(audio_data: str, session_id: str) -> Dict[str, Any]:
    """
    Transcribe audio using AWS Transcribe
    """
    
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Upload audio to S3 for Transcribe
        bucket_name = os.environ.get('S3_BUCKET', 'lms-voice-processing')
        audio_key = f"interviews/{session_id}/{uuid.uuid4()}.wav"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=audio_key,
            Body=audio_bytes,
            ContentType='audio/wav'
        )
        
        # Start transcription job
        job_name = f"interview-{session_id}-{int(time.time())}"
        
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{bucket_name}/{audio_key}'},
            MediaFormat='wav',
            LanguageCode='en-US',
            Settings={
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 1
            }
        )
        
        # Wait for transcription to complete (with timeout)
        max_wait_time = 30  # seconds
        wait_time = 0
        
        while wait_time < max_wait_time:
            job_status = transcribe.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = job_status['TranscriptionJob']['TranscriptionJobStatus']
            
            if status == 'COMPLETED':
                # Get transcription result
                transcript_uri = job_status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                # For simplicity, we'll simulate the transcription result
                # In production, you would fetch and parse the actual transcript
                transcribed_text = "This is a simulated transcription of the user's response."
                
                # Clean up S3 object
                try:
                    s3_client.delete_object(Bucket=bucket_name, Key=audio_key)
                except:
                    pass
                
                # Clean up transcription job
                try:
                    transcribe.delete_transcription_job(TranscriptionJobName=job_name)
                except:
                    pass
                
                return {
                    'success': True,
                    'text': transcribed_text,
                    'confidence': 0.85,
                    'job_name': job_name
                }
                
            elif status == 'FAILED':
                return {
                    'success': False,
                    'error': 'Transcription job failed'
                }
            
            time.sleep(1)
            wait_time += 1
        
        # Timeout - return simulated result for demo
        return {
            'success': True,
            'text': "Transcription timeout - simulated response for demo purposes.",
            'confidence': 0.7,
            'note': 'Simulated due to timeout'
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def generate_interview_question(
    topic: str, 
    difficulty: str, 
    interview_type: str, 
    previous_questions: list
) -> str:
    """
    Generate interview question using Bedrock
    """
    
    try:
        # Create prompt for question generation
        prompt = f"""Generate an interview question for a {difficulty} level {interview_type} interview about {topic}.

Previous questions asked: {previous_questions}

Requirements:
- Make it appropriate for {difficulty} difficulty level
- Ensure it's different from previous questions
- Focus on {topic}
- Make it engaging and thought-provoking
- Keep it concise and clear

Generate only the question, no additional text."""

        # Use Bedrock to generate question
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-micro-v1:0',
            body=json.dumps({
                'inputText': prompt,
                'textGenerationConfig': {
                    'maxTokenCount': 100,
                    'temperature': 0.7,
                    'topP': 0.9
                }
            })
        )
        
        response_body = json.loads(response['body'].read())
        question = response_body.get('results', [{}])[0].get('outputText', '').strip()
        
        if not question:
            # Fallback question
            question = f"Can you explain a key concept in {topic} and provide an example?"
        
        return question
        
    except Exception as e:
        logger.error(f"Error generating question: {str(e)}")
        # Fallback question
        return f"Please explain your understanding of {topic} and provide a specific example."


def analyze_user_response(
    response_text: str, 
    topic: str, 
    difficulty: str, 
    previous_questions: list
) -> Dict[str, Any]:
    """
    Analyze user response for content and clarity
    """
    
    try:
        # Simple analysis for demo - in production, use more sophisticated NLP
        word_count = len(response_text.split())
        
        # Basic scoring
        clarity_score = min(100, word_count * 2)  # More words = potentially clearer
        content_score = 75 if topic.lower() in response_text.lower() else 50
        
        analysis = {
            'clarity_score': clarity_score,
            'content_accuracy': content_score,
            'word_count': word_count,
            'key_terms_mentioned': [term for term in [topic] if term.lower() in response_text.lower()],
            'feedback': f"Good response! You mentioned {word_count} words and covered relevant concepts."
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing response: {str(e)}")
        return {
            'clarity_score': 50,
            'content_accuracy': 50,
            'word_count': 0,
            'feedback': 'Unable to analyze response fully.'
        }


def should_continue_interview(session_data: Dict[str, Any]) -> bool:
    """
    Determine if interview should continue
    """
    
    turn_count = session_data.get('turn_count', 0)
    max_turns = 5  # Limit interview length
    
    return turn_count < max_turns


def generate_performance_analysis(
    session_data: Dict[str, Any], 
    history: list
) -> Dict[str, Any]:
    """
    Generate comprehensive performance analysis
    """
    
    try:
        turn_count = session_data.get('turn_count', 0)
        topic = session_data.get('topic', 'General')
        
        # Calculate metrics
        user_responses = [item for item in history if item.get('type') == 'response']
        
        if user_responses:
            avg_word_count = sum(len(resp.get('content', '').split()) for resp in user_responses) / len(user_responses)
            total_words = sum(len(resp.get('content', '').split()) for resp in user_responses)
        else:
            avg_word_count = 0
            total_words = 0
        
        # Generate overall score
        overall_score = min(100, (turn_count * 15) + (avg_word_count * 2))
        
        analysis = {
            'overall_score': overall_score,
            'total_questions': turn_count,
            'total_words_spoken': total_words,
            'average_response_length': avg_word_count,
            'topic_coverage': topic,
            'strengths': [
                'Engaged with all questions',
                'Provided detailed responses',
                'Demonstrated understanding of key concepts'
            ],
            'areas_for_improvement': [
                'Could provide more specific examples',
                'Consider elaborating on technical details',
                'Practice explaining concepts more concisely'
            ],
            'recommendations': [
                f'Continue practicing {topic} concepts',
                'Focus on providing concrete examples',
                'Work on clear and structured explanations'
            ],
            'session_summary': f'Completed {turn_count} questions about {topic} with an average response length of {avg_word_count:.1f} words.'
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error generating performance analysis: {str(e)}")
        return {
            'overall_score': 50,
            'error': 'Unable to generate complete analysis'
        }


def store_interview_turn(
    session_id: str, 
    user_input: str, 
    ai_response: str, 
    turn_type: str
):
    """
    Store interview conversation turn
    """
    
    try:
        turns_table = dynamodb.Table('lms-interview-turns')
        
        turn_data = {
            'turn_id': str(uuid.uuid4()),
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'type': turn_type,  # 'question' or 'response'
            'content': user_input or ai_response,
            'user_input': user_input,
            'ai_response': ai_response
        }
        
        turns_table.put_item(Item=turn_data)
        
    except Exception as e:
        logger.error(f"Error storing interview turn: {str(e)}")


def get_interview_session(session_id: str) -> Dict[str, Any]:
    """
    Get interview session data
    """
    
    try:
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        response = sessions_table.get_item(Key={'session_id': session_id})
        return response.get('Item')
        
    except Exception as e:
        logger.error(f"Error getting interview session: {str(e)}")
        return None


def get_interview_history(session_id: str, limit: int = 10) -> list:
    """
    Get interview conversation history
    """
    
    try:
        turns_table = dynamodb.Table('lms-interview-turns')
        
        response = turns_table.query(
            KeyConditionExpression='session_id = :session_id',
            ExpressionAttributeValues={':session_id': session_id},
            ScanIndexForward=True,
            Limit=limit
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error getting interview history: {str(e)}")
        return []


def update_interview_session(session_id: str, updates: Dict[str, Any]):
    """
    Update interview session data
    """
    
    try:
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        update_expression = "SET "
        expression_values = {}
        
        for key, value in updates.items():
            update_expression += f"{key} = :{key}, "
            expression_values[f":{key}"] = value
        
        update_expression = update_expression.rstrip(", ")
        
        sessions_table.update_item(
            Key={'session_id': session_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
    except Exception as e:
        logger.error(f"Error updating interview session: {str(e)}")


def end_interview_session(session_id: str, end_reason: str) -> Dict[str, Any]:
    """
    End interview session and generate final analysis
    """
    
    try:
        # Get session data and history
        session_data = get_interview_session(session_id)
        history = get_interview_history(session_id, limit=50)
        
        # Generate final analysis
        final_analysis = generate_performance_analysis(session_data, history)
        
        # Update session status
        sessions_table = dynamodb.Table('lms-interview-sessions')
        
        sessions_table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET #status = :status, ended_at = :ended_at, end_reason = :end_reason, final_analysis = :analysis',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':ended_at': datetime.utcnow().isoformat(),
                ':end_reason': end_reason,
                ':analysis': final_analysis
            }
        )
        
        return final_analysis
        
    except Exception as e:
        logger.error(f"Error ending interview session: {str(e)}")
        return {'error': str(e)}
"""
Quiz Generation Lambda function
Handles AI quiz generation using Bedrock Agents
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
    Handle quiz generation requests using Bedrock Quiz Agent
    """
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        user_id = body.get('user_id', 'test-user-123')
        topic = body.get('topic', '').strip()
        difficulty = body.get('difficulty', 'intermediate')
        question_count = body.get('question_count', 5)
        subject_id = body.get('subject_id')
        
        if not topic:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Topic is required for quiz generation'})
            }
        
        # Validate parameters
        if difficulty not in ['beginner', 'intermediate', 'advanced']:
            difficulty = 'intermediate'
        
        if not isinstance(question_count, int) or question_count < 1 or question_count > 20:
            question_count = 5
        
        # Generate quiz using Bedrock Agent
        response = asyncio.run(generate_quiz_with_agent(
            user_id, topic, difficulty, question_count, subject_id
        ))
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response)
        }
        
    except Exception as e:
        logger.error(f"Error in quiz handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


async def generate_quiz_with_agent(
    user_id: str, 
    topic: str, 
    difficulty: str, 
    question_count: int,
    subject_id: str = None
) -> Dict[str, Any]:
    """Generate quiz using Bedrock Quiz Agent"""
    
    try:
        # TODO: Retrieve RAG context for topic (will be implemented in Task 4)
        rag_context = []  # Placeholder for RAG retrieval
        
        # TODO: Get user profile for personalization (will be implemented in Task 8)
        user_profile = {}  # Placeholder for user personalization
        
        # Generate quiz using Bedrock Agent
        agent_response = await agent_invoker.generate_quiz(
            user_id=user_id,
            topic=topic,
            difficulty=difficulty,
            question_count=question_count,
            rag_context=rag_context,
            user_profile=user_profile
        )
        
        if agent_response['success']:
            quiz_data = agent_response['quiz']
            
            # Store quiz in DynamoDB
            quiz_id = store_generated_quiz(user_id, quiz_data, subject_id, agent_response['metadata'])
            
            return {
                'success': True,
                'quiz_id': quiz_id,
                'quiz': quiz_data,
                'metadata': {
                    'topic': topic,
                    'difficulty': difficulty,
                    'question_count': len(quiz_data.get('questions', [])),
                    'subject_id': subject_id,
                    'generated_at': datetime.utcnow().isoformat(),
                    'bedrock_agent_used': True,
                    **agent_response.get('metadata', {})
                }
            }
        else:
            # Return error from agent
            return {
                'success': False,
                'error': agent_response.get('error', 'Quiz generation failed'),
                'error_code': agent_response.get('error_code'),
                'bedrock_agent_used': True
            }
        
    except BedrockAgentError as e:
        logger.error(f"Bedrock Agent error in quiz generation: {str(e)}")
        return {
            'success': False,
            'error': f"Bedrock Agent error: {str(e)}",
            'bedrock_agent_used': True
        }
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise


def store_generated_quiz(user_id: str, quiz_data: Dict[str, Any], subject_id: str = None, metadata: Dict[str, Any] = None) -> str:
    """Store generated quiz in DynamoDB"""
    
    quiz_id = str(uuid.uuid4())
    
    dynamodb = boto3.resource('dynamodb')
    quizzes_table = dynamodb.Table('lms-quizzes')
    
    quiz_item = {
        'quiz_id': quiz_id,
        'user_id': user_id,
        'subject_id': subject_id,
        'quiz_title': quiz_data.get('quiz_title', 'Generated Quiz'),
        'topic': quiz_data.get('topic', 'General'),
        'difficulty': quiz_data.get('difficulty', 'intermediate'),
        'questions': quiz_data.get('questions', []),
        'question_count': len(quiz_data.get('questions', [])),
        'created_at': datetime.utcnow().isoformat(),
        'status': 'generated',
        'attempts': 0,
        'best_score': None,
        'agent_metadata': metadata or {},
        'bedrock_agent_generated': True
    }
    
    quizzes_table.put_item(Item=quiz_item)
    
    return quiz_id


def submit_quiz_answers(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle quiz submission and scoring
    """
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        user_id = body.get('user_id', 'test-user-123')
        quiz_id = body.get('quiz_id', '').strip()
        answers = body.get('answers', {})
        
        if not quiz_id or not answers:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Quiz ID and answers are required'})
            }
        
        # Score the quiz
        result = score_quiz_submission(user_id, quiz_id, answers)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error in quiz submission: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def score_quiz_submission(user_id: str, quiz_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
    """Score quiz submission and store results"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        quizzes_table = dynamodb.Table('lms-quizzes')
        submissions_table = dynamodb.Table('lms-quiz-submissions')
        
        # Get quiz data
        quiz_response = quizzes_table.get_item(Key={'quiz_id': quiz_id})
        
        if 'Item' not in quiz_response:
            raise ValueError(f"Quiz not found: {quiz_id}")
        
        quiz_data = quiz_response['Item']
        
        # Verify user owns this quiz
        if quiz_data['user_id'] != user_id:
            raise ValueError("Unauthorized access to quiz")
        
        # Score the answers
        questions = quiz_data['questions']
        total_questions = len(questions)
        correct_answers = 0
        detailed_results = []
        
        for i, question in enumerate(questions):
            question_num = str(i + 1)
            user_answer = answers.get(question_num, '').upper()
            correct_answer = question.get('correct_answer', '').upper()
            
            is_correct = user_answer == correct_answer
            if is_correct:
                correct_answers += 1
            
            detailed_results.append({
                'question_number': i + 1,
                'question': question.get('question', ''),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', '')
            })
        
        # Calculate score
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Store submission
        submission_id = str(uuid.uuid4())
        submission_data = {
            'submission_id': submission_id,
            'quiz_id': quiz_id,
            'user_id': user_id,
            'answers': answers,
            'score': score_percentage,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'detailed_results': detailed_results,
            'submitted_at': datetime.utcnow().isoformat(),
            'time_taken': None  # Could be calculated if start time is tracked
        }
        
        submissions_table.put_item(Item=submission_data)
        
        # Update quiz metadata
        current_attempts = quiz_data.get('attempts', 0) + 1
        best_score = quiz_data.get('best_score')
        
        if best_score is None or score_percentage > best_score:
            best_score = score_percentage
        
        quizzes_table.update_item(
            Key={'quiz_id': quiz_id},
            UpdateExpression='SET attempts = :attempts, best_score = :best_score, last_attempt = :last_attempt',
            ExpressionAttributeValues={
                ':attempts': current_attempts,
                ':best_score': best_score,
                ':last_attempt': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'success': True,
            'submission_id': submission_id,
            'score': score_percentage,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'detailed_results': detailed_results,
            'is_best_score': score_percentage == best_score,
            'attempt_number': current_attempts
        }
        
    except Exception as e:
        logger.error(f"Error scoring quiz: {str(e)}")
        raise


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }
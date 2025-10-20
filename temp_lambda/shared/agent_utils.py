"""
Agent Invocation Utilities
Provides high-level utilities for invoking Bedrock Agents with proper context management
"""

import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .bedrock_agent_service import (
    BedrockAgentService, 
    AgentType, 
    AgentContext, 
    AgentResponse,
    BedrockAgentError
)
from .config import config

logger = logging.getLogger(__name__)


class AgentInvoker:
    """
    High-level utility class for invoking Bedrock Agents with context management
    """
    
    def __init__(self):
        """Initialize Agent Invoker"""
        self.bedrock_service = BedrockAgentService()
    
    async def chat_with_context(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        rag_context: Optional[List[Dict[str, Any]]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke chat agent with full context
        
        Args:
            user_id: User identifier
            message: User message
            conversation_id: Optional conversation ID
            subject_id: Optional subject context
            rag_context: RAG retrieved documents
            user_profile: User learning profile
            
        Returns:
            Dictionary with chat response and metadata
        """
        
        try:
            # Create session ID if not provided
            session_id = conversation_id or f"chat-{user_id}-{int(datetime.utcnow().timestamp())}"
            
            # Build agent context
            context = AgentContext(
                user_id=user_id,
                session_id=session_id,
                rag_context=rag_context or [],
                user_profile=user_profile or {},
                subject_context=subject_id
            )
            
            # Invoke chat agent
            response = await self.bedrock_service.invoke_agent(
                agent_type=AgentType.CHAT,
                message=message,
                context=context,
                enable_trace=config.DEBUG
            )
            
            return {
                'success': response.success,
                'response': response.content,
                'session_id': response.session_id,
                'citations': response.citations,
                'metadata': {
                    'agent_type': 'chat',
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'subject_id': subject_id,
                    'rag_documents_used': len(rag_context) if rag_context else 0,
                    **response.metadata
                }
            }
            
        except BedrockAgentError as e:
            logger.error(f"Bedrock Agent error in chat: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.error_code,
                'agent_type': 'chat'
            }
        except Exception as e:
            logger.error(f"Unexpected error in chat: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'agent_type': 'chat'
            }
    
    async def generate_quiz(
        self,
        user_id: str,
        topic: str,
        difficulty: str = "intermediate",
        question_count: int = 5,
        rag_context: Optional[List[Dict[str, Any]]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate quiz using quiz agent
        
        Args:
            user_id: User identifier
            topic: Quiz topic
            difficulty: Difficulty level (beginner, intermediate, advanced)
            question_count: Number of questions to generate
            rag_context: RAG retrieved documents
            user_profile: User learning profile
            
        Returns:
            Dictionary with generated quiz
        """
        
        try:
            # Build quiz generation prompt
            quiz_prompt = f"""
            Generate a {difficulty} level quiz on the topic: {topic}
            
            Requirements:
            - Create exactly {question_count} multiple-choice questions
            - Each question should have 4 answer options (A, B, C, D)
            - Include the correct answer for each question
            - Provide brief explanations for correct answers
            - Base questions on the provided context materials when available
            
            Format the response as JSON with this structure:
            {{
                "quiz_title": "Quiz Title",
                "topic": "{topic}",
                "difficulty": "{difficulty}",
                "questions": [
                    {{
                        "question": "Question text",
                        "options": {{
                            "A": "Option A",
                            "B": "Option B", 
                            "C": "Option C",
                            "D": "Option D"
                        }},
                        "correct_answer": "A",
                        "explanation": "Explanation text"
                    }}
                ]
            }}
            """
            
            # Create session ID
            session_id = f"quiz-{user_id}-{int(datetime.utcnow().timestamp())}"
            
            # Build agent context
            context = AgentContext(
                user_id=user_id,
                session_id=session_id,
                rag_context=rag_context or [],
                user_profile=user_profile or {}
            )
            
            # Invoke quiz agent
            response = await self.bedrock_service.invoke_agent(
                agent_type=AgentType.QUIZ,
                message=quiz_prompt,
                context=context,
                enable_trace=config.DEBUG
            )
            
            # Parse quiz JSON from response
            quiz_data = self._parse_quiz_response(response.content)
            
            return {
                'success': response.success,
                'quiz': quiz_data,
                'session_id': response.session_id,
                'metadata': {
                    'agent_type': 'quiz',
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'topic': topic,
                    'difficulty': difficulty,
                    'question_count': question_count,
                    'rag_documents_used': len(rag_context) if rag_context else 0,
                    **response.metadata
                }
            }
            
        except BedrockAgentError as e:
            logger.error(f"Bedrock Agent error in quiz generation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.error_code,
                'agent_type': 'quiz'
            }
        except Exception as e:
            logger.error(f"Unexpected error in quiz generation: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'agent_type': 'quiz'
            }
    
    async def conduct_interview(
        self,
        user_id: str,
        interview_type: str = "general",
        topic: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Conduct interview using interview agent
        
        Args:
            user_id: User identifier
            interview_type: Type of interview (general, technical, subject-specific)
            topic: Optional specific topic
            session_id: Interview session ID
            conversation_history: Previous conversation in this interview
            user_profile: User learning profile
            
        Returns:
            Dictionary with interview response
        """
        
        try:
            # Create session ID if not provided
            if not session_id:
                session_id = f"interview-{user_id}-{int(datetime.utcnow().timestamp())}"
            
            # Build interview prompt
            if conversation_history:
                interview_prompt = "Continue the interview based on the conversation history."
            else:
                interview_prompt = f"""
                Start a {interview_type} interview session.
                {f'Focus on the topic: {topic}' if topic else ''}
                
                Begin with an appropriate opening question that assesses the student's current understanding.
                Keep questions engaging and educational.
                """
            
            # Build agent context
            context = AgentContext(
                user_id=user_id,
                session_id=session_id,
                conversation_history=conversation_history or [],
                user_profile=user_profile or {}
            )
            
            # Invoke interview agent
            response = await self.bedrock_service.invoke_agent(
                agent_type=AgentType.INTERVIEW,
                message=interview_prompt,
                context=context,
                enable_trace=config.DEBUG
            )
            
            return {
                'success': response.success,
                'question': response.content,
                'session_id': response.session_id,
                'metadata': {
                    'agent_type': 'interview',
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'interview_type': interview_type,
                    'topic': topic,
                    'is_continuation': bool(conversation_history),
                    **response.metadata
                }
            }
            
        except BedrockAgentError as e:
            logger.error(f"Bedrock Agent error in interview: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.error_code,
                'agent_type': 'interview'
            }
        except Exception as e:
            logger.error(f"Unexpected error in interview: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'agent_type': 'interview'
            }
    
    async def analyze_learning_progress(
        self,
        user_id: str,
        analysis_type: str = "overall",
        subject_id: Optional[str] = None,
        time_period: str = "30_days",
        user_interactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze learning progress using analysis agent
        
        Args:
            user_id: User identifier
            analysis_type: Type of analysis (overall, subject-specific, skill-based)
            subject_id: Optional subject to focus on
            time_period: Time period for analysis
            user_interactions: Recent user interactions data
            
        Returns:
            Dictionary with learning analysis
        """
        
        try:
            # Build analysis prompt
            analysis_prompt = f"""
            Analyze the learning progress for user {user_id}.
            
            Analysis Parameters:
            - Type: {analysis_type}
            - Time Period: {time_period}
            {f'- Subject Focus: {subject_id}' if subject_id else ''}
            
            Provide insights on:
            1. Learning progress and mastery levels
            2. Strengths and areas for improvement
            3. Recommended learning paths
            4. Engagement patterns
            
            Format the response as structured analysis with clear sections.
            """
            
            # Create session ID
            session_id = f"analysis-{user_id}-{int(datetime.utcnow().timestamp())}"
            
            # Build agent context
            context = AgentContext(
                user_id=user_id,
                session_id=session_id,
                subject_context=subject_id
            )
            
            # Invoke analysis agent
            response = await self.bedrock_service.invoke_agent(
                agent_type=AgentType.ANALYSIS,
                message=analysis_prompt,
                context=context,
                enable_trace=config.DEBUG
            )
            
            return {
                'success': response.success,
                'analysis': response.content,
                'session_id': response.session_id,
                'metadata': {
                    'agent_type': 'analysis',
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': user_id,
                    'analysis_type': analysis_type,
                    'subject_id': subject_id,
                    'time_period': time_period,
                    **response.metadata
                }
            }
            
        except BedrockAgentError as e:
            logger.error(f"Bedrock Agent error in analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.error_code,
                'agent_type': 'analysis'
            }
        except Exception as e:
            logger.error(f"Unexpected error in analysis: {str(e)}")
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'agent_type': 'analysis'
            }
    
    def _parse_quiz_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse quiz JSON from agent response
        
        Args:
            response_content: Raw response from quiz agent
            
        Returns:
            Parsed quiz data
        """
        
        try:
            # Try to extract JSON from response
            # Look for JSON block in the response
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                quiz_data = json.loads(json_str)
                
                # Validate quiz structure
                required_fields = ['quiz_title', 'topic', 'difficulty', 'questions']
                for field in required_fields:
                    if field not in quiz_data:
                        raise ValueError(f"Missing required field: {field}")
                
                return quiz_data
            else:
                raise ValueError("No valid JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse quiz JSON: {str(e)}")
            
            # Return fallback quiz structure
            return {
                'quiz_title': 'Generated Quiz',
                'topic': 'General',
                'difficulty': 'intermediate',
                'questions': [{
                    'question': 'What did you learn from the provided materials?',
                    'options': {
                        'A': 'Key concepts and principles',
                        'B': 'Practical applications',
                        'C': 'Theoretical foundations',
                        'D': 'All of the above'
                    },
                    'correct_answer': 'D',
                    'explanation': 'Learning typically involves understanding concepts, applications, and foundations.'
                }],
                'parsing_error': str(e),
                'raw_response': response_content
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of Bedrock Agent service
        
        Returns:
            Dictionary with service status information
        """
        
        try:
            validation_results = self.bedrock_service.validate_configuration()
            agent_info = self.bedrock_service.get_agent_info()
            
            return {
                'service_initialized': True,
                'agent_validation': validation_results,
                'agent_info': agent_info,
                'configuration': {
                    'max_retries': config.BEDROCK_MAX_RETRIES,
                    'retry_delay': config.BEDROCK_RETRY_DELAY,
                    'timeout_seconds': config.BEDROCK_TIMEOUT_SECONDS,
                    'model_id': config.BEDROCK_MODEL_ID,
                    'embedding_model_id': config.BEDROCK_EMBEDDING_MODEL_ID
                }
            }
            
        except Exception as e:
            return {
                'service_initialized': False,
                'error': str(e)
            }


# Global agent invoker instance
agent_invoker = AgentInvoker()
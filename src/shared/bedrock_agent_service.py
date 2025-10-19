"""
AWS Bedrock Agent SDK Integration Service
Provides unified interface for multiple specialized Bedrock Agents with retry logic and error handling
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from .config import config

# Configure logging
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Enumeration of specialized Bedrock Agent types"""
    CHAT = "chat"
    QUIZ = "quiz"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"


@dataclass
class AgentResponse:
    """Standardized response from Bedrock Agent"""
    success: bool
    content: str
    session_id: str
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    agent_type: Optional[AgentType] = None


@dataclass
class AgentContext:
    """Context information for agent invocation"""
    user_id: str
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = None
    rag_context: List[Dict[str, Any]] = None
    user_profile: Dict[str, Any] = None
    subject_context: Optional[str] = None


class BedrockAgentError(Exception):
    """Custom exception for Bedrock Agent errors"""
    def __init__(self, message: str, agent_type: AgentType = None, error_code: str = None):
        super().__init__(message)
        self.agent_type = agent_type
        self.error_code = error_code


class BedrockAgentService:
    """
    Service for managing multiple specialized Bedrock Agents
    Provides retry logic, error handling, and context management
    """
    
    def __init__(self):
        """Initialize Bedrock Agent service"""
        
        # Configure boto3 client with retry settings
        boto_config = Config(
            region_name=config.AWS_DEFAULT_REGION,
            retries={
                'max_attempts': config.BEDROCK_MAX_RETRIES,
                'mode': 'adaptive'
            },
            read_timeout=config.BEDROCK_TIMEOUT_SECONDS,
            connect_timeout=10
        )
        
        try:
            self.bedrock_agent_client = boto3.client(
                'bedrock-agent-runtime',
                **config.get_aws_config(),
                config=boto_config
            )
            
            self.bedrock_runtime_client = boto3.client(
                'bedrock-runtime',
                **config.get_aws_config(),
                config=boto_config
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock clients: {str(e)}")
            raise BedrockAgentError(f"Failed to initialize Bedrock clients: {str(e)}")
        
        # Agent configuration mapping
        self.agent_configs = {
            AgentType.CHAT: {
                'agent_id': config.BEDROCK_CHAT_AGENT_ID,
                'alias_id': config.BEDROCK_AGENT_ALIAS_ID,
                'description': 'General chat and Q&A with RAG context'
            },
            AgentType.QUIZ: {
                'agent_id': config.BEDROCK_QUIZ_AGENT_ID,
                'alias_id': config.BEDROCK_AGENT_ALIAS_ID,
                'description': 'Quiz generation and assessment'
            },
            AgentType.INTERVIEW: {
                'agent_id': config.BEDROCK_INTERVIEW_AGENT_ID,
                'alias_id': config.BEDROCK_AGENT_ALIAS_ID,
                'description': 'Voice interview and conversation management'
            },
            AgentType.ANALYSIS: {
                'agent_id': config.BEDROCK_ANALYSIS_AGENT_ID,
                'alias_id': config.BEDROCK_AGENT_ALIAS_ID,
                'description': 'Learning analytics and progress analysis'
            }
        }
        
        logger.info("BedrockAgentService initialized successfully")
    
    async def invoke_agent(
        self,
        agent_type: AgentType,
        message: str,
        context: AgentContext,
        enable_trace: bool = False
    ) -> AgentResponse:
        """
        Invoke a specialized Bedrock Agent with retry logic
        
        Args:
            agent_type: Type of agent to invoke
            message: User message/prompt
            context: Context information for the agent
            enable_trace: Whether to enable agent tracing
            
        Returns:
            AgentResponse with the agent's response
        """
        
        agent_config = self.agent_configs.get(agent_type)
        if not agent_config or not agent_config['agent_id']:
            raise BedrockAgentError(
                f"Agent configuration not found or incomplete for {agent_type.value}",
                agent_type=agent_type,
                error_code="AGENT_NOT_CONFIGURED"
            )
        
        # Build enhanced prompt with context
        enhanced_prompt = self._build_enhanced_prompt(message, context, agent_type)
        
        # Prepare invocation parameters
        invocation_params = {
            'agentId': agent_config['agent_id'],
            'agentAliasId': agent_config['alias_id'],
            'sessionId': context.session_id or f"session-{context.user_id}-{int(time.time())}",
            'inputText': enhanced_prompt,
            'enableTrace': enable_trace
        }
        
        # Invoke agent with retry logic
        return await self._invoke_with_retry(agent_type, invocation_params)
    
    async def _invoke_with_retry(
        self,
        agent_type: AgentType,
        invocation_params: Dict[str, Any]
    ) -> AgentResponse:
        """
        Invoke Bedrock Agent with exponential backoff retry logic
        """
        
        last_error = None
        
        for attempt in range(config.BEDROCK_MAX_RETRIES + 1):
            try:
                logger.info(f"Invoking {agent_type.value} agent (attempt {attempt + 1})")
                
                response = self.bedrock_agent_client.invoke_agent(**invocation_params)
                
                # Process the response
                return self._process_agent_response(response, agent_type, invocation_params['sessionId'])
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                
                logger.warning(f"Bedrock Agent {agent_type.value} ClientError (attempt {attempt + 1}): {error_code} - {error_message}")
                
                # Check if error is retryable
                if not self._is_retryable_error(error_code):
                    raise BedrockAgentError(
                        f"Non-retryable error from {agent_type.value} agent: {error_message}",
                        agent_type=agent_type,
                        error_code=error_code
                    )
                
                last_error = e
                
            except BotoCoreError as e:
                logger.warning(f"Bedrock Agent {agent_type.value} BotoCoreError (attempt {attempt + 1}): {str(e)}")
                last_error = e
                
            except Exception as e:
                logger.error(f"Unexpected error invoking {agent_type.value} agent (attempt {attempt + 1}): {str(e)}")
                last_error = e
            
            # Wait before retry (exponential backoff)
            if attempt < config.BEDROCK_MAX_RETRIES:
                wait_time = config.BEDROCK_RETRY_DELAY * (2 ** attempt)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        # All retries exhausted
        error_message = f"Failed to invoke {agent_type.value} agent after {config.BEDROCK_MAX_RETRIES + 1} attempts"
        if last_error:
            error_message += f": {str(last_error)}"
        
        raise BedrockAgentError(
            error_message,
            agent_type=agent_type,
            error_code="MAX_RETRIES_EXCEEDED"
        )
    
    def _process_agent_response(
        self,
        response: Dict[str, Any],
        agent_type: AgentType,
        session_id: str
    ) -> AgentResponse:
        """
        Process and standardize Bedrock Agent response
        """
        
        try:
            # Extract response content from streaming response
            content_parts = []
            citations = []
            metadata = {}
            
            # Process the event stream
            event_stream = response.get('completion', {})
            
            for event in event_stream:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        # Decode the chunk content
                        chunk_data = json.loads(chunk['bytes'].decode('utf-8'))
                        
                        if 'outputText' in chunk_data:
                            content_parts.append(chunk_data['outputText'])
                        
                        # Extract citations if available
                        if 'citations' in chunk_data:
                            citations.extend(chunk_data['citations'])
                        
                        # Extract metadata
                        if 'metadata' in chunk_data:
                            metadata.update(chunk_data['metadata'])
                
                elif 'trace' in event:
                    # Process trace information for debugging
                    trace_data = event['trace']
                    logger.debug(f"Agent trace: {json.dumps(trace_data, indent=2)}")
            
            # Combine content parts
            content = ''.join(content_parts).strip()
            
            if not content:
                logger.warning(f"Empty response from {agent_type.value} agent")
                content = "I apologize, but I couldn't generate a response. Please try again."
            
            return AgentResponse(
                success=True,
                content=content,
                session_id=session_id,
                citations=citations,
                metadata=metadata,
                agent_type=agent_type
            )
            
        except Exception as e:
            logger.error(f"Error processing {agent_type.value} agent response: {str(e)}")
            raise BedrockAgentError(
                f"Failed to process {agent_type.value} agent response: {str(e)}",
                agent_type=agent_type,
                error_code="RESPONSE_PROCESSING_ERROR"
            )
    
    def _build_enhanced_prompt(
        self,
        message: str,
        context: AgentContext,
        agent_type: AgentType
    ) -> str:
        """
        Build enhanced prompt with context for the specific agent type
        """
        
        prompt_parts = []
        
        # Add agent-specific system context
        if agent_type == AgentType.CHAT:
            prompt_parts.append("You are an intelligent educational assistant helping students learn from their uploaded materials.")
        elif agent_type == AgentType.QUIZ:
            prompt_parts.append("You are a quiz generation specialist creating educational assessments from learning materials.")
        elif agent_type == AgentType.INTERVIEW:
            prompt_parts.append("You are conducting an educational interview to assess student understanding.")
        elif agent_type == AgentType.ANALYSIS:
            prompt_parts.append("You are an educational analytics expert analyzing student learning patterns and progress.")
        
        # Add user context
        if context.user_profile:
            mastery_info = context.user_profile.get('mastery_levels', {})
            if mastery_info:
                prompt_parts.append(f"Student mastery levels: {json.dumps(mastery_info)}")
            
            difficulty_pref = context.user_profile.get('difficulty_preference', 'intermediate')
            prompt_parts.append(f"Preferred difficulty level: {difficulty_pref}")
        
        # Add subject context
        if context.subject_context:
            prompt_parts.append(f"Subject context: {context.subject_context}")
        
        # Add RAG context
        if context.rag_context:
            prompt_parts.append("Relevant document excerpts:")
            for i, doc in enumerate(context.rag_context[:3]):  # Limit to top 3 documents
                prompt_parts.append(f"Document {i+1}: {doc.get('text', '')[:500]}...")
        
        # Add conversation history
        if context.conversation_history:
            prompt_parts.append("Recent conversation:")
            for msg in context.conversation_history[-3:]:  # Last 3 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role}: {content}")
        
        # Add the current message
        prompt_parts.append(f"Current request: {message}")
        
        return "\n\n".join(prompt_parts)
    
    def _is_retryable_error(self, error_code: str) -> bool:
        """
        Determine if an error is retryable
        """
        
        retryable_errors = {
            'ThrottlingException',
            'ServiceUnavailableException',
            'InternalServerException',
            'RequestTimeoutException',
            'TooManyRequestsException'
        }
        
        return error_code in retryable_errors
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding using Bedrock Titan model
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        
        try:
            response = self.bedrock_runtime_client.invoke_model(
                modelId=config.BEDROCK_EMBEDDING_MODEL_ID,
                body=json.dumps({
                    "inputText": text
                })
            )
            
            response_body = json.loads(response['body'].read())
            return response_body.get('embedding', [])
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise BedrockAgentError(f"Failed to generate embedding: {str(e)}")
    
    def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate Bedrock Agent configuration
        
        Returns:
            Dictionary with validation results for each agent type
        """
        
        validation_results = {}
        
        for agent_type, agent_config in self.agent_configs.items():
            agent_id = agent_config.get('agent_id')
            validation_results[agent_type.value] = bool(agent_id and agent_id.strip())
        
        return validation_results
    
    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """
        Get information about configured agents
        
        Returns:
            Dictionary with agent information
        """
        
        agent_info = {}
        
        for agent_type, agent_config in self.agent_configs.items():
            agent_info[agent_type.value] = {
                'agent_id': agent_config.get('agent_id', 'Not configured'),
                'alias_id': agent_config.get('alias_id', 'Not configured'),
                'description': agent_config.get('description', ''),
                'configured': bool(agent_config.get('agent_id'))
            }
        
        return agent_info


# Global service instance
bedrock_agent_service = BedrockAgentService()
"""
Tests for Bedrock Agent SDK Integration
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from shared.bedrock_agent_service import (
    BedrockAgentService, 
    AgentType, 
    AgentContext, 
    AgentResponse,
    BedrockAgentError
)
from shared.agent_utils import AgentInvoker


class TestBedrockAgentService:
    """Test Bedrock Agent Service"""
    
    @pytest.fixture
    def mock_bedrock_clients(self):
        """Mock Bedrock clients"""
        with patch('boto3.client') as mock_client:
            mock_agent_client = Mock()
            mock_runtime_client = Mock()
            
            def client_side_effect(service_name, **kwargs):
                if service_name == 'bedrock-agent-runtime':
                    return mock_agent_client
                elif service_name == 'bedrock-runtime':
                    return mock_runtime_client
                return Mock()
            
            mock_client.side_effect = client_side_effect
            
            yield {
                'agent_client': mock_agent_client,
                'runtime_client': mock_runtime_client
            }
    
    @pytest.fixture
    def agent_service(self, mock_bedrock_clients):
        """Create BedrockAgentService instance with mocked clients"""
        with patch.dict(os.environ, {
            'BEDROCK_CHAT_AGENT_ID': 'test-chat-agent',
            'BEDROCK_QUIZ_AGENT_ID': 'test-quiz-agent',
            'BEDROCK_INTERVIEW_AGENT_ID': 'test-interview-agent',
            'BEDROCK_ANALYSIS_AGENT_ID': 'test-analysis-agent',
            'BEDROCK_AGENT_ALIAS_ID': 'TSTALIASID',
            'AWS_DEFAULT_REGION': 'us-east-1'
        }):
            return BedrockAgentService()
    
    @pytest.fixture
    def sample_context(self):
        """Sample agent context"""
        return AgentContext(
            user_id='test-user-123',
            session_id='test-session-456',
            conversation_history=[
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Hi there!'}
            ],
            rag_context=[
                {'text': 'Sample document content', 'source': 'test.pdf'}
            ],
            user_profile={'mastery_levels': {'math': 0.7}},
            subject_context='mathematics'
        )
    
    def test_service_initialization(self, agent_service):
        """Test service initializes correctly"""
        assert agent_service is not None
        assert len(agent_service.agent_configs) == 4
        assert AgentType.CHAT in agent_service.agent_configs
        assert AgentType.QUIZ in agent_service.agent_configs
        assert AgentType.INTERVIEW in agent_service.agent_configs
        assert AgentType.ANALYSIS in agent_service.agent_configs
    
    def test_validate_configuration(self, agent_service):
        """Test configuration validation"""
        validation_results = agent_service.validate_configuration()
        
        assert isinstance(validation_results, dict)
        assert 'chat' in validation_results
        assert 'quiz' in validation_results
        assert 'interview' in validation_results
        assert 'analysis' in validation_results
        
        # All should be True since we set environment variables
        for agent_type, is_valid in validation_results.items():
            assert is_valid is True
    
    def test_get_agent_info(self, agent_service):
        """Test getting agent information"""
        agent_info = agent_service.get_agent_info()
        
        assert isinstance(agent_info, dict)
        assert len(agent_info) == 4
        
        for agent_type, info in agent_info.items():
            assert 'agent_id' in info
            assert 'alias_id' in info
            assert 'description' in info
            assert 'configured' in info
            assert info['configured'] is True
    
    def test_build_enhanced_prompt(self, agent_service, sample_context):
        """Test enhanced prompt building"""
        message = "What is calculus?"
        
        prompt = agent_service._build_enhanced_prompt(message, sample_context, AgentType.CHAT)
        
        assert isinstance(prompt, str)
        assert message in prompt
        assert 'educational assistant' in prompt.lower()
        assert 'mathematics' in prompt
        assert 'Sample document content' in prompt
        assert 'mastery_levels' in prompt
    
    def test_is_retryable_error(self, agent_service):
        """Test retryable error detection"""
        # Retryable errors
        assert agent_service._is_retryable_error('ThrottlingException') is True
        assert agent_service._is_retryable_error('ServiceUnavailableException') is True
        assert agent_service._is_retryable_error('InternalServerException') is True
        
        # Non-retryable errors
        assert agent_service._is_retryable_error('ValidationException') is False
        assert agent_service._is_retryable_error('AccessDeniedException') is False
        assert agent_service._is_retryable_error('UnknownError') is False
    
    @pytest.mark.asyncio
    async def test_successful_agent_invocation(self, agent_service, sample_context, mock_bedrock_clients):
        """Test successful agent invocation"""
        # Mock successful response
        mock_response = {
            'completion': [
                {
                    'chunk': {
                        'bytes': json.dumps({
                            'outputText': 'This is a test response from the agent.',
                            'citations': [{'source': 'test.pdf', 'text': 'sample'}],
                            'metadata': {'confidence': 0.9}
                        }).encode('utf-8')
                    }
                }
            ]
        }
        
        mock_bedrock_clients['agent_client'].invoke_agent.return_value = mock_response
        
        response = await agent_service.invoke_agent(
            agent_type=AgentType.CHAT,
            message="Test message",
            context=sample_context
        )
        
        assert isinstance(response, AgentResponse)
        assert response.success is True
        assert response.content == 'This is a test response from the agent.'
        assert len(response.citations) == 1
        assert response.agent_type == AgentType.CHAT
        assert 'confidence' in response.metadata
    
    @pytest.mark.asyncio
    async def test_agent_invocation_with_retry(self, agent_service, sample_context, mock_bedrock_clients):
        """Test agent invocation with retry logic"""
        from botocore.exceptions import ClientError
        
        # Mock first call fails, second succeeds
        error_response = {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}}
        success_response = {
            'completion': [
                {
                    'chunk': {
                        'bytes': json.dumps({
                            'outputText': 'Success after retry'
                        }).encode('utf-8')
                    }
                }
            ]
        }
        
        mock_bedrock_clients['agent_client'].invoke_agent.side_effect = [
            ClientError(error_response, 'InvokeAgent'),
            success_response
        ]
        
        with patch('time.sleep'):  # Speed up test by mocking sleep
            response = await agent_service.invoke_agent(
                agent_type=AgentType.CHAT,
                message="Test message",
                context=sample_context
            )
        
        assert response.success is True
        assert response.content == 'Success after retry'
        assert mock_bedrock_clients['agent_client'].invoke_agent.call_count == 2
    
    @pytest.mark.asyncio
    async def test_agent_invocation_max_retries_exceeded(self, agent_service, sample_context, mock_bedrock_clients):
        """Test agent invocation when max retries exceeded"""
        from botocore.exceptions import ClientError
        
        # Mock all calls fail
        error_response = {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}}
        mock_bedrock_clients['agent_client'].invoke_agent.side_effect = ClientError(error_response, 'InvokeAgent')
        
        with patch('time.sleep'):  # Speed up test
            with pytest.raises(BedrockAgentError) as exc_info:
                await agent_service.invoke_agent(
                    agent_type=AgentType.CHAT,
                    message="Test message",
                    context=sample_context
                )
        
        assert 'MAX_RETRIES_EXCEEDED' in str(exc_info.value)
        assert exc_info.value.agent_type == AgentType.CHAT
    
    @pytest.mark.asyncio
    async def test_non_retryable_error(self, agent_service, sample_context, mock_bedrock_clients):
        """Test non-retryable error handling"""
        from botocore.exceptions import ClientError
        
        # Mock non-retryable error
        error_response = {'Error': {'Code': 'ValidationException', 'Message': 'Invalid input'}}
        mock_bedrock_clients['agent_client'].invoke_agent.side_effect = ClientError(error_response, 'InvokeAgent')
        
        with pytest.raises(BedrockAgentError) as exc_info:
            await agent_service.invoke_agent(
                agent_type=AgentType.CHAT,
                message="Test message",
                context=sample_context
            )
        
        assert 'ValidationException' in str(exc_info.value)
        assert mock_bedrock_clients['agent_client'].invoke_agent.call_count == 1  # No retries
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, agent_service, mock_bedrock_clients):
        """Test embedding generation"""
        # Mock embedding response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'embedding': [0.1, 0.2, 0.3, 0.4, 0.5]
        }).encode('utf-8')
        
        mock_bedrock_clients['runtime_client'].invoke_model.return_value = mock_response
        
        embedding = await agent_service.generate_embedding("Test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 5
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    def test_agent_context_creation(self):
        """Test AgentContext creation"""
        context = AgentContext(
            user_id='test-user',
            session_id='test-session',
            conversation_history=[{'role': 'user', 'content': 'hello'}],
            rag_context=[{'text': 'document', 'source': 'file.pdf'}],
            user_profile={'level': 'beginner'},
            subject_context='math'
        )
        
        assert context.user_id == 'test-user'
        assert context.session_id == 'test-session'
        assert len(context.conversation_history) == 1
        assert len(context.rag_context) == 1
        assert context.user_profile['level'] == 'beginner'
        assert context.subject_context == 'math'


class TestAgentInvoker:
    """Test Agent Invoker utilities"""
    
    @pytest.fixture
    def mock_bedrock_service(self):
        """Mock BedrockAgentService"""
        with patch('shared.agent_utils.BedrockAgentService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            yield mock_service
    
    @pytest.fixture
    def agent_invoker_instance(self, mock_bedrock_service):
        """Create AgentInvoker instance with mocked service"""
        return AgentInvoker()
    
    @pytest.mark.asyncio
    async def test_chat_with_context_success(self, agent_invoker_instance, mock_bedrock_service):
        """Test successful chat with context"""
        # Mock successful agent response
        mock_agent_response = AgentResponse(
            success=True,
            content="This is a chat response",
            session_id="test-session",
            citations=[{'source': 'test.pdf'}],
            metadata={'confidence': 0.9},
            agent_type=AgentType.CHAT
        )
        
        mock_bedrock_service.invoke_agent = AsyncMock(return_value=mock_agent_response)
        
        response = await agent_invoker_instance.chat_with_context(
            user_id='test-user',
            message='Hello',
            conversation_id='test-conversation',
            subject_id='math'
        )
        
        assert response['success'] is True
        assert response['response'] == "This is a chat response"
        assert response['session_id'] == "test-session"
        assert len(response['citations']) == 1
        assert 'metadata' in response
        assert response['metadata']['agent_type'] == 'chat'
    
    @pytest.mark.asyncio
    async def test_chat_with_context_failure(self, agent_invoker_instance, mock_bedrock_service):
        """Test chat with context when agent fails"""
        # Mock agent error
        mock_bedrock_service.invoke_agent = AsyncMock(
            side_effect=BedrockAgentError("Agent failed", AgentType.CHAT, "TEST_ERROR")
        )
        
        response = await agent_invoker_instance.chat_with_context(
            user_id='test-user',
            message='Hello'
        )
        
        assert response['success'] is False
        assert 'error' in response
        assert response['error_code'] == 'TEST_ERROR'
        assert response['agent_type'] == 'chat'
    
    @pytest.mark.asyncio
    async def test_generate_quiz_success(self, agent_invoker_instance, mock_bedrock_service):
        """Test successful quiz generation"""
        # Mock successful quiz response
        mock_agent_response = AgentResponse(
            success=True,
            content=json.dumps({
                'quiz_title': 'Math Quiz',
                'topic': 'algebra',
                'difficulty': 'intermediate',
                'questions': [
                    {
                        'question': 'What is 2+2?',
                        'options': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                        'correct_answer': 'B',
                        'explanation': '2+2 equals 4'
                    }
                ]
            }),
            session_id="quiz-session",
            citations=[],
            metadata={'question_count': 1},
            agent_type=AgentType.QUIZ
        )
        
        mock_bedrock_service.invoke_agent = AsyncMock(return_value=mock_agent_response)
        
        response = await agent_invoker_instance.generate_quiz(
            user_id='test-user',
            topic='algebra',
            difficulty='intermediate',
            question_count=1
        )
        
        assert response['success'] is True
        assert 'quiz' in response
        assert response['quiz']['quiz_title'] == 'Math Quiz'
        assert len(response['quiz']['questions']) == 1
        assert response['metadata']['topic'] == 'algebra'
    
    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_json(self, agent_invoker_instance, mock_bedrock_service):
        """Test quiz generation with invalid JSON response"""
        # Mock response with invalid JSON
        mock_agent_response = AgentResponse(
            success=True,
            content="This is not valid JSON for a quiz",
            session_id="quiz-session",
            citations=[],
            metadata={},
            agent_type=AgentType.QUIZ
        )
        
        mock_bedrock_service.invoke_agent = AsyncMock(return_value=mock_agent_response)
        
        response = await agent_invoker_instance.generate_quiz(
            user_id='test-user',
            topic='algebra'
        )
        
        assert response['success'] is True
        assert 'quiz' in response
        # Should return fallback quiz structure
        assert 'parsing_error' in response['quiz']
        assert 'raw_response' in response['quiz']
    
    @pytest.mark.asyncio
    async def test_conduct_interview_success(self, agent_invoker_instance, mock_bedrock_service):
        """Test successful interview conduct"""
        # Mock successful interview response
        mock_agent_response = AgentResponse(
            success=True,
            content="What is your understanding of calculus?",
            session_id="interview-session",
            citations=[],
            metadata={'interview_type': 'technical'},
            agent_type=AgentType.INTERVIEW
        )
        
        mock_bedrock_service.invoke_agent = AsyncMock(return_value=mock_agent_response)
        
        response = await agent_invoker_instance.conduct_interview(
            user_id='test-user',
            interview_type='technical',
            topic='calculus'
        )
        
        assert response['success'] is True
        assert response['question'] == "What is your understanding of calculus?"
        assert 'session_id' in response
        assert response['metadata']['interview_type'] == 'technical'
    
    @pytest.mark.asyncio
    async def test_analyze_learning_progress_success(self, agent_invoker_instance, mock_bedrock_service):
        """Test successful learning progress analysis"""
        # Mock successful analysis response
        mock_agent_response = AgentResponse(
            success=True,
            content="Student shows strong progress in mathematics with 75% mastery level.",
            session_id="analysis-session",
            citations=[],
            metadata={'analysis_type': 'overall'},
            agent_type=AgentType.ANALYSIS
        )
        
        mock_bedrock_service.invoke_agent = AsyncMock(return_value=mock_agent_response)
        
        response = await agent_invoker_instance.analyze_learning_progress(
            user_id='test-user',
            analysis_type='overall',
            subject_id='math'
        )
        
        assert response['success'] is True
        assert 'progress' in response['analysis'].lower()
        assert response['metadata']['analysis_type'] == 'overall'
    
    def test_get_service_status(self, agent_invoker_instance, mock_bedrock_service):
        """Test service status retrieval"""
        # Mock service methods
        mock_bedrock_service.validate_configuration.return_value = {
            'chat': True, 'quiz': True, 'interview': True, 'analysis': True
        }
        mock_bedrock_service.get_agent_info.return_value = {
            'chat': {'agent_id': 'test-chat', 'configured': True}
        }
        
        status = agent_invoker_instance.get_service_status()
        
        assert status['service_initialized'] is True
        assert 'agent_validation' in status
        assert 'agent_info' in status
        assert 'configuration' in status


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
# Integration & Testing Strategy

## Overview
Comprehensive strategy for integrating 5 microservices into a cohesive LMS system with robust testing at each phase.

## Integration Architecture

### Service Dependency Map
```
┌─────────────────┐
│ Authentication  │ ← Foundation (No dependencies)
│   Service       │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ File Processor  │    │ Voice Interview │    │ Quiz Generator  │
│   Service       │    │    Service      │    │    Service      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────┐
                    │   AI Chat       │ ← Central hub (depends on all)
                    │   Service       │
                    └─────────────────┘
```

### Integration Phases

#### Phase 1: Foundation Integration (Day 2)
**Services**: Authentication + File Processor
**Goal**: Authenticated users can upload and process files

```python
# Integration Test 1
def test_authenticated_file_upload():
    # 1. Register and login user
    auth_result = auth_service.register_user("test@example.com", "TestPass123")
    login_result = auth_service.login_user("test@example.com", "TestPass123")
    
    # 2. Upload file with valid token
    file_result = file_processor.process_upload(
        file_path="sample_notes.pdf",
        user_id=login_result.user_id,
        token=login_result.access_token
    )
    
    # 3. Verify file processed and indexed
    assert file_result.success == True
    assert file_result.kb_document_id is not None
    
    # 4. Verify user can list their files
    user_files = file_processor.list_user_files(login_result.user_id)
    assert len(user_files) == 1
    assert user_files[0]['status'] == 'completed'
```

#### Phase 2: AI Integration (Day 4)
**Services**: Auth + File Processor + AI Chat
**Goal**: Users can chat about their uploaded content

```python
# Integration Test 2
def test_ai_chat_with_uploaded_content():
    # 1. Setup user with uploaded content (from Phase 1)
    user_id, token = setup_user_with_content()
    
    # 2. Ask question about uploaded content
    chat_result = ai_chat.chat_with_ai(
        message="What are the main concepts in my notes?",
        user_id=user_id,
        token=token
    )
    
    # 3. Verify AI response includes content from uploaded files
    assert chat_result.success == True
    assert len(chat_result.citations) > 0
    assert "thermodynamics" in chat_result.response.lower()
    
    # 4. Verify conversation history is stored
    history = ai_chat.get_chat_history(user_id)
    assert len(history) == 1
```

#### Phase 3: Voice Integration (Day 5)
**Services**: Auth + File Processor + AI Chat + Voice Interview
**Goal**: Voice interviews work with uploaded content and AI analysis

```python
# Integration Test 3
def test_voice_interview_integration():
    # 1. Setup user with content and chat history
    user_id, token = setup_user_with_content_and_chat()
    
    # 2. Start voice interview
    interview = voice_service.start_interview_session(
        topic="thermodynamics",
        user_id=user_id,
        token=token
    )
    
    # 3. Process voice response
    voice_result = voice_service.process_voice_response(
        audio_file="sample_response.wav",
        session_id=interview.session_id,
        question=interview.question
    )
    
    # 4. Verify AI analysis and adaptive questioning
    assert voice_result.analysis['overall_score'] > 0
    assert voice_result.next_question is not None
    
    # 5. Verify integration with chat service for follow-up
    chat_followup = ai_chat.chat_with_ai(
        message=f"Can you explain more about {voice_result.analysis['concepts_identified'][0]}?",
        user_id=user_id,
        context=voice_result.analysis
    )
    assert chat_followup.success == True
```

#### Phase 4: Complete Integration (Day 6)
**Services**: All 5 services integrated
**Goal**: Complete user journey works seamlessly

```python
# Integration Test 4 - Complete User Journey
def test_complete_user_journey():
    # 1. User Registration and Login
    user = auth_service.register_user("student@test.com", "SecurePass123")
    login = auth_service.login_user("student@test.com", "SecurePass123")
    
    # 2. File Upload and Processing
    file_upload = file_processor.process_upload(
        file_path="physics_notes.pdf",
        user_id=login.user_id,
        token=login.access_token
    )
    
    # 3. AI Chat Interaction
    chat1 = ai_chat.chat_with_ai(
        message="Summarize my physics notes",
        user_id=login.user_id,
        token=login.access_token
    )
    
    # 4. Quiz Generation
    quiz = quiz_generator.generate_quiz(
        topic="physics",
        user_id=login.user_id,
        token=login.access_token
    )
    
    # 5. Voice Interview
    interview = voice_service.start_interview_session(
        topic="physics",
        user_id=login.user_id,
        token=login.access_token
    )
    
    voice_analysis = voice_service.process_voice_response(
        audio_file="physics_explanation.wav",
        session_id=interview.session_id,
        question=interview.question
    )
    
    # 6. Follow-up Chat with Context
    chat2 = ai_chat.chat_with_ai(
        message="Based on my voice interview, what should I study more?",
        user_id=login.user_id,
        context={
            'quiz_results': quiz.results,
            'voice_analysis': voice_analysis.analysis
        }
    )
    
    # Verify complete integration
    assert all([
        user.success,
        login.success,
        file_upload.success,
        chat1.success,
        quiz.success,
        voice_analysis.success,
        chat2.success
    ])
```

## Testing Framework

### Test Environment Setup
```python
# test_environment.py
import pytest
import boto3
from moto import mock_s3, mock_dynamodb, mock_cognito_idp
import tempfile
import os

class TestEnvironment:
    """Unified test environment for all microservices"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_aws_services()
        self.setup_test_data()
    
    @mock_s3
    @mock_dynamodb
    @mock_cognito_idp
    def mock_aws_services(self):
        """Mock AWS services for testing"""
        # Create mock S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-lms-files')
        
        # Create mock DynamoDB tables
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # File metadata table
        dynamodb.create_table(
            TableName='test-file-metadata',
            KeySchema=[{'AttributeName': 'file_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'file_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Chat history table
        dynamodb.create_table(
            TableName='test-chat-history',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create mock Cognito User Pool
        cognito = boto3.client('cognito-idp', region_name='us-east-1')
        user_pool = cognito.create_user_pool(PoolName='test-lms-pool')
        self.user_pool_id = user_pool['UserPool']['Id']
    
    def setup_test_data(self):
        """Create test files and data"""
        # Create sample PDF content
        self.sample_pdf = os.path.join(self.temp_dir, 'sample_notes.pdf')
        self.create_sample_pdf(self.sample_pdf)
        
        # Create sample audio file
        self.sample_audio = os.path.join(self.temp_dir, 'sample_response.wav')
        self.create_sample_audio(self.sample_audio)
    
    def create_sample_pdf(self, file_path):
        """Create a sample PDF for testing"""
        # Simple PDF creation for testing
        with open(file_path, 'w') as f:
            f.write("Sample thermodynamics notes content for testing...")
    
    def create_sample_audio(self, file_path):
        """Create a sample audio file for testing"""
        # Simple audio file creation for testing
        with open(file_path, 'wb') as f:
            f.write(b"fake audio content for testing")

@pytest.fixture(scope="session")
def test_env():
    """Provide test environment for all tests"""
    env = TestEnvironment()
    yield env
    # Cleanup
    import shutil
    shutil.rmtree(env.temp_dir)
```

### Unit Testing Strategy

#### Authentication Service Tests
```python
# test_auth_service.py
class TestAuthService:
    
    def test_user_registration(self, test_env):
        """Test user registration functionality"""
        auth = FastAuth(user_pool_id=test_env.user_pool_id)
        
        result = auth.register_user("test@example.com", "TestPass123")
        
        assert result.success == True
        assert result.user_id is not None
        assert "test@example.com" in result.message
    
    def test_user_login(self, test_env):
        """Test user login functionality"""
        auth = FastAuth(user_pool_id=test_env.user_pool_id)
        
        # Register user first
        auth.register_user("test@example.com", "TestPass123")
        
        # Test login
        result = auth.login_user("test@example.com", "TestPass123")
        
        assert result.success == True
        assert result.access_token is not None
        assert result.user_id is not None
    
    def test_token_validation(self, test_env):
        """Test JWT token validation"""
        auth = FastAuth(user_pool_id=test_env.user_pool_id)
        
        # Create user and get token
        auth.register_user("test@example.com", "TestPass123")
        login_result = auth.login_user("test@example.com", "TestPass123")
        
        # Validate token
        is_valid = auth.validate_token(login_result.access_token)
        
        assert is_valid == True
```

#### File Processor Tests
```python
# test_file_processor.py
class TestFileProcessor:
    
    def test_file_upload(self, test_env):
        """Test file upload to S3"""
        processor = FastFileProcessor(bucket_name='test-lms-files')
        
        result = processor.process_upload(
            file_path=test_env.sample_pdf,
            user_id="test-user-123"
        )
        
        assert result.success == True
        assert result.s3_key is not None
        assert "test-user-123" in result.s3_key
    
    def test_text_extraction(self, test_env):
        """Test text extraction from files"""
        processor = FastFileProcessor()
        
        text = processor.extract_text(test_env.sample_pdf)
        
        assert len(text) > 0
        assert "thermodynamics" in text.lower()
    
    def test_knowledge_base_indexing(self, test_env):
        """Test Knowledge Base indexing"""
        processor = FastFileProcessor()
        
        # Mock Knowledge Base operations
        result = processor.index_content(
            content="Sample thermodynamics content",
            metadata={"user_id": "test-user-123", "file_name": "test.pdf"}
        )
        
        assert result.success == True
```

### Integration Testing Framework

#### Cross-Service Integration Tests
```python
# test_integration.py
class TestServiceIntegration:
    
    def test_auth_file_integration(self, test_env):
        """Test authentication with file processing"""
        # Setup services
        auth = FastAuth(user_pool_id=test_env.user_pool_id)
        file_proc = FastFileProcessor(bucket_name='test-lms-files')
        
        # Register and login user
        auth.register_user("test@example.com", "TestPass123")
        login_result = auth.login_user("test@example.com", "TestPass123")
        
        # Upload file with authentication
        file_result = file_proc.process_upload(
            file_path=test_env.sample_pdf,
            user_id=login_result.user_id,
            token=login_result.access_token
        )
        
        assert file_result.success == True
        assert file_result.user_id == login_result.user_id
    
    def test_file_chat_integration(self, test_env):
        """Test file processing with AI chat"""
        # Setup with processed file
        user_id = "test-user-123"
        
        # Process file
        file_proc = FastFileProcessor()
        file_result = file_proc.process_upload(
            file_path=test_env.sample_pdf,
            user_id=user_id
        )
        
        # Chat about the file
        ai_chat = FastAIChat()
        chat_result = ai_chat.chat_with_ai(
            message="What are the main topics in my notes?",
            user_id=user_id,
            history=[]
        )
        
        assert chat_result[0]  # Updated history
        assert len(chat_result[0]) == 1  # One conversation pair
    
    def test_complete_workflow_integration(self, test_env):
        """Test complete user workflow"""
        # This is the comprehensive test from Phase 4 above
        pass
```

### Performance Testing

#### Load Testing Framework
```python
# test_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class PerformanceTests:
    
    def test_concurrent_file_uploads(self, test_env):
        """Test concurrent file upload performance"""
        file_proc = FastFileProcessor()
        
        def upload_file(user_id):
            start_time = time.time()
            result = file_proc.process_upload(
                file_path=test_env.sample_pdf,
                user_id=f"user-{user_id}"
            )
            end_time = time.time()
            return end_time - start_time, result.success
        
        # Test 10 concurrent uploads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_file, i) for i in range(10)]
            results = [future.result() for future in futures]
        
        # Verify all uploads succeeded
        assert all(result[1] for result in results)
        
        # Verify performance (should be < 30 seconds each)
        assert all(result[0] < 30 for result in results)
    
    def test_chat_response_time(self, test_env):
        """Test AI chat response time"""
        ai_chat = FastAIChat()
        
        start_time = time.time()
        result = ai_chat.chat_with_ai(
            message="Explain thermodynamics",
            user_id="test-user",
            history=[]
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within 5 seconds
        assert response_time < 5.0
        assert result[0]  # Should have response
    
    def test_voice_processing_performance(self, test_env):
        """Test voice processing performance"""
        voice_service = VoiceInterviewAgent()
        
        start_time = time.time()
        result = voice_service.process_voice_response(
            audio_file=test_env.sample_audio,
            session_id="test-session",
            question="Explain entropy"
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should process within 60 seconds
        assert processing_time < 60.0
        assert result['status'] == 'completed'
```

## Testing Schedule

### Daily Testing Checkpoints

#### Day 1 (Authentication Service)
- **Unit Tests**: Registration, login, token validation
- **Integration Tests**: Basic auth flow
- **Performance Tests**: Login response time
- **Manual Tests**: Gradio interface functionality

#### Day 2 (File Processor Service)
- **Unit Tests**: File upload, text extraction, KB indexing
- **Integration Tests**: Auth + File processing
- **Performance Tests**: File upload speed, concurrent uploads
- **Manual Tests**: File management interface

#### Day 3 (AI Chat Service)
- **Unit Tests**: Bedrock Agent integration, conversation management
- **Integration Tests**: Auth + File + Chat
- **Performance Tests**: Chat response time, conversation history
- **Manual Tests**: Chat interface and conversation flow

#### Day 4 (Voice Interview Service)
- **Unit Tests**: Audio processing, transcription, analysis
- **Integration Tests**: Auth + File + Chat + Voice
- **Performance Tests**: Voice processing speed, concurrent interviews
- **Manual Tests**: Voice interview interface and workflow

#### Day 5 (Quiz Generator Service)
- **Unit Tests**: Quiz generation, scoring, feedback
- **Integration Tests**: All services integrated
- **Performance Tests**: Quiz generation speed, concurrent quizzes
- **Manual Tests**: Quiz interface and user experience

#### Day 6 (Complete Integration)
- **End-to-End Tests**: Complete user journeys
- **Load Tests**: System under stress
- **Demo Tests**: Demo scenarios and timing
- **Final Manual Tests**: Complete system validation

### Continuous Integration Pipeline

```yaml
# .github/workflows/ci.yml
name: LMS Microservices CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov moto
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src/
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v
    
    - name: Generate coverage report
      run: |
        coverage report -m
        coverage html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

## Error Handling and Recovery

### Error Scenarios and Testing

#### Network Failures
```python
def test_network_failure_recovery():
    """Test system behavior during network failures"""
    
    # Simulate network failure during file upload
    with mock_network_failure():
        result = file_processor.process_upload(file_path, user_id)
        assert result.success == False
        assert "network" in result.error_message.lower()
    
    # Test recovery after network restoration
    result = file_processor.process_upload(file_path, user_id)
    assert result.success == True
```

#### Service Unavailability
```python
def test_service_unavailability():
    """Test graceful degradation when services are unavailable"""
    
    # Test chat service when Knowledge Base is unavailable
    with mock_bedrock_unavailable():
        result = ai_chat.chat_with_ai("Test question", user_id, [])
        assert "temporarily unavailable" in result[0][0][1].lower()
        assert result[1] == ""  # Input cleared
```

#### Data Corruption
```python
def test_data_corruption_handling():
    """Test handling of corrupted data"""
    
    # Test corrupted file upload
    corrupted_file = create_corrupted_file()
    result = file_processor.process_upload(corrupted_file, user_id)
    
    assert result.success == False
    assert "corrupted" in result.error_message.lower()
```

## Success Metrics

### Technical Metrics
- **Unit Test Coverage**: > 85%
- **Integration Test Coverage**: > 90%
- **Performance Targets Met**: 100%
- **Error Handling Coverage**: > 95%

### User Experience Metrics
- **Complete User Journey Success**: > 95%
- **Interface Responsiveness**: < 2s for all interactions
- **Error Recovery Success**: > 90%
- **Demo Readiness**: 100% of demo scenarios working

### Integration Metrics
- **Cross-Service Communication**: 100% success rate
- **Data Consistency**: 100% across services
- **Authentication Integration**: 100% coverage
- **Real-time Features**: < 3s latency

This comprehensive testing strategy ensures that all microservices work individually and integrate seamlessly for a successful hackathon demo.
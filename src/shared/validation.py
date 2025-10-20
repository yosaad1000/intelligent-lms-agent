"""
Pydantic models for request/response validation
Provides type-safe validation for all API endpoints
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Message types for chat"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationType(str, Enum):
    """Conversation types"""
    GENERAL = "general"
    SUBJECT = "subject"
    QUIZ = "quiz"
    INTERVIEW = "interview"


class ProcessingStatus(str, Enum):
    """File processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    """User roles"""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


# Base Models

class BaseRequest(BaseModel):
    """Base request model with common fields"""
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields
    
    user_id: Optional[str] = Field(None, description="User ID (for testing without auth)")


class BaseResponse(BaseModel):
    """Base response model with common fields"""
    model_config = ConfigDict(extra="allow")
    
    success: bool = Field(description="Whether the request was successful")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str = Field(description="Error code")
    message: str = Field(description="User-friendly error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseResponse):
    """Standardized error response"""
    success: Literal[False] = Field(False, description="Always false for error responses")
    error: ErrorDetail


# Chat API Models

class ChatMessageRequest(BaseRequest):
    """Request model for sending chat messages"""
    message: str = Field(..., min_length=1, max_length=5000, description="Chat message content")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    subject_id: Optional[str] = Field(None, description="Subject context for the chat")
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()


class Citation(BaseModel):
    """Citation information for AI responses"""
    source: str = Field(description="Source document name")
    chunk_index: Optional[int] = Field(None, description="Chunk index in document")
    score: Optional[float] = Field(None, ge=0, le=1, description="Relevance score")
    page: Optional[int] = Field(None, description="Page number if available")


class ChatMessageResponse(BaseResponse):
    """Response model for chat messages"""
    response: str = Field(description="AI response content")
    conversation_id: str = Field(description="Conversation ID")
    citations: List[Citation] = Field(default_factory=list, description="Source citations")
    rag_documents_used: int = Field(0, ge=0, description="Number of RAG documents used")
    rag_enhanced: bool = Field(False, description="Whether RAG was used")
    bedrock_agent_used: bool = Field(True, description="Whether Bedrock Agent was used")
    subject_context: Optional[str] = Field(None, description="Subject context")
    agent_metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")


class ChatMessage(BaseModel):
    """Individual chat message"""
    message_id: str = Field(description="Unique message ID")
    message_type: MessageType = Field(description="Type of message")
    content: str = Field(description="Message content")
    timestamp: int = Field(description="Message timestamp (Unix milliseconds)")
    citations: List[Citation] = Field(default_factory=list)
    context_used: Dict[str, Any] = Field(default_factory=dict, description="Context metadata")


class ConversationHistoryResponse(BaseResponse):
    """Response model for conversation history"""
    conversation_id: Optional[str] = Field(None, description="Conversation ID if specific")
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages")
    total_messages: int = Field(0, ge=0, description="Total number of messages")


class Conversation(BaseModel):
    """Conversation metadata"""
    conversation_id: str = Field(description="Unique conversation ID")
    title: str = Field(description="Conversation title")
    conversation_type: ConversationType = Field(description="Type of conversation")
    subject_id: Optional[str] = Field(None, description="Associated subject ID")
    message_count: int = Field(0, ge=0, description="Number of messages")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class UserConversationsResponse(BaseResponse):
    """Response model for user conversations list"""
    conversations: List[Conversation] = Field(default_factory=list)
    total_conversations: int = Field(0, ge=0)


# File Processing API Models

class FileUploadRequest(BaseRequest):
    """Request model for file upload"""
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_size: int = Field(..., gt=0, le=10*1024*1024, description="File size in bytes")
    subject_id: Optional[str] = Field(None, description="Associated subject ID")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        allowed_extensions = ['.pdf', '.docx', '.txt', '.doc']
        if '.' not in v:
            raise ValueError('Filename must have an extension')
        
        ext = '.' + v.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise ValueError(f'File extension {ext} not supported. Allowed: {", ".join(allowed_extensions)}')
        
        return v


class FileUploadResponse(BaseResponse):
    """Response model for file upload"""
    file_id: str = Field(description="Unique file ID")
    upload_url: str = Field(description="Presigned URL for file upload")
    status: str = Field(description="Upload status")
    process_url: str = Field(description="URL to trigger processing")


class FileProcessingRequest(BaseRequest):
    """Request model for file processing"""
    file_id: str = Field(..., description="File ID to process")


class FileProcessingResponse(BaseResponse):
    """Response model for file processing"""
    file_id: str = Field(description="File ID")
    status: str = Field(description="Processing status")
    chunks_created: int = Field(0, ge=0, description="Number of text chunks created")
    vectors_stored: int = Field(0, ge=0, description="Number of vectors stored")
    message: str = Field(description="Status message")


class FileMetadata(BaseModel):
    """File metadata information"""
    file_id: str = Field(description="Unique file ID")
    filename: str = Field(description="Original filename")
    file_size: int = Field(ge=0, description="File size in bytes")
    status: str = Field(description="File status")
    processing_status: ProcessingStatus = Field(description="Processing status")
    text_extraction_status: ProcessingStatus = Field(description="Text extraction status")
    vector_storage_status: ProcessingStatus = Field(description="Vector storage status")
    upload_timestamp: str = Field(description="Upload timestamp")
    subject_id: Optional[str] = Field(None, description="Associated subject ID")
    chunks_created: int = Field(0, ge=0, description="Number of chunks created")
    vectors_stored: int = Field(0, ge=0, description="Number of vectors stored")
    content_preview: str = Field("", description="Preview of extracted content")


class UserFilesResponse(BaseResponse):
    """Response model for user files list"""
    files: List[FileMetadata] = Field(default_factory=list)
    total: int = Field(0, ge=0, description="Total number of files")


class FileStatusResponse(BaseResponse):
    """Response model for file status"""
    file_id: str = Field(description="File ID")
    filename: str = Field(description="Original filename")
    processing_status: ProcessingStatus = Field(description="Processing status")
    text_extraction_status: ProcessingStatus = Field(description="Text extraction status")
    vector_storage_status: ProcessingStatus = Field(description="Vector storage status")
    chunks_created: int = Field(0, ge=0)
    vectors_stored: int = Field(0, ge=0)
    upload_timestamp: str = Field(description="Upload timestamp")
    error_message: str = Field("", description="Error message if failed")


# Quiz API Models

class QuizGenerationRequest(BaseRequest):
    """Request model for quiz generation"""
    subject_id: Optional[str] = Field(None, description="Subject context")
    document_ids: Optional[List[str]] = Field(None, description="Specific documents to use")
    num_questions: int = Field(5, ge=1, le=20, description="Number of questions to generate")
    difficulty: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")
    question_types: Optional[List[str]] = Field(None, description="Types of questions to generate")


class QuizOption(BaseModel):
    """Quiz question option"""
    option_id: str = Field(description="Option identifier (A, B, C, D)")
    text: str = Field(description="Option text")
    is_correct: bool = Field(description="Whether this is the correct answer")


class QuizQuestion(BaseModel):
    """Quiz question"""
    question_id: str = Field(description="Unique question ID")
    question_text: str = Field(description="Question text")
    options: List[QuizOption] = Field(description="Answer options")
    explanation: Optional[str] = Field(None, description="Explanation of correct answer")
    source_document: Optional[str] = Field(None, description="Source document")
    difficulty: str = Field(description="Question difficulty level")


class QuizGenerationResponse(BaseResponse):
    """Response model for quiz generation"""
    quiz_id: str = Field(description="Unique quiz ID")
    questions: List[QuizQuestion] = Field(description="Generated questions")
    subject_id: Optional[str] = Field(None, description="Subject context")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class QuizSubmissionRequest(BaseRequest):
    """Request model for quiz submission"""
    quiz_id: str = Field(..., description="Quiz ID")
    answers: Dict[str, str] = Field(..., description="Question ID to answer mapping")


class QuizResult(BaseModel):
    """Quiz result for individual question"""
    question_id: str = Field(description="Question ID")
    user_answer: str = Field(description="User's answer")
    correct_answer: str = Field(description="Correct answer")
    is_correct: bool = Field(description="Whether user answer is correct")
    explanation: Optional[str] = Field(None, description="Answer explanation")


class QuizSubmissionResponse(BaseResponse):
    """Response model for quiz submission"""
    quiz_id: str = Field(description="Quiz ID")
    score: float = Field(ge=0, le=100, description="Score percentage")
    total_questions: int = Field(ge=0, description="Total number of questions")
    correct_answers: int = Field(ge=0, description="Number of correct answers")
    results: List[QuizResult] = Field(description="Detailed results")
    submitted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Health API Models

class ServiceStatus(BaseModel):
    """Individual service status"""
    service: str = Field(description="Service name")
    status: str = Field(description="Service status")
    details: Optional[str] = Field(None, description="Additional status details")


class HealthResponse(BaseResponse):
    """Response model for health check"""
    status: str = Field(description="Overall system status")
    services: List[ServiceStatus] = Field(description="Individual service statuses")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Voice Interview API Models

class VoiceInterviewStartRequest(BaseRequest):
    """Request model for starting voice interview"""
    subject_id: Optional[str] = Field(None, description="Subject context")
    interview_type: str = Field("general", description="Type of interview")
    duration_minutes: int = Field(15, ge=5, le=60, description="Interview duration")


class VoiceInterviewStartResponse(BaseResponse):
    """Response model for voice interview start"""
    session_id: str = Field(description="Interview session ID")
    websocket_url: str = Field(description="WebSocket URL for audio streaming")
    initial_question: str = Field(description="First interview question")


class VoiceInterviewMessage(BaseModel):
    """WebSocket message for voice interview"""
    type: str = Field(description="Message type")
    session_id: str = Field(description="Session ID")
    data: Dict[str, Any] = Field(description="Message data")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Analytics API Models

class LearningAnalyticsRequest(BaseRequest):
    """Request model for learning analytics"""
    subject_id: Optional[str] = Field(None, description="Subject filter")
    date_from: Optional[str] = Field(None, description="Start date (ISO format)")
    date_to: Optional[str] = Field(None, description="End date (ISO format)")


class ConceptMastery(BaseModel):
    """Concept mastery information"""
    concept: str = Field(description="Concept name")
    mastery_level: float = Field(ge=0, le=1, description="Mastery level (0-1)")
    interaction_count: int = Field(ge=0, description="Number of interactions")
    last_interaction: str = Field(description="Last interaction timestamp")


class LearningAnalyticsResponse(BaseResponse):
    """Response model for learning analytics"""
    user_id: str = Field(description="User ID")
    total_interactions: int = Field(ge=0, description="Total interactions")
    documents_processed: int = Field(ge=0, description="Documents processed")
    quizzes_taken: int = Field(ge=0, description="Quizzes taken")
    average_score: float = Field(ge=0, le=100, description="Average quiz score")
    study_time_hours: float = Field(ge=0, description="Total study time")
    concept_masteries: List[ConceptMastery] = Field(description="Concept mastery levels")
    recommendations: List[str] = Field(description="Learning recommendations")


# Utility Functions

def validate_request_model(model_class: BaseModel, data: Dict[str, Any]) -> BaseModel:
    """
    Validate request data against Pydantic model
    
    Args:
        model_class: Pydantic model class
        data: Request data dictionary
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationException: If validation fails
    """
    from .exceptions import ValidationException
    
    try:
        return model_class(**data)
    except Exception as e:
        raise ValidationException(
            message=f"Request validation failed: {str(e)}",
            details={'validation_errors': str(e)}
        )


def create_success_response(model_class: BaseModel, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create validated success response
    
    Args:
        model_class: Pydantic response model class
        data: Response data dictionary
        
    Returns:
        Validated response dictionary
    """
    
    try:
        response_model = model_class(**data)
        return response_model.dict()
    except Exception as e:
        # Fallback to basic response if validation fails
        return {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            **data
        }
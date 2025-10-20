"""
Test API error handling and validation
Tests comprehensive error scenarios, validation, and exception handling
"""

import json
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from shared.exceptions import (
    LMSException, ValidationException, AuthenticationException, 
    AuthorizationException, ResourceNotFoundException, BedrockAgentException,
    FileProcessingException, AWSServiceException, ErrorCode,
    create_error_response, lambda_error_handler, validate_required_fields,
    validate_file_upload, log_api_request, log_api_response
)
from shared.validation import (
    ChatMessageRequest, FileUploadRequest, validate_request_model,
    create_success_response, ChatMessageResponse
)
from shared.logging_config import setup_logging, get_logger


class TestLMSExceptions:
    """Test custom exception classes"""
    
    def test_lms_exception_basic(self):
        """Test basic LMS exception"""
        
        exception = LMSException(
            message="Test error",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500
        )
        
        assert exception.message == "Test error"
        assert exception.error_code == ErrorCode.INTERNAL_ERROR
        assert exception.status_code == 500
        assert exception.user_message == "Test error"
        assert exception.details == {}
        assert exception.timestamp is not None
    
    def test_validation_exception(self):
        """Test validation exception"""
        
        exception = ValidationException(
            message="Invalid field",
            field="email",
            details={"reason": "Invalid format"}
        )
        
        assert exception.error_code == ErrorCode.VALIDATION_ERROR
        assert exception.status_code == 400
        assert exception.details['field'] == "email"
        assert exception.details['reason'] == "Invalid format"
        assert "Validation error" in exception.user_message
    
    def test_authentication_exception(self):
        """Test authentication exception"""
        
        exception = AuthenticationException()
        
        assert exception.error_code == ErrorCode.UNAUTHORIZED
        assert exception.status_code == 401
        assert "log in" in exception.user_message.lower()
    
    def test_authorization_exception(self):
        """Test authorization exception"""
        
        exception = AuthorizationException()
        
        assert exception.error_code == ErrorCode.FORBIDDEN
        assert exception.status_code == 403
        assert "permission" in exception.user_message.lower()
    
    def test_resource_not_found_exception(self):
        """Test resource not found exception"""
        
        exception = ResourceNotFoundException("File", "file-123")
        
        assert exception.error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert exception.status_code == 404
        assert exception.details['resource_type'] == "File"
        assert exception.details['resource_id'] == "file-123"
        assert "file" in exception.user_message.lower()
    
    def test_bedrock_agent_exception(self):
        """Test Bedrock Agent exception"""
        
        exception = BedrockAgentException(
            message="Agent timeout",
            agent_id="agent-123",
            details={"timeout_seconds": 30}
        )
        
        assert exception.error_code == ErrorCode.BEDROCK_ERROR
        assert exception.status_code == 503
        assert exception.details['agent_id'] == "agent-123"
        assert exception.details['timeout_seconds'] == 30
        assert "temporarily unavailable" in exception.user_message.lower()
    
    def test_file_processing_exception(self):
        """Test file processing exception"""
        
        exception = FileProcessingException(
            message="Text extraction failed",
            file_id="file-123",
            processing_stage="text_extraction"
        )
        
        assert exception.error_code == ErrorCode.PROCESSING_FAILED
        assert exception.status_code == 422
        assert exception.details['file_id'] == "file-123"
        assert exception.details['processing_stage'] == "text_extraction"
    
    def test_aws_service_exception(self):
        """Test AWS service exception"""
        
        exception = AWSServiceException(
            service="DynamoDB",
            message="Table not found",
            aws_error_code="ResourceNotFoundException"
        )
        
        assert exception.error_code == ErrorCode.AWS_SERVICE_ERROR
        assert exception.status_code == 503
        assert exception.details['service'] == "DynamoDB"
        assert exception.details['aws_error_code'] == "ResourceNotFoundException"


class TestErrorResponseCreation:
    """Test error response creation"""
    
    def test_create_error_response_lms_exception(self):
        """Test creating error response from LMS exception"""
        
        exception = ValidationException(
            message="Invalid email format",
            field="email"
        )
        
        response = create_error_response(exception)
        
        assert response['success'] is False
        assert response['error']['code'] == ErrorCode.VALIDATION_ERROR.value
        assert response['error']['message'] == "Validation error: Invalid email format"
        assert response['error']['details']['field'] == "email"
        assert 'timestamp' in response['error']
    
    def test_create_error_response_generic_exception(self):
        """Test creating error response from generic exception"""
        
        exception = ValueError("Something went wrong")
        
        response = create_error_response(exception)
        
        assert response['success'] is False
        assert response['error']['code'] == ErrorCode.INTERNAL_ERROR.value
        assert response['error']['message'] == "An unexpected error occurred. Please try again."
        assert 'timestamp' in response['error']
    
    def test_create_error_response_with_traceback(self):
        """Test creating error response with traceback"""
        
        exception = ValidationException("Test error")
        
        response = create_error_response(exception, include_traceback=True)
        
        assert 'technical_message' in response['error']
        assert 'traceback' in response['error']


class TestLambdaErrorHandler:
    """Test Lambda error handler decorator"""
    
    def test_lambda_error_handler_success(self):
        """Test Lambda error handler with successful function"""
        
        @lambda_error_handler
        def test_lambda(event, context):
            return {
                'statusCode': 200,
                'body': json.dumps({'success': True})
            }
        
        result = test_lambda({}, {})
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['success'] is True
    
    def test_lambda_error_handler_lms_exception(self):
        """Test Lambda error handler with LMS exception"""
        
        @lambda_error_handler
        def test_lambda(event, context):
            raise ValidationException("Invalid input")
        
        result = test_lambda({}, {})
        
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error']['code'] == ErrorCode.VALIDATION_ERROR.value
    
    def test_lambda_error_handler_generic_exception(self):
        """Test Lambda error handler with generic exception"""
        
        @lambda_error_handler
        def test_lambda(event, context):
            raise ValueError("Something went wrong")
        
        result = test_lambda({}, {})
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error']['code'] == ErrorCode.INTERNAL_ERROR.value


class TestValidationFunctions:
    """Test validation utility functions"""
    
    def test_validate_required_fields_success(self):
        """Test successful required fields validation"""
        
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        }
        
        # Should not raise exception
        validate_required_fields(data, ['name', 'email'])
    
    def test_validate_required_fields_missing(self):
        """Test required fields validation with missing fields"""
        
        data = {
            'name': 'John Doe'
        }
        
        with pytest.raises(ValidationException) as exc_info:
            validate_required_fields(data, ['name', 'email', 'age'])
        
        assert 'email' in exc_info.value.message
        assert 'age' in exc_info.value.message
        assert exc_info.value.details['missing_fields'] == ['email', 'age']
    
    def test_validate_required_fields_empty_values(self):
        """Test required fields validation with empty values"""
        
        data = {
            'name': '',
            'email': None,
            'age': 30
        }
        
        with pytest.raises(ValidationException) as exc_info:
            validate_required_fields(data, ['name', 'email', 'age'])
        
        assert exc_info.value.details['missing_fields'] == ['name', 'email']
    
    def test_validate_file_upload_success(self):
        """Test successful file upload validation"""
        
        # Should not raise exception
        validate_file_upload("document.pdf", 1024 * 1024)  # 1MB
    
    def test_validate_file_upload_no_filename(self):
        """Test file upload validation with no filename"""
        
        with pytest.raises(ValidationException) as exc_info:
            validate_file_upload("", 1024)
        
        assert "Filename is required" in exc_info.value.message
        assert exc_info.value.details.get('field') == 'filename'
    
    def test_validate_file_upload_invalid_extension(self):
        """Test file upload validation with invalid extension"""
        
        with pytest.raises(ValidationException) as exc_info:
            validate_file_upload("virus.exe", 1024)
        
        assert "not supported" in exc_info.value.message
        assert exc_info.value.details.get('field') == 'filename'
    
    def test_validate_file_upload_too_large(self):
        """Test file upload validation with file too large"""
        
        with pytest.raises(ValidationException) as exc_info:
            validate_file_upload("large.pdf", 20 * 1024 * 1024)  # 20MB
        
        assert "exceeds limit" in exc_info.value.message
        assert exc_info.value.details.get('field') == 'file_size'


class TestPydanticValidation:
    """Test Pydantic model validation"""
    
    def test_chat_message_request_valid(self):
        """Test valid chat message request"""
        
        data = {
            'message': 'Hello, how are you?',
            'user_id': 'test-user'
        }
        
        model = validate_request_model(ChatMessageRequest, data)
        
        assert model.message == 'Hello, how are you?'
        assert model.user_id == 'test-user'
        assert model.conversation_id is None
    
    def test_chat_message_request_missing_message(self):
        """Test chat message request with missing message"""
        
        data = {
            'user_id': 'test-user'
        }
        
        with pytest.raises(ValidationException) as exc_info:
            validate_request_model(ChatMessageRequest, data)
        
        assert "validation failed" in exc_info.value.message.lower()
    
    def test_chat_message_request_empty_message(self):
        """Test chat message request with empty message"""
        
        data = {
            'message': '   ',
            'user_id': 'test-user'
        }
        
        with pytest.raises(ValidationException) as exc_info:
            validate_request_model(ChatMessageRequest, data)
        
        assert "validation failed" in exc_info.value.message.lower()
    
    def test_chat_message_request_message_too_long(self):
        """Test chat message request with message too long"""
        
        data = {
            'message': 'x' * 6000,  # Exceeds 5000 char limit
            'user_id': 'test-user'
        }
        
        with pytest.raises(ValidationException) as exc_info:
            validate_request_model(ChatMessageRequest, data)
        
        assert "validation failed" in exc_info.value.message.lower()
    
    def test_file_upload_request_valid(self):
        """Test valid file upload request"""
        
        data = {
            'filename': 'document.pdf',
            'file_size': 1024 * 1024,
            'user_id': 'test-user'
        }
        
        model = validate_request_model(FileUploadRequest, data)
        
        assert model.filename == 'document.pdf'
        assert model.file_size == 1024 * 1024
        assert model.user_id == 'test-user'
    
    def test_file_upload_request_invalid_extension(self):
        """Test file upload request with invalid extension"""
        
        data = {
            'filename': 'virus.exe',
            'file_size': 1024,
            'user_id': 'test-user'
        }
        
        with pytest.raises(ValidationException) as exc_info:
            validate_request_model(FileUploadRequest, data)
        
        assert "validation failed" in exc_info.value.message.lower()
    
    def test_file_upload_request_file_too_large(self):
        """Test file upload request with file too large"""
        
        data = {
            'filename': 'large.pdf',
            'file_size': 20 * 1024 * 1024,  # 20MB
            'user_id': 'test-user'
        }
        
        with pytest.raises(ValidationException) as exc_info:
            validate_request_model(FileUploadRequest, data)
        
        assert "validation failed" in exc_info.value.message.lower()
    
    def test_create_success_response(self):
        """Test creating success response"""
        
        data = {
            'success': True,
            'response': 'Hello there!',
            'conversation_id': 'conv-123',
            'citations': [],
            'rag_documents_used': 0,
            'rag_enhanced': False,
            'bedrock_agent_used': True
        }
        
        response = create_success_response(ChatMessageResponse, data)
        
        assert response['success'] is True
        assert response['response'] == 'Hello there!'
        assert response['conversation_id'] == 'conv-123'
        assert 'timestamp' in response
    
    def test_create_success_response_validation_failure(self):
        """Test creating success response with validation failure"""
        
        data = {
            'invalid_field': 'value'
        }
        
        response = create_success_response(ChatMessageResponse, data)
        
        # Should fallback to basic response
        assert response['success'] is True
        assert 'timestamp' in response
        assert response['invalid_field'] == 'value'


class TestLoggingIntegration:
    """Test logging integration"""
    
    def setup_method(self):
        """Setup test logging"""
        self.logger = setup_logging(level='DEBUG', format_type='json')
    
    def test_log_api_request(self):
        """Test API request logging"""
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/chat',
            'requestContext': {
                'identity': {
                    'sourceIp': '192.168.1.1'
                }
            },
            'headers': {
                'User-Agent': 'Test-Client/1.0'
            },
            'body': json.dumps({'message': 'Hello'})
        }
        
        # Should not raise exception
        log_api_request(event, user_id='test-user')
    
    def test_log_api_response(self):
        """Test API response logging"""
        
        response = {
            'statusCode': 200,
            'body': json.dumps({'success': True})
        }
        
        # Should not raise exception
        log_api_response(response, duration_ms=150.5)
    
    def test_log_api_response_error(self):
        """Test API response logging with error"""
        
        response = {
            'statusCode': 400,
            'body': json.dumps({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input'
                }
            })
        }
        
        # Should not raise exception
        log_api_response(response, duration_ms=50.0)


class TestErrorScenarios:
    """Test various error scenarios"""
    
    def test_multiple_validation_errors(self):
        """Test handling multiple validation errors"""
        
        data = {}
        
        with pytest.raises(ValidationException) as exc_info:
            validate_required_fields(data, ['name', 'email', 'phone'])
        
        missing_fields = exc_info.value.details['missing_fields']
        assert len(missing_fields) == 3
        assert 'name' in missing_fields
        assert 'email' in missing_fields
        assert 'phone' in missing_fields
    
    def test_nested_exception_handling(self):
        """Test nested exception handling"""
        
        @lambda_error_handler
        def outer_function(event, context):
            def inner_function():
                raise ValidationException("Inner validation error")
            
            try:
                inner_function()
            except ValidationException:
                raise BedrockAgentException("Agent processing failed")
        
        result = outer_function({}, {})
        
        assert result['statusCode'] == 503
        body = json.loads(result['body'])
        assert body['error']['code'] == ErrorCode.BEDROCK_ERROR.value
    
    def test_error_response_serialization(self):
        """Test error response JSON serialization"""
        
        exception = ValidationException(
            message="Test error",
            details={'timestamp': datetime.utcnow()}
        )
        
        response = create_error_response(exception)
        
        # Should be JSON serializable
        json_str = json.dumps(response, default=str)
        parsed = json.loads(json_str)
        
        assert parsed['success'] is False
        assert parsed['error']['code'] == ErrorCode.VALIDATION_ERROR.value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
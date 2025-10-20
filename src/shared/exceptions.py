"""
Global exception handling for LMS API
Provides standardized error responses and exception classes
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for the LMS API"""
    
    # Authentication & Authorization (4xx)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Validation Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    
    # Resource Errors (4xx)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    
    # Business Logic Errors (4xx)
    PROCESSING_FAILED = "PROCESSING_FAILED"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    
    # Server Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    AWS_SERVICE_ERROR = "AWS_SERVICE_ERROR"
    BEDROCK_ERROR = "BEDROCK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class LMSException(Exception):
    """Base exception class for LMS API"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or message
        self.timestamp = datetime.utcnow().isoformat()


class ValidationException(LMSException):
    """Exception for validation errors"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details=details or {},
            user_message=f"Validation error: {message}"
        )
        if field:
            self.details['field'] = field


class AuthenticationException(LMSException):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            user_message="Please log in to access this resource"
        )


class AuthorizationException(LMSException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
            user_message="You don't have permission to access this resource"
        )


class ResourceNotFoundException(LMSException):
    """Exception for resource not found errors"""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details={'resource_type': resource_type, 'resource_id': resource_id},
            user_message=f"The requested {resource_type.lower()} could not be found"
        )


class BedrockAgentException(LMSException):
    """Exception for Bedrock Agent errors"""
    
    def __init__(self, message: str, agent_id: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.BEDROCK_ERROR,
            status_code=503,
            details=details or {},
            user_message="AI service is temporarily unavailable. Please try again."
        )
        if agent_id:
            self.details['agent_id'] = agent_id


class FileProcessingException(LMSException):
    """Exception for file processing errors"""
    
    def __init__(self, message: str, file_id: str = None, processing_stage: str = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PROCESSING_FAILED,
            status_code=422,
            details={'file_id': file_id, 'processing_stage': processing_stage},
            user_message="File processing failed. Please check the file format and try again."
        )


class AWSServiceException(LMSException):
    """Exception for AWS service errors"""
    
    def __init__(self, service: str, message: str, aws_error_code: str = None):
        super().__init__(
            message=f"{service} error: {message}",
            error_code=ErrorCode.AWS_SERVICE_ERROR,
            status_code=503,
            details={'service': service, 'aws_error_code': aws_error_code},
            user_message="A service is temporarily unavailable. Please try again later."
        )


def create_error_response(
    exception: Union[LMSException, Exception],
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Create standardized error response from exception
    
    Args:
        exception: The exception to convert to error response
        include_traceback: Whether to include stack trace (for debugging)
        
    Returns:
        Dictionary containing error response
    """
    
    if isinstance(exception, LMSException):
        error_response = {
            'error': {
                'code': exception.error_code.value,
                'message': exception.user_message,
                'details': exception.details,
                'timestamp': exception.timestamp
            },
            'success': False
        }
        
        # Add technical details for debugging
        if include_traceback or logger.isEnabledFor(logging.DEBUG):
            error_response['error']['technical_message'] = exception.message
            if include_traceback:
                error_response['error']['traceback'] = traceback.format_exc()
        
        return error_response
    
    else:
        # Handle unexpected exceptions
        error_response = {
            'error': {
                'code': ErrorCode.INTERNAL_ERROR.value,
                'message': 'An unexpected error occurred. Please try again.',
                'details': {},
                'timestamp': datetime.utcnow().isoformat()
            },
            'success': False
        }
        
        # Add technical details for debugging
        if include_traceback or logger.isEnabledFor(logging.DEBUG):
            error_response['error']['technical_message'] = str(exception)
            if include_traceback:
                error_response['error']['traceback'] = traceback.format_exc()
        
        return error_response


def lambda_error_handler(func):
    """
    Decorator for Lambda functions to handle exceptions and return standardized responses
    
    Usage:
        @lambda_error_handler
        def lambda_handler(event, context):
            # Your Lambda function code
    """
    
    def wrapper(event, context):
        try:
            return func(event, context)
        
        except LMSException as e:
            logger.error(f"LMS Exception in {func.__name__}: {e.message}", extra={
                'error_code': e.error_code.value,
                'status_code': e.status_code,
                'details': e.details,
                'event': event
            })
            
            error_response = create_error_response(e, include_traceback=False)
            
            return {
                'statusCode': e.status_code,
                'headers': get_cors_headers(),
                'body': json.dumps(error_response)
            }
        
        except Exception as e:
            logger.error(f"Unexpected exception in {func.__name__}: {str(e)}", extra={
                'traceback': traceback.format_exc(),
                'event': event
            })
            
            error_response = create_error_response(e, include_traceback=False)
            
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps(error_response)
            }
    
    return wrapper


def get_cors_headers() -> Dict[str, str]:
    """Get standardized CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in request data
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
        
    Raises:
        ValidationException: If any required field is missing
    """
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationException(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            details={'missing_fields': missing_fields}
        )


def validate_file_upload(filename: str, file_size: int, max_size_mb: int = 10) -> None:
    """
    Validate file upload parameters
    
    Args:
        filename: Name of the file
        file_size: Size of the file in bytes
        max_size_mb: Maximum allowed file size in MB
        
    Raises:
        ValidationException: If validation fails
    """
    
    if not filename:
        raise ValidationException("Filename is required", field="filename")
    
    # Check file extension
    allowed_extensions = ['.pdf', '.docx', '.txt', '.doc']
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if f'.{file_ext}' not in allowed_extensions:
        raise ValidationException(
            f"File type '.{file_ext}' not supported. Allowed: {', '.join(allowed_extensions)}",
            field="filename",
            details={'allowed_extensions': allowed_extensions}
        )
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise ValidationException(
            f"File size {file_size} bytes exceeds limit of {max_size_mb}MB",
            field="file_size",
            details={'max_size_bytes': max_size_bytes, 'actual_size': file_size}
        )


def log_api_request(event: Dict[str, Any], user_id: str = None) -> None:
    """
    Log API request for monitoring and debugging
    
    Args:
        event: Lambda event object
        user_id: User ID if available
    """
    
    request_info = {
        'method': event.get('httpMethod'),
        'path': event.get('path'),
        'user_id': user_id,
        'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
        'user_agent': event.get('headers', {}).get('User-Agent'),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Don't log sensitive data
    if event.get('body'):
        try:
            body = json.loads(event['body'])
            # Remove sensitive fields
            safe_body = {k: v for k, v in body.items() if k not in ['password', 'token', 'secret']}
            request_info['body_keys'] = list(safe_body.keys())
        except:
            request_info['body_size'] = len(event['body'])
    
    logger.info("API Request", extra=request_info)


def log_api_response(response: Dict[str, Any], duration_ms: float = None) -> None:
    """
    Log API response for monitoring
    
    Args:
        response: Lambda response object
        duration_ms: Request duration in milliseconds
    """
    
    response_info = {
        'status_code': response.get('statusCode'),
        'duration_ms': duration_ms,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Check if response indicates error
    if response.get('statusCode', 200) >= 400:
        try:
            body = json.loads(response.get('body', '{}'))
            if 'error' in body:
                response_info['error_code'] = body['error'].get('code')
        except:
            pass
    
    logger.info("API Response", extra=response_info)
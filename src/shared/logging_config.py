"""
Comprehensive logging configuration for LMS API
Provides structured logging with proper formatting and monitoring integration
"""

import logging
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger


class LMSFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for LMS logging"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service information
        log_record['service'] = 'lms-api'
        log_record['version'] = os.getenv('APP_VERSION', '1.0.0')
        
        # Add AWS Lambda context if available
        if hasattr(record, 'aws_request_id'):
            log_record['aws_request_id'] = record.aws_request_id
        
        # Add user context if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        # Add correlation ID for request tracing
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        
        # Ensure level is always present
        if 'level' not in log_record:
            log_record['level'] = record.levelname


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""
    
    def __init__(self):
        super().__init__()
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context variables for current request"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context variables"""
        self.context.clear()
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


# Global request context filter
request_context = RequestContextFilter()


def setup_logging(
    level: str = None,
    format_type: str = 'json',
    include_request_context: bool = True
) -> logging.Logger:
    """
    Set up comprehensive logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ('json' or 'text')
        include_request_context: Whether to include request context
        
    Returns:
        Configured logger instance
    """
    
    # Determine log level
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Get root logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set log level
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter
    if format_type == 'json':
        formatter = LMSFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    
    # Add request context filter
    if include_request_context:
        handler.addFilter(request_context)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Configure specific loggers
    configure_aws_logging()
    configure_third_party_logging()
    
    return logger


def configure_aws_logging():
    """Configure AWS SDK logging"""
    
    # Reduce AWS SDK logging noise
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Keep important AWS errors
    logging.getLogger('botocore.client').setLevel(logging.ERROR)


def configure_third_party_logging():
    """Configure third-party library logging"""
    
    # Reduce third-party logging noise
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('pinecone').setLevel(logging.INFO)
    
    # Keep important errors
    logging.getLogger('langchain').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with proper configuration
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    
    logger = logging.getLogger(name)
    
    # Ensure logger inherits from root logger configuration
    if not logger.handlers and logger.parent:
        logger.handlers = logger.parent.handlers
    
    return logger


def log_lambda_start(event: Dict[str, Any], context: Any, logger: logging.Logger) -> str:
    """
    Log Lambda function start with context
    
    Args:
        event: Lambda event
        context: Lambda context
        logger: Logger instance
        
    Returns:
        Correlation ID for request tracing
    """
    
    import uuid
    correlation_id = str(uuid.uuid4())
    
    # Set request context
    request_context.set_context(
        aws_request_id=getattr(context, 'aws_request_id', None),
        correlation_id=correlation_id,
        function_name=getattr(context, 'function_name', None),
        function_version=getattr(context, 'function_version', None)
    )
    
    # Log function start
    logger.info("Lambda function started", extra={
        'event_type': 'lambda_start',
        'http_method': event.get('httpMethod'),
        'path': event.get('path'),
        'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
        'user_agent': event.get('headers', {}).get('User-Agent'),
        'correlation_id': correlation_id
    })
    
    return correlation_id


def log_lambda_end(
    response: Dict[str, Any],
    duration_ms: float,
    logger: logging.Logger,
    correlation_id: str = None
) -> None:
    """
    Log Lambda function end with metrics
    
    Args:
        response: Lambda response
        duration_ms: Execution duration in milliseconds
        logger: Logger instance
        correlation_id: Request correlation ID
    """
    
    status_code = response.get('statusCode', 200)
    
    logger.info("Lambda function completed", extra={
        'event_type': 'lambda_end',
        'status_code': status_code,
        'duration_ms': duration_ms,
        'success': status_code < 400,
        'correlation_id': correlation_id
    })
    
    # Clear request context
    request_context.clear_context()


def log_api_call(
    service: str,
    operation: str,
    duration_ms: float = None,
    success: bool = True,
    error: str = None,
    logger: logging.Logger = None
) -> None:
    """
    Log external API calls
    
    Args:
        service: Service name (e.g., 'bedrock', 's3', 'dynamodb')
        operation: Operation name (e.g., 'invoke_agent', 'put_object')
        duration_ms: Operation duration in milliseconds
        success: Whether operation was successful
        error: Error message if failed
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    log_data = {
        'event_type': 'api_call',
        'service': service,
        'operation': operation,
        'success': success
    }
    
    if duration_ms is not None:
        log_data['duration_ms'] = duration_ms
    
    if error:
        log_data['error'] = error
    
    if success:
        logger.info(f"API call successful: {service}.{operation}", extra=log_data)
    else:
        logger.error(f"API call failed: {service}.{operation}", extra=log_data)


def log_user_action(
    user_id: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: Dict[str, Any] = None,
    logger: logging.Logger = None
) -> None:
    """
    Log user actions for analytics and auditing
    
    Args:
        user_id: User identifier
        action: Action performed (e.g., 'upload_file', 'send_message')
        resource_type: Type of resource (e.g., 'file', 'conversation')
        resource_id: Resource identifier
        details: Additional action details
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    # Set user context
    request_context.set_context(user_id=user_id)
    
    log_data = {
        'event_type': 'user_action',
        'user_id': user_id,
        'action': action
    }
    
    if resource_type:
        log_data['resource_type'] = resource_type
    
    if resource_id:
        log_data['resource_id'] = resource_id
    
    if details:
        log_data['details'] = details
    
    logger.info(f"User action: {action}", extra=log_data)


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = 'ms',
    tags: Dict[str, str] = None,
    logger: logging.Logger = None
) -> None:
    """
    Log performance metrics
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        tags: Additional tags for the metric
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    log_data = {
        'event_type': 'performance_metric',
        'metric_name': metric_name,
        'value': value,
        'unit': unit
    }
    
    if tags:
        log_data['tags'] = tags
    
    logger.info(f"Performance metric: {metric_name}={value}{unit}", extra=log_data)


def log_security_event(
    event_type: str,
    user_id: str = None,
    source_ip: str = None,
    details: Dict[str, Any] = None,
    severity: str = 'INFO',
    logger: logging.Logger = None
) -> None:
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        user_id: User identifier if available
        source_ip: Source IP address
        details: Additional event details
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    log_data = {
        'event_type': 'security_event',
        'security_event_type': event_type,
        'severity': severity
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    if source_ip:
        log_data['source_ip'] = source_ip
    
    if details:
        log_data['details'] = details
    
    level = getattr(logging, severity, logging.INFO)
    logger.log(level, f"Security event: {event_type}", extra=log_data)


def log_validation_error(
    field: str,
    value: Any,
    error_message: str,
    user_id: str = None,
    logger: logging.Logger = None
) -> None:
    """
    Log validation errors for monitoring and security
    
    Args:
        field: Field that failed validation
        value: Value that failed (sanitized)
        error_message: Validation error message
        user_id: User identifier if available
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    # Sanitize sensitive values
    sanitized_value = str(value)[:100] if value else None
    if field.lower() in ['password', 'token', 'secret', 'key']:
        sanitized_value = '[REDACTED]'
    
    log_data = {
        'event_type': 'validation_error',
        'field': field,
        'value': sanitized_value,
        'error_message': error_message
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    logger.warning(f"Validation error for field '{field}': {error_message}", extra=log_data)


def log_rate_limit_event(
    user_id: str,
    endpoint: str,
    limit_type: str,
    current_count: int,
    limit: int,
    source_ip: str = None,
    logger: logging.Logger = None
) -> None:
    """
    Log rate limiting events
    
    Args:
        user_id: User identifier
        endpoint: API endpoint
        limit_type: Type of rate limit (requests_per_minute, files_per_hour, etc.)
        current_count: Current request count
        limit: Rate limit threshold
        source_ip: Source IP address
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    log_data = {
        'event_type': 'rate_limit',
        'user_id': user_id,
        'endpoint': endpoint,
        'limit_type': limit_type,
        'current_count': current_count,
        'limit': limit,
        'exceeded': current_count >= limit
    }
    
    if source_ip:
        log_data['source_ip'] = source_ip
    
    if current_count >= limit:
        logger.warning(f"Rate limit exceeded for user {user_id} on {endpoint}", extra=log_data)
    else:
        logger.info(f"Rate limit check for user {user_id} on {endpoint}", extra=log_data)


def log_business_event(
    event_type: str,
    user_id: str,
    details: Dict[str, Any] = None,
    logger: logging.Logger = None
) -> None:
    """
    Log business events for analytics and monitoring
    
    Args:
        event_type: Type of business event (file_uploaded, quiz_completed, etc.)
        user_id: User identifier
        details: Additional event details
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    log_data = {
        'event_type': 'business_event',
        'business_event_type': event_type,
        'user_id': user_id
    }
    
    if details:
        log_data['details'] = details
    
    logger.info(f"Business event: {event_type} for user {user_id}", extra=log_data)


def log_error_with_context(
    error: Exception,
    context: Dict[str, Any] = None,
    user_id: str = None,
    correlation_id: str = None,
    logger: logging.Logger = None
) -> None:
    """
    Log errors with comprehensive context information
    
    Args:
        error: Exception that occurred
        context: Additional context information
        user_id: User identifier if available
        correlation_id: Request correlation ID
        logger: Logger instance
    """
    
    if logger is None:
        logger = get_logger(__name__)
    
    import traceback
    
    log_data = {
        'event_type': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc()
    }
    
    if context:
        log_data['context'] = context
    
    if user_id:
        log_data['user_id'] = user_id
    
    if correlation_id:
        log_data['correlation_id'] = correlation_id
    
    logger.error(f"Error occurred: {type(error).__name__}: {str(error)}", extra=log_data)


def create_structured_logger(
    name: str,
    additional_fields: Dict[str, Any] = None
) -> logging.Logger:
    """
    Create a structured logger with additional fields
    
    Args:
        name: Logger name
        additional_fields: Additional fields to include in all log messages
        
    Returns:
        Configured logger with structured logging
    """
    
    logger = get_logger(name)
    
    if additional_fields:
        # Create a custom filter to add fields
        class StructuredFilter(logging.Filter):
            def __init__(self, fields):
                super().__init__()
                self.fields = fields
            
            def filter(self, record):
                for key, value in self.fields.items():
                    setattr(record, key, value)
                return True
        
        logger.addFilter(StructuredFilter(additional_fields))
    
    return logger


class LoggingContext:
    """Context manager for request-scoped logging"""
    
    def __init__(self, **context):
        self.context = context
        self.original_context = {}
    
    def __enter__(self):
        # Save original context
        self.original_context = request_context.context.copy()
        
        # Set new context
        request_context.set_context(**self.context)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original context
        request_context.context.clear()
        request_context.context.update(self.original_context)


# Initialize logging on module import
setup_logging()
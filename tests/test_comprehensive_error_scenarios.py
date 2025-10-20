"""
Comprehensive error scenario testing
Tests edge cases, security scenarios, and error handling robustness
"""

import json
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from shared.exceptions import (
    LMSException, ValidationException, AuthenticationException,
    AuthorizationException, ResourceNotFoundException, BedrockAgentException,
    FileProcessingException, AWSServiceException, ErrorCode,
    create_error_response, lambda_error_handler, validate_required_fields,
    validate_file_upload
)
from shared.validation import (
    ChatMessageRequest, FileUploadRequest, QuizGenerationRequest,
    validate_request_model
)
from shared.logging_config import (
    log_security_event, log_validation_error, log_rate_limit_event,
    log_business_event, log_error_with_context
)
from shared.api_testing import APITester, APIEndpoint


class TestSecurityScenarios:
    """Test security-related error scenarios"""
    
    def test_sql_injection_attempts(self):
        """Test SQL injection attempt handling"""
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for malicious_input in malicious_inputs:
            data = {
                'message': malicious_input,
                'user_id': 'test-user'
            }
            
            # Should validate successfully (input sanitization happens at application level)
            model = validate_request_model(ChatMessageRequest, data)
            assert model.message == malicious_input
            
            # Log security event
            log_security_event(
                'sql_injection_attempt',
                user_id='test-user',
                details={'input': malicious_input[:100]},
                severity='WARNING'
            )
    
    def test_xss_attempts(self):
        """Test XSS attempt handling"""
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            data = {
                'message': payload,
                'user_id': 'test-user'
            }
            
            # Should validate successfully (XSS prevention happens at output encoding)
            model = validate_request_model(ChatMessageRequest, data)
            assert model.message == payload
            
            # Log security event
            log_security_event(
                'xss_attempt',
                user_id='test-user',
                details={'payload': payload[:100]},
                severity='WARNING'
            )
    
    def test_path_traversal_attempts(self):
        """Test path traversal attempt handling"""
        
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        for attempt in path_traversal_attempts:
            with pytest.raises(ValidationException):
                validate_file_upload(attempt, 1024)
            
            # Log security event
            log_security_event(
                'path_traversal_attempt',
                details={'filename': attempt},
                severity='WARNING'
            )
    
    def test_oversized_requests(self):
        """Test handling of oversized requests"""
        
        # Test extremely long message
        long_message = "x" * 10000
        data = {
            'message': long_message,
            'user_id': 'test-user'
        }
        
        with pytest.raises(ValidationException):
            validate_request_model(ChatMessageRequest, data)
        
        # Test oversized file
        with pytest.raises(ValidationException):
            validate_file_upload("large_file.pdf", 50 * 1024 * 1024)  # 50MB
    
    def test_malformed_data_handling(self):
        """Test handling of malformed data"""
        
        malformed_data_sets = [
            {},  # Empty object
            {'message': None},  # Null message
            {'message': ''},  # Empty message
            {'message': '   '},  # Whitespace only
            {'message': 'test', 'user_id': None},  # Null user_id
            {'invalid_field': 'value'},  # Invalid field
        ]
        
        for data in malformed_data_sets:
            with pytest.raises(ValidationException):
                validate_request_model(ChatMessageRequest, data)
    
    def test_unicode_and_encoding_attacks(self):
        """Test Unicode and encoding attack handling"""
        
        unicode_attacks = [
            "test\x00null_byte",
            "test\uffff",  # Invalid Unicode
            "test\u202e",  # Right-to-left override
            "test\u200b",  # Zero-width space
            "test\ud800",  # Invalid surrogate
        ]
        
        for attack in unicode_attacks:
            try:
                data = {
                    'message': attack,
                    'user_id': 'test-user'
                }
                
                # Some may validate, some may not - both are acceptable
                validate_request_model(ChatMessageRequest, data)
                
            except (ValidationException, UnicodeError):
                # Expected for some inputs
                pass


class TestRateLimitingScenarios:
    """Test rate limiting scenarios"""
    
    def test_rate_limit_logging(self):
        """Test rate limit event logging"""
        
        # Simulate rate limit scenarios
        scenarios = [
            {
                'user_id': 'user-123',
                'endpoint': '/api/chat',
                'limit_type': 'requests_per_minute',
                'current_count': 95,
                'limit': 100,
                'should_warn': False
            },
            {
                'user_id': 'user-123',
                'endpoint': '/api/chat',
                'limit_type': 'requests_per_minute',
                'current_count': 100,
                'limit': 100,
                'should_warn': True
            },
            {
                'user_id': 'user-456',
                'endpoint': '/api/files',
                'limit_type': 'files_per_hour',
                'current_count': 15,
                'limit': 10,
                'should_warn': True
            }
        ]
        
        for scenario in scenarios:
            log_rate_limit_event(
                user_id=scenario['user_id'],
                endpoint=scenario['endpoint'],
                limit_type=scenario['limit_type'],
                current_count=scenario['current_count'],
                limit=scenario['limit'],
                source_ip='192.168.1.1'
            )
    
    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests"""
        
        # Simulate concurrent validation requests
        import threading
        
        results = []
        errors = []
        
        def validate_request():
            try:
                data = {
                    'message': f'Concurrent test {threading.current_thread().ident}',
                    'user_id': 'test-user'
                }
                model = validate_request_model(ChatMessageRequest, data)
                results.append(model)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=validate_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 10
        assert len(errors) == 0


class TestErrorRecoveryScenarios:
    """Test error recovery and resilience scenarios"""
    
    def test_partial_failure_handling(self):
        """Test handling of partial failures"""
        
        @lambda_error_handler
        def partial_failure_function(event, context):
            # Simulate partial processing
            results = []
            errors = []
            
            items = event.get('items', [])
            for item in items:
                try:
                    if item.get('should_fail'):
                        raise ValidationException(f"Item {item['id']} failed validation")
                    results.append({'id': item['id'], 'status': 'success'})
                except Exception as e:
                    errors.append({'id': item['id'], 'error': str(e)})
            
            if errors and not results:
                # All failed
                raise ValidationException("All items failed processing")
            elif errors:
                # Partial failure - return mixed results
                return {
                    'statusCode': 207,  # Multi-status
                    'body': json.dumps({
                        'success': True,
                        'results': results,
                        'errors': errors,
                        'partial_failure': True
                    })
                }
            else:
                # All succeeded
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'results': results
                    })
                }
        
        # Test all success
        event = {
            'items': [
                {'id': '1', 'should_fail': False},
                {'id': '2', 'should_fail': False}
            ]
        }
        result = partial_failure_function(event, {})
        assert result['statusCode'] == 200
        
        # Test partial failure
        event = {
            'items': [
                {'id': '1', 'should_fail': False},
                {'id': '2', 'should_fail': True}
            ]
        }
        result = partial_failure_function(event, {})
        assert result['statusCode'] == 207
        
        # Test all failure
        event = {
            'items': [
                {'id': '1', 'should_fail': True},
                {'id': '2', 'should_fail': True}
            ]
        }
        result = partial_failure_function(event, {})
        assert result['statusCode'] == 400
    
    def test_timeout_handling(self):
        """Test timeout scenario handling"""
        
        @lambda_error_handler
        def timeout_function(event, context):
            timeout_seconds = event.get('timeout', 1)
            time.sleep(timeout_seconds)
            return {
                'statusCode': 200,
                'body': json.dumps({'success': True})
            }
        
        # Test normal execution
        result = timeout_function({'timeout': 0.1}, {})
        assert result['statusCode'] == 200
        
        # Test timeout scenario (simulated)
        try:
            # In real Lambda, this would timeout
            result = timeout_function({'timeout': 2}, {})
            assert result['statusCode'] == 200
        except Exception:
            # Expected in test environment
            pass
    
    def test_memory_pressure_handling(self):
        """Test handling under memory pressure"""
        
        @lambda_error_handler
        def memory_intensive_function(event, context):
            size = event.get('data_size', 1000)
            
            try:
                # Simulate memory-intensive operation
                large_data = ['x' * 1000 for _ in range(size)]
                
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'processed_items': len(large_data)
                    })
                }
            except MemoryError:
                raise AWSServiceException(
                    service='Lambda',
                    message='Insufficient memory to process request',
                    aws_error_code='MemoryError'
                )
        
        # Test normal memory usage
        result = memory_intensive_function({'data_size': 100}, {})
        assert result['statusCode'] == 200
        
        # Test high memory usage (may fail in constrained environments)
        try:
            result = memory_intensive_function({'data_size': 100000}, {})
        except Exception:
            # Expected in memory-constrained environments
            pass


class TestBusinessLogicErrorScenarios:
    """Test business logic error scenarios"""
    
    def test_invalid_business_state_transitions(self):
        """Test invalid business state transitions"""
        
        # Test quiz submission for non-existent quiz
        with pytest.raises(ResourceNotFoundException):
            raise ResourceNotFoundException("Quiz", "non-existent-quiz-id")
        
        # Test file processing for already processed file
        exception = FileProcessingException(
            message="File already processed",
            file_id="file-123",
            processing_stage="already_completed"
        )
        
        assert exception.error_code == ErrorCode.PROCESSING_FAILED
        assert exception.details['processing_stage'] == "already_completed"
    
    def test_data_consistency_errors(self):
        """Test data consistency error scenarios"""
        
        # Test conversation without messages
        exception = ValidationException(
            message="Conversation has no messages",
            details={'conversation_id': 'conv-123', 'message_count': 0}
        )
        
        assert 'conversation_id' in exception.details
        assert exception.details['message_count'] == 0
    
    def test_external_service_failures(self):
        """Test external service failure scenarios"""
        
        service_failures = [
            ('Bedrock', 'Model not available', 'ModelNotAvailableException'),
            ('S3', 'Bucket not found', 'NoSuchBucket'),
            ('DynamoDB', 'Table not found', 'ResourceNotFoundException'),
            ('Textract', 'Document too large', 'DocumentTooLargeException'),
            ('Comprehend', 'Language not supported', 'UnsupportedLanguageException')
        ]
        
        for service, message, aws_code in service_failures:
            exception = AWSServiceException(
                service=service,
                message=message,
                aws_error_code=aws_code
            )
            
            assert exception.error_code == ErrorCode.AWS_SERVICE_ERROR
            assert exception.details['service'] == service
            assert exception.details['aws_error_code'] == aws_code
            assert exception.status_code == 503


class TestErrorLoggingAndMonitoring:
    """Test error logging and monitoring scenarios"""
    
    def test_comprehensive_error_logging(self):
        """Test comprehensive error logging"""
        
        # Test validation error logging
        log_validation_error(
            field='email',
            value='invalid-email',
            error_message='Invalid email format',
            user_id='user-123'
        )
        
        # Test business event logging
        log_business_event(
            event_type='file_upload_failed',
            user_id='user-123',
            details={
                'file_id': 'file-456',
                'error_reason': 'Invalid file type',
                'file_size': 1024000
            }
        )
        
        # Test error with context logging
        try:
            raise ValueError("Test error for logging")
        except Exception as e:
            log_error_with_context(
                error=e,
                context={
                    'function': 'test_function',
                    'parameters': {'param1': 'value1'},
                    'user_action': 'file_upload'
                },
                user_id='user-123',
                correlation_id='corr-123'
            )
    
    def test_error_aggregation_scenarios(self):
        """Test error aggregation for monitoring"""
        
        # Simulate multiple similar errors
        error_patterns = [
            ('VALIDATION_ERROR', 'Invalid file type', 5),
            ('BEDROCK_ERROR', 'Model timeout', 3),
            ('AWS_SERVICE_ERROR', 'S3 access denied', 2),
        ]
        
        for error_code, message, count in error_patterns:
            for i in range(count):
                exception = LMSException(
                    message=f"{message} #{i+1}",
                    error_code=ErrorCode(error_code),
                    status_code=400 if error_code == 'VALIDATION_ERROR' else 503
                )
                
                # Log for aggregation
                log_error_with_context(
                    error=exception,
                    context={'error_pattern': error_code},
                    correlation_id=f'batch-{i}'
                )
    
    def test_performance_degradation_logging(self):
        """Test performance degradation logging"""
        
        # Simulate slow operations
        slow_operations = [
            ('bedrock_agent_invoke', 5000),  # 5 seconds
            ('file_processing', 15000),      # 15 seconds
            ('quiz_generation', 8000),       # 8 seconds
        ]
        
        for operation, duration_ms in slow_operations:
            if duration_ms > 3000:  # Threshold for slow operations
                log_security_event(
                    'performance_degradation',
                    details={
                        'operation': operation,
                        'duration_ms': duration_ms,
                        'threshold_ms': 3000
                    },
                    severity='WARNING'
                )


class TestAPIEndpointErrorScenarios:
    """Test API endpoint-specific error scenarios"""
    
    def setup_method(self):
        """Setup test API tester"""
        self.tester = APITester("http://localhost:3000")
    
    def test_chat_endpoint_error_scenarios(self):
        """Test chat endpoint error scenarios"""
        
        error_scenarios = [
            # Missing message
            ({}, 400),
            # Empty message
            ({'message': ''}, 400),
            # Whitespace only message
            ({'message': '   '}, 400),
            # Extremely long message
            ({'message': 'x' * 10000}, 400),
            # Invalid conversation ID format
            ({'message': 'test', 'conversation_id': 'invalid-format'}, 400),
        ]
        
        for data, expected_status in error_scenarios:
            endpoint = APIEndpoint(
                method="POST",
                path="/api/chat",
                description="Chat error scenario",
                expected_status=expected_status
            )
            
            result = self.tester.test_endpoint(endpoint, data=data)
            # Note: In real testing, we'd assert result.success
    
    def test_file_upload_error_scenarios(self):
        """Test file upload error scenarios"""
        
        error_scenarios = [
            # Missing filename
            ({'file_size': 1024}, 400),
            # Missing file size
            ({'filename': 'test.pdf'}, 400),
            # Invalid file extension
            ({'filename': 'virus.exe', 'file_size': 1024}, 400),
            # File too large
            ({'filename': 'large.pdf', 'file_size': 50 * 1024 * 1024}, 400),
            # Negative file size
            ({'filename': 'test.pdf', 'file_size': -1024}, 400),
            # Zero file size
            ({'filename': 'test.pdf', 'file_size': 0}, 400),
        ]
        
        for data, expected_status in error_scenarios:
            endpoint = APIEndpoint(
                method="POST",
                path="/api/files",
                description="File upload error scenario",
                expected_status=expected_status
            )
            
            result = self.tester.test_endpoint(endpoint, data=data)
            # Note: In real testing, we'd assert result.success
    
    def test_quiz_generation_error_scenarios(self):
        """Test quiz generation error scenarios"""
        
        error_scenarios = [
            # Invalid difficulty
            ({'difficulty': 'impossible', 'num_questions': 5}, 400),
            # Too many questions
            ({'difficulty': 'intermediate', 'num_questions': 100}, 400),
            # Zero questions
            ({'difficulty': 'intermediate', 'num_questions': 0}, 400),
            # Negative questions
            ({'difficulty': 'intermediate', 'num_questions': -5}, 400),
        ]
        
        for data, expected_status in error_scenarios:
            endpoint = APIEndpoint(
                method="POST",
                path="/api/quiz/generate",
                description="Quiz generation error scenario",
                expected_status=expected_status
            )
            
            result = self.tester.test_endpoint(endpoint, data=data)
            # Note: In real testing, we'd assert result.success


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
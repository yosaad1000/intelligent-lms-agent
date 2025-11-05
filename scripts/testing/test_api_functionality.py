#!/usr/bin/env python3
"""
Test API functionality without requiring a running server
Tests the validation, error handling, and documentation components
"""

import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shared.exceptions import (
    ValidationException, AuthenticationException, ResourceNotFoundException,
    ErrorCode, create_error_response, lambda_error_handler, validate_required_fields,
    validate_file_upload, create_lambda_response, handle_validation_error
)
from shared.validation import (
    ChatMessageRequest, FileUploadRequest, QuizGenerationRequest,
    validate_request_model, create_success_response
)
from shared.logging_config import setup_logging, get_logger
from shared.openapi_spec import generate_openapi_spec


def test_validation_functionality():
    """Test validation functionality"""
    
    print("🧪 Testing Validation Functionality...")
    
    # Test valid chat request
    try:
        valid_data = {
            'message': 'Hello, how are you?',
            'user_id': 'test-user',
            'conversation_id': 'conv-123'
        }
        
        model = validate_request_model(ChatMessageRequest, valid_data)
        print(f"✅ Valid chat request: {model.message[:30]}...")
        
    except Exception as e:
        print(f"❌ Valid chat request failed: {e}")
        return False
    
    # Test invalid chat request
    try:
        invalid_data = {
            'message': '   ',  # Empty message
            'user_id': 'test-user'
        }
        
        validate_request_model(ChatMessageRequest, invalid_data)
        print("❌ Invalid chat request should have failed")
        return False
        
    except ValidationException:
        print("✅ Invalid chat request properly rejected")
    except Exception as e:
        print("✅ Invalid chat request rejected (different exception type)")
    
    # Test file upload validation
    try:
        valid_file_data = {
            'filename': 'document.pdf',
            'file_size': 1024 * 1024,
            'user_id': 'test-user'
        }
        
        model = validate_request_model(FileUploadRequest, valid_file_data)
        print(f"✅ Valid file upload: {model.filename}")
        
    except Exception as e:
        print(f"❌ Valid file upload failed: {e}")
        return False
    
    # Test invalid file extension
    try:
        invalid_file_data = {
            'filename': 'virus.exe',
            'file_size': 1024,
            'user_id': 'test-user'
        }
        
        validate_request_model(FileUploadRequest, invalid_file_data)
        print("❌ Invalid file extension should have failed")
        return False
        
    except Exception:
        print("✅ Invalid file extension properly rejected")
    
    return True


def test_error_handling():
    """Test error handling functionality"""
    
    print("\n🧪 Testing Error Handling...")
    
    # Test ValidationException
    try:
        exc = ValidationException("Invalid email format", field="email")
        response = create_error_response(exc)
        
        assert response['success'] is False
        assert response['error']['code'] == ErrorCode.VALIDATION_ERROR.value
        assert 'email' in str(response['error']['details'])
        
        print("✅ ValidationException handling works")
        
    except Exception as e:
        print(f"❌ ValidationException handling failed: {e}")
        return False
    
    # Test AuthenticationException
    try:
        exc = AuthenticationException("Token expired")
        response = create_error_response(exc)
        
        assert response['success'] is False
        assert response['error']['code'] == ErrorCode.UNAUTHORIZED.value
        assert response['error']['message'] == "Please log in to access this resource"
        
        print("✅ AuthenticationException handling works")
        
    except Exception as e:
        print(f"❌ AuthenticationException handling failed: {e}")
        return False
    
    # Test ResourceNotFoundException
    try:
        exc = ResourceNotFoundException("File", "file-123")
        response = create_error_response(exc)
        
        assert response['success'] is False
        assert response['error']['code'] == ErrorCode.RESOURCE_NOT_FOUND.value
        assert 'file-123' in str(response['error']['details'])
        
        print("✅ ResourceNotFoundException handling works")
        
    except Exception as e:
        print(f"❌ ResourceNotFoundException handling failed: {e}")
        return False
    
    # Test Lambda response creation
    try:
        lambda_response = create_lambda_response(
            status_code=400,
            body={'success': False, 'error': 'Test error'}
        )
        
        assert lambda_response['statusCode'] == 400
        assert 'Content-Type' in lambda_response['headers']
        assert 'Access-Control-Allow-Origin' in lambda_response['headers']
        
        body = json.loads(lambda_response['body'])
        assert body['success'] is False
        
        print("✅ Lambda response creation works")
        
    except Exception as e:
        print(f"❌ Lambda response creation failed: {e}")
        return False
    
    return True


def test_lambda_error_decorator():
    """Test Lambda error handler decorator"""
    
    print("\n🧪 Testing Lambda Error Decorator...")
    
    # Test successful function
    @lambda_error_handler
    def successful_lambda(event, context):
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True, 'message': 'Hello World'})
        }
    
    try:
        result = successful_lambda({}, {})
        assert result['statusCode'] == 200
        
        body = json.loads(result['body'])
        assert body['success'] is True
        
        print("✅ Successful Lambda function works")
        
    except Exception as e:
        print(f"❌ Successful Lambda function failed: {e}")
        return False
    
    # Test function that raises ValidationException
    @lambda_error_handler
    def validation_error_lambda(event, context):
        raise ValidationException("Invalid input data")
    
    try:
        result = validation_error_lambda({}, {})
        assert result['statusCode'] == 400
        
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error']['code'] == ErrorCode.VALIDATION_ERROR.value
        
        print("✅ ValidationException Lambda handling works")
        
    except Exception as e:
        print(f"❌ ValidationException Lambda handling failed: {e}")
        return False
    
    # Test function that raises generic exception
    @lambda_error_handler
    def generic_error_lambda(event, context):
        raise ValueError("Something went wrong")
    
    try:
        result = generic_error_lambda({}, {})
        assert result['statusCode'] == 500
        
        body = json.loads(result['body'])
        assert body['success'] is False
        assert body['error']['code'] == ErrorCode.INTERNAL_ERROR.value
        
        print("✅ Generic exception Lambda handling works")
        
    except Exception as e:
        print(f"❌ Generic exception Lambda handling failed: {e}")
        return False
    
    return True


def test_utility_functions():
    """Test utility functions"""
    
    print("\n🧪 Testing Utility Functions...")
    
    # Test required fields validation
    try:
        data = {'name': 'John', 'email': 'john@example.com'}
        validate_required_fields(data, ['name', 'email'])
        print("✅ Required fields validation (valid) works")
        
    except Exception as e:
        print(f"❌ Required fields validation (valid) failed: {e}")
        return False
    
    try:
        data = {'name': 'John'}
        validate_required_fields(data, ['name', 'email', 'phone'])
        print("❌ Required fields validation should have failed")
        return False
        
    except ValidationException as e:
        assert 'email' in e.message
        assert 'phone' in e.message
        print("✅ Required fields validation (missing) works")
        
    except Exception as e:
        print(f"❌ Required fields validation (missing) failed: {e}")
        return False
    
    # Test file upload validation
    try:
        validate_file_upload("document.pdf", 1024 * 1024)
        print("✅ File upload validation (valid) works")
        
    except Exception as e:
        print(f"❌ File upload validation (valid) failed: {e}")
        return False
    
    try:
        validate_file_upload("virus.exe", 1024)
        print("❌ File upload validation should have failed")
        return False
        
    except ValidationException:
        print("✅ File upload validation (invalid) works")
        
    except Exception as e:
        print(f"❌ File upload validation (invalid) failed: {e}")
        return False
    
    return True


def test_openapi_generation():
    """Test OpenAPI specification generation"""
    
    print("\n🧪 Testing OpenAPI Generation...")
    
    try:
        spec = generate_openapi_spec()
        
        # Check basic structure
        assert 'openapi' in spec
        assert 'info' in spec
        assert 'paths' in spec
        assert 'components' in spec
        
        # Check info section
        assert spec['info']['title'] == 'LMS AI Backend API'
        assert 'version' in spec['info']
        
        # Check paths
        assert '/health' in spec['paths']
        assert '/api/chat' in spec['paths']
        assert '/api/files' in spec['paths']
        
        # Check components
        assert 'schemas' in spec['components']
        assert 'responses' in spec['components']
        assert 'securitySchemes' in spec['components']
        
        print("✅ OpenAPI specification generation works")
        
    except Exception as e:
        print(f"❌ OpenAPI specification generation failed: {e}")
        return False
    
    return True


def test_logging_setup():
    """Test logging configuration"""
    
    print("\n🧪 Testing Logging Setup...")
    
    try:
        # Setup logging
        logger = setup_logging(level="INFO", format_type="json")
        
        # Get a logger
        test_logger = get_logger(__name__)
        
        # Test logging (won't show output but shouldn't crash)
        test_logger.info("Test log message")
        test_logger.warning("Test warning message")
        test_logger.error("Test error message")
        
        print("✅ Logging setup works")
        
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
        return False
    
    return True


def main():
    """Run all functionality tests"""
    
    print("LMS API Functionality Test Suite")
    print("=" * 50)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    tests = [
        ("Validation Functionality", test_validation_functionality),
        ("Error Handling", test_error_handling),
        ("Lambda Error Decorator", test_lambda_error_decorator),
        ("Utility Functions", test_utility_functions),
        ("OpenAPI Generation", test_openapi_generation),
        ("Logging Setup", test_logging_setup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_function in tests:
        try:
            if test_function():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! API functionality is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
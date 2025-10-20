"""
Comprehensive API testing utilities
Provides tools for testing API endpoints, validation, and error scenarios
"""

import json
import time
import uuid
import asyncio
import requests
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    method: str
    path: str
    description: str
    required_fields: List[str] = None
    optional_fields: List[str] = None
    expected_status: int = 200
    auth_required: bool = True


class APITester:
    """Comprehensive API testing utility"""
    
    def __init__(self, base_url: str, auth_token: str = None):
        """
        Initialize API tester
        
        Args:
            base_url: Base URL for the API
            auth_token: Authentication token (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = requests.Session()
        self.test_results: List[TestResult] = []
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'LMS-API-Tester/1.0'
        })
        
        if auth_token:
            self.session.headers.update({
                'Authorization': f'Bearer {auth_token}'
            })
    
    def test_endpoint(
        self,
        endpoint: APIEndpoint,
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        timeout: int = 30
    ) -> TestResult:
        """
        Test a single API endpoint
        
        Args:
            endpoint: Endpoint configuration
            data: Request body data
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            Test result
        """
        
        start_time = time.time()
        
        try:
            # Prepare request
            url = f"{self.base_url}{endpoint.path}"
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            # Make request
            if endpoint.method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=request_headers, timeout=timeout)
            elif endpoint.method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params, headers=request_headers, timeout=timeout)
            elif endpoint.method.upper() == 'PUT':
                response = self.session.put(url, json=data, params=params, headers=request_headers, timeout=timeout)
            elif endpoint.method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, headers=request_headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {endpoint.method}")
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            # Check if test passed
            success = response.status_code == endpoint.expected_status
            
            result = TestResult(
                test_name=f"{endpoint.method.upper()} {endpoint.path}",
                success=success,
                status_code=response.status_code,
                response_data=response_data,
                duration_ms=duration_ms,
                error_message=None if success else f"Expected {endpoint.expected_status}, got {response.status_code}"
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            result = TestResult(
                test_name=f"{endpoint.method.upper()} {endpoint.path}",
                success=False,
                error_message=str(e),
                duration_ms=duration_ms
            )
        
        self.test_results.append(result)
        return result
    
    def test_health_endpoint(self) -> TestResult:
        """Test health check endpoint"""
        
        endpoint = APIEndpoint(
            method="GET",
            path="/health",
            description="Health check",
            auth_required=False,
            expected_status=200
        )
        
        return self.test_endpoint(endpoint)
    
    def test_chat_endpoint(self, message: str = "Hello, how are you?", user_id: str = "test-user") -> TestResult:
        """Test chat endpoint"""
        
        endpoint = APIEndpoint(
            method="POST",
            path="/api/chat",
            description="Send chat message",
            required_fields=["message"],
            optional_fields=["conversation_id", "subject_id", "user_id"]
        )
        
        data = {
            "message": message,
            "user_id": user_id
        }
        
        return self.test_endpoint(endpoint, data=data)
    
    def test_file_upload_endpoint(self, filename: str = "test.pdf", file_size: int = 1024) -> TestResult:
        """Test file upload endpoint"""
        
        endpoint = APIEndpoint(
            method="POST",
            path="/api/files",
            description="Upload file",
            required_fields=["filename", "file_size"],
            optional_fields=["subject_id", "user_id"]
        )
        
        data = {
            "filename": filename,
            "file_size": file_size,
            "user_id": "test-user"
        }
        
        return self.test_endpoint(endpoint, data=data)
    
    def test_get_files_endpoint(self, user_id: str = "test-user") -> TestResult:
        """Test get files endpoint"""
        
        endpoint = APIEndpoint(
            method="GET",
            path="/api/files",
            description="Get user files",
            auth_required=True
        )
        
        params = {"user_id": user_id}
        
        return self.test_endpoint(endpoint, params=params)
    
    def test_validation_errors(self) -> List[TestResult]:
        """Test various validation error scenarios"""
        
        validation_tests = []
        
        # Test missing required fields
        endpoint = APIEndpoint(
            method="POST",
            path="/api/chat",
            description="Chat with missing message",
            expected_status=400
        )
        
        result = self.test_endpoint(endpoint, data={"user_id": "test-user"})
        result.test_name = "Chat - Missing message field"
        validation_tests.append(result)
        
        # Test invalid file type
        endpoint = APIEndpoint(
            method="POST",
            path="/api/files",
            description="Upload invalid file type",
            expected_status=400
        )
        
        result = self.test_endpoint(endpoint, data={
            "filename": "test.exe",
            "file_size": 1024,
            "user_id": "test-user"
        })
        result.test_name = "File Upload - Invalid file type"
        validation_tests.append(result)
        
        # Test file too large
        endpoint = APIEndpoint(
            method="POST",
            path="/api/files",
            description="Upload file too large",
            expected_status=400
        )
        
        result = self.test_endpoint(endpoint, data={
            "filename": "large_file.pdf",
            "file_size": 20 * 1024 * 1024,  # 20MB
            "user_id": "test-user"
        })
        result.test_name = "File Upload - File too large"
        validation_tests.append(result)
        
        # Test empty message
        endpoint = APIEndpoint(
            method="POST",
            path="/api/chat",
            description="Chat with empty message",
            expected_status=400
        )
        
        result = self.test_endpoint(endpoint, data={
            "message": "",
            "user_id": "test-user"
        })
        result.test_name = "Chat - Empty message"
        validation_tests.append(result)
        
        self.test_results.extend(validation_tests)
        return validation_tests
    
    def test_authentication_errors(self) -> List[TestResult]:
        """Test authentication error scenarios"""
        
        auth_tests = []
        
        # Test without auth token
        original_auth = self.session.headers.get('Authorization')
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        endpoint = APIEndpoint(
            method="POST",
            path="/api/chat",
            description="Chat without authentication",
            expected_status=401
        )
        
        result = self.test_endpoint(endpoint, data={
            "message": "Hello",
            "user_id": "test-user"
        })
        result.test_name = "Chat - No authentication"
        auth_tests.append(result)
        
        # Test with invalid token
        self.session.headers['Authorization'] = 'Bearer invalid-token'
        
        result = self.test_endpoint(endpoint, data={
            "message": "Hello",
            "user_id": "test-user"
        })
        result.test_name = "Chat - Invalid token"
        auth_tests.append(result)
        
        # Restore original auth
        if original_auth:
            self.session.headers['Authorization'] = original_auth
        elif 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        self.test_results.extend(auth_tests)
        return auth_tests
    
    def test_error_scenarios(self) -> List[TestResult]:
        """Test various error scenarios"""
        
        error_tests = []
        
        # Test non-existent conversation
        endpoint = APIEndpoint(
            method="GET",
            path="/api/chat/history",
            description="Get non-existent conversation",
            expected_status=404
        )
        
        result = self.test_endpoint(endpoint, params={
            "conversation_id": "non-existent-conv-id",
            "user_id": "test-user"
        })
        result.test_name = "Chat History - Non-existent conversation"
        error_tests.append(result)
        
        # Test processing non-existent file
        endpoint = APIEndpoint(
            method="POST",
            path="/api/files/process",
            description="Process non-existent file",
            expected_status=404
        )
        
        result = self.test_endpoint(endpoint, data={
            "file_id": "non-existent-file-id",
            "user_id": "test-user"
        })
        result.test_name = "File Processing - Non-existent file"
        error_tests.append(result)
        
        self.test_results.extend(error_tests)
        return error_tests
    
    def test_performance(self, endpoint: APIEndpoint, data: Dict[str, Any] = None, iterations: int = 10) -> Dict[str, Any]:
        """
        Test endpoint performance
        
        Args:
            endpoint: Endpoint to test
            data: Request data
            iterations: Number of test iterations
            
        Returns:
            Performance metrics
        """
        
        durations = []
        success_count = 0
        
        for i in range(iterations):
            result = self.test_endpoint(endpoint, data=data)
            if result.duration_ms:
                durations.append(result.duration_ms)
            if result.success:
                success_count += 1
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = min_duration = max_duration = 0
        
        return {
            "endpoint": f"{endpoint.method.upper()} {endpoint.path}",
            "iterations": iterations,
            "success_rate": success_count / iterations * 100,
            "avg_duration_ms": avg_duration,
            "min_duration_ms": min_duration,
            "max_duration_ms": max_duration,
            "total_duration_ms": sum(durations)
        }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive test suite
        
        Returns:
            Test summary
        """
        
        print("Starting comprehensive API tests...")
        
        # Basic functionality tests
        print("Testing basic functionality...")
        self.test_health_endpoint()
        self.test_chat_endpoint()
        self.test_file_upload_endpoint()
        self.test_get_files_endpoint()
        
        # Validation tests
        print("Testing validation errors...")
        self.test_validation_errors()
        
        # Authentication tests
        print("Testing authentication...")
        self.test_authentication_errors()
        
        # Error scenario tests
        print("Testing error scenarios...")
        self.test_error_scenarios()
        
        # Performance tests
        print("Testing performance...")
        chat_endpoint = APIEndpoint("POST", "/api/chat", "Chat performance test")
        perf_results = self.test_performance(
            chat_endpoint,
            data={"message": "Performance test", "user_id": "test-user"},
            iterations=5
        )
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0,
            "performance_metrics": perf_results,
            "test_results": [
                {
                    "test_name": result.test_name,
                    "success": result.success,
                    "status_code": result.status_code,
                    "duration_ms": result.duration_ms,
                    "error_message": result.error_message
                }
                for result in self.test_results
            ]
        }
        
        return summary
    
    def generate_test_report(self, output_file: str = "test_report.json") -> None:
        """
        Generate detailed test report
        
        Args:
            output_file: Output file path
        """
        
        summary = self.run_comprehensive_tests()
        
        report = {
            "test_run_info": {
                "timestamp": datetime.utcnow().isoformat(),
                "base_url": self.base_url,
                "total_duration_ms": sum(
                    result.duration_ms for result in self.test_results 
                    if result.duration_ms
                )
            },
            "summary": summary,
            "detailed_results": [
                {
                    "test_name": result.test_name,
                    "success": result.success,
                    "status_code": result.status_code,
                    "response_data": result.response_data,
                    "error_message": result.error_message,
                    "duration_ms": result.duration_ms,
                    "timestamp": result.timestamp
                }
                for result in self.test_results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Test report saved to {output_file}")
        print(f"Tests: {summary['total_tests']}, Passed: {summary['passed_tests']}, Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")


class MockAPIServer:
    """Mock API server for testing"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.responses = {}
    
    def add_response(self, method: str, path: str, response_data: Dict[str, Any], status_code: int = 200):
        """Add mock response for endpoint"""
        key = f"{method.upper()}:{path}"
        self.responses[key] = {
            "data": response_data,
            "status_code": status_code
        }
    
    def setup_default_responses(self):
        """Setup default mock responses"""
        
        # Health endpoint
        self.add_response("GET", "/health", {
            "success": True,
            "status": "healthy",
            "services": {
                "dynamodb": "healthy",
                "s3": "healthy",
                "bedrock": "healthy"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Chat endpoint
        self.add_response("POST", "/api/chat", {
            "success": True,
            "response": "This is a mock AI response for testing purposes.",
            "conversation_id": str(uuid.uuid4()),
            "citations": [],
            "rag_documents_used": 0,
            "rag_enhanced": False,
            "bedrock_agent_used": True,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # File upload endpoint
        self.add_response("POST", "/api/files", {
            "success": True,
            "file_id": str(uuid.uuid4()),
            "upload_url": "https://mock-s3-url.com/upload",
            "status": "ready_for_upload",
            "process_url": "/api/files/process",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Get files endpoint
        self.add_response("GET", "/api/files", {
            "success": True,
            "files": [],
            "total": 0,
            "timestamp": datetime.utcnow().isoformat()
        })


def create_test_data_generator():
    """Create test data generator for various scenarios"""
    
    def generate_chat_messages():
        """Generate test chat messages"""
        return [
            "Hello, how are you?",
            "What is machine learning?",
            "Explain quantum physics",
            "Summarize my uploaded document",
            "Create a quiz about biology",
            "What are the key concepts in this chapter?",
            "Help me understand this topic better",
            "Can you provide examples?",
            "What should I study next?",
            "How can I improve my understanding?"
        ]
    
    def generate_file_data():
        """Generate test file data"""
        return [
            {"filename": "lecture_notes.pdf", "file_size": 1024 * 1024},
            {"filename": "textbook_chapter.docx", "file_size": 512 * 1024},
            {"filename": "research_paper.pdf", "file_size": 2 * 1024 * 1024},
            {"filename": "study_guide.txt", "file_size": 64 * 1024},
            {"filename": "assignment.pdf", "file_size": 256 * 1024}
        ]
    
    def generate_invalid_data():
        """Generate invalid test data"""
        return {
            "invalid_file_types": [
                {"filename": "virus.exe", "file_size": 1024},
                {"filename": "image.jpg", "file_size": 1024},
                {"filename": "video.mp4", "file_size": 1024}
            ],
            "oversized_files": [
                {"filename": "huge_file.pdf", "file_size": 50 * 1024 * 1024}
            ],
            "empty_messages": ["", "   ", "\n\t"],
            "oversized_messages": ["x" * 10000]
        }
    
    return {
        "chat_messages": generate_chat_messages(),
        "file_data": generate_file_data(),
        "invalid_data": generate_invalid_data()
    }


if __name__ == "__main__":
    # Example usage
    tester = APITester("http://localhost:3000")
    
    # Run comprehensive tests
    summary = tester.run_comprehensive_tests()
    
    # Generate report
    tester.generate_test_report("api_test_report.json")
    
    print("API testing completed!")
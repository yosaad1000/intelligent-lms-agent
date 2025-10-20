#!/usr/bin/env python3
"""
Comprehensive API Test Runner
Orchestrates all API testing including validation, error handling, and performance tests
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from api_testing import APITester, APIEndpoint, create_test_data_generator
from exceptions import (
    LMSException, ValidationException, AuthenticationException,
    ErrorCode, create_error_response
)
from validation import validate_request_model, ChatMessageRequest, FileUploadRequest
from logging_config import setup_logging, get_logger


class APITestRunner:
    """Comprehensive API test runner with detailed reporting"""
    
    def __init__(self, base_url: str, auth_token: str = None, output_dir: str = "test_results"):
        """
        Initialize test runner
        
        Args:
            base_url: Base URL for API testing
            auth_token: Authentication token
            output_dir: Directory for test results
        """
        self.base_url = base_url
        self.auth_token = auth_token
        self.output_dir = output_dir
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.tester = APITester(base_url, auth_token)
        self.test_data = create_test_data_generator()
        
        # Test results
        self.test_results = []
        self.performance_metrics = {}
        self.error_scenarios = []
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run all comprehensive API tests
        
        Returns:
            Complete test results
        """
        
        self.logger.info(f"Starting comprehensive API tests for {self.base_url}")
        
        start_time = time.time()
        
        # Test categories
        test_categories = [
            ("Health Check", self._test_health_endpoints),
            ("Basic Functionality", self._test_basic_functionality),
            ("Request Validation", self._test_request_validation),
            ("Response Validation", self._test_response_validation),
            ("Authentication & Authorization", self._test_authentication),
            ("Error Handling", self._test_error_handling),
            ("Security Scenarios", self._test_security_scenarios),
            ("Performance & Load", self._test_performance),
            ("Edge Cases", self._test_edge_cases),
            ("Integration Scenarios", self._test_integration_scenarios)
        ]
        
        results = {
            "test_run_info": {
                "start_time": datetime.utcnow().isoformat(),
                "base_url": self.base_url,
                "auth_provided": bool(self.auth_token),
                "test_categories": len(test_categories)
            },
            "categories": {},
            "summary": {}
        }
        
        # Run each test category
        for category_name, test_function in test_categories:
            self.logger.info(f"Running {category_name} tests...")
            
            try:
                category_start = time.time()
                category_results = test_function()
                category_duration = time.time() - category_start
                
                category_results["duration_seconds"] = category_duration
                results["categories"][category_name.lower().replace(" ", "_")] = category_results
                
                # Log category results
                passed = category_results.get("passed", 0)
                total = category_results.get("total", 0)
                self.logger.info(f"{category_name}: {passed}/{total} tests passed")
                
            except Exception as e:
                self.logger.error(f"Error in {category_name}: {str(e)}")
                results["categories"][category_name.lower().replace(" ", "_")] = {
                    "error": str(e),
                    "passed": 0,
                    "total": 0,
                    "tests": []
                }
        
        # Calculate summary
        total_duration = time.time() - start_time
        results["summary"] = self._calculate_summary(results["categories"])
        results["test_run_info"]["end_time"] = datetime.utcnow().isoformat()
        results["test_run_info"]["total_duration_seconds"] = total_duration
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _test_health_endpoints(self) -> Dict[str, Any]:
        """Test health and status endpoints"""
        
        tests = []
        
        # Basic health check
        result = self.tester.test_health_endpoint()
        tests.append({
            "name": "Health Check - Basic",
            "success": result.success,
            "status_code": result.status_code,
            "duration_ms": result.duration_ms,
            "error": result.error_message,
            "response_data": result.response_data
        })
        
        # Health check performance
        health_endpoint = APIEndpoint("GET", "/health", "Health Performance", auth_required=False)
        perf_results = self.tester.test_performance(health_endpoint, iterations=5)
        
        tests.append({
            "name": "Health Check - Performance",
            "success": perf_results["avg_duration_ms"] < 1000,  # Under 1 second
            "avg_duration_ms": perf_results["avg_duration_ms"],
            "success_rate": perf_results["success_rate"],
            "iterations": perf_results["iterations"]
        })
        
        return {
            "category": "Health Check",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_basic_functionality(self) -> Dict[str, Any]:
        """Test basic API functionality"""
        
        tests = []
        
        # Chat functionality
        for i, message in enumerate(self.test_data["chat_messages"][:3]):
            result = self.tester.test_chat_endpoint(message)
            tests.append({
                "name": f"Chat Message {i+1}",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message,
                "message": message[:50] + "..." if len(message) > 50 else message
            })
        
        # File upload functionality
        for i, file_data in enumerate(self.test_data["file_data"][:2]):
            result = self.tester.test_file_upload_endpoint(
                file_data["filename"],
                file_data["file_size"]
            )
            tests.append({
                "name": f"File Upload {i+1}",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message,
                "filename": file_data["filename"]
            })
        
        # Get files
        result = self.tester.test_get_files_endpoint()
        tests.append({
            "name": "Get User Files",
            "success": result.success,
            "status_code": result.status_code,
            "duration_ms": result.duration_ms,
            "error": result.error_message
        })
        
        return {
            "category": "Basic Functionality",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_request_validation(self) -> Dict[str, Any]:
        """Test request validation using Pydantic models"""
        
        tests = []
        
        # Valid request validation
        valid_chat_data = {
            "message": "Hello, this is a test message",
            "user_id": "test-user"
        }
        
        try:
            model = validate_request_model(ChatMessageRequest, valid_chat_data)
            tests.append({
                "name": "Valid Chat Request",
                "success": True,
                "validated_data": {
                    "message": model.message,
                    "user_id": model.user_id
                }
            })
        except Exception as e:
            tests.append({
                "name": "Valid Chat Request",
                "success": False,
                "error": str(e)
            })
        
        # Invalid request validation scenarios
        invalid_scenarios = [
            ({}, "Empty request"),
            ({"user_id": "test"}, "Missing message"),
            ({"message": ""}, "Empty message"),
            ({"message": "   "}, "Whitespace only message"),
            ({"message": "x" * 6000}, "Message too long"),
            ({"message": "test", "invalid_field": "value"}, "Extra fields")
        ]
        
        for invalid_data, scenario_name in invalid_scenarios:
            try:
                validate_request_model(ChatMessageRequest, invalid_data)
                tests.append({
                    "name": f"Invalid Request - {scenario_name}",
                    "success": False,
                    "error": "Validation should have failed but didn't"
                })
            except ValidationException:
                tests.append({
                    "name": f"Invalid Request - {scenario_name}",
                    "success": True,
                    "expected_failure": True
                })
            except Exception as e:
                tests.append({
                    "name": f"Invalid Request - {scenario_name}",
                    "success": True,
                    "expected_failure": True,
                    "error_type": type(e).__name__
                })
        
        # File upload validation
        valid_file_data = {
            "filename": "test_document.pdf",
            "file_size": 1024 * 1024,
            "user_id": "test-user"
        }
        
        try:
            model = validate_request_model(FileUploadRequest, valid_file_data)
            tests.append({
                "name": "Valid File Upload Request",
                "success": True,
                "validated_data": {
                    "filename": model.filename,
                    "file_size": model.file_size
                }
            })
        except Exception as e:
            tests.append({
                "name": "Valid File Upload Request",
                "success": False,
                "error": str(e)
            })
        
        return {
            "category": "Request Validation",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_response_validation(self) -> Dict[str, Any]:
        """Test response validation and format consistency"""
        
        tests = []
        
        # Test response format consistency
        endpoints_to_test = [
            ("GET", "/health", {}, "Health endpoint response format"),
            ("POST", "/api/chat", {"message": "test", "user_id": "test-user"}, "Chat response format"),
            ("GET", "/api/files", {"user_id": "test-user"}, "Files list response format")
        ]
        
        for method, path, data, test_name in endpoints_to_test:
            endpoint = APIEndpoint(method, path, test_name)
            
            if method == "GET":
                result = self.tester.test_endpoint(endpoint, params=data)
            else:
                result = self.tester.test_endpoint(endpoint, data=data)
            
            # Validate response structure
            response_valid = False
            error_details = None
            
            if result.response_data:
                try:
                    # Check for required fields
                    if isinstance(result.response_data, dict):
                        has_success = 'success' in result.response_data
                        has_timestamp = 'timestamp' in result.response_data
                        
                        if result.status_code >= 400:
                            # Error response should have error field
                            has_error = 'error' in result.response_data
                            response_valid = has_success and has_error
                        else:
                            # Success response should have success=True
                            response_valid = has_success and result.response_data.get('success') is True
                        
                        if not response_valid:
                            error_details = f"Missing required fields. Has success: {has_success}, Has timestamp: {has_timestamp}"
                    else:
                        error_details = "Response is not a JSON object"
                        
                except Exception as e:
                    error_details = f"Response validation error: {str(e)}"
            else:
                error_details = "No response data received"
            
            tests.append({
                "name": test_name,
                "success": response_valid,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": error_details,
                "response_structure_valid": response_valid
            })
        
        return {
            "category": "Response Validation",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_authentication(self) -> Dict[str, Any]:
        """Test authentication and authorization"""
        
        tests = []
        
        # Run authentication tests from APITester
        auth_results = self.tester.test_authentication_errors()
        
        for result in auth_results:
            tests.append({
                "name": result.test_name,
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        return {
            "category": "Authentication & Authorization",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """Test comprehensive error handling"""
        
        tests = []
        
        # Run error scenario tests from APITester
        error_results = self.tester.test_error_scenarios()
        
        for result in error_results:
            tests.append({
                "name": result.test_name,
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        # Test custom error scenarios
        custom_error_tests = [
            # Test malformed JSON
            {
                "name": "Malformed JSON Handling",
                "method": "POST",
                "path": "/api/chat",
                "data": "invalid json{",
                "expected_status": 400,
                "content_type": "text/plain"
            },
            # Test unsupported content type
            {
                "name": "Unsupported Content Type",
                "method": "POST", 
                "path": "/api/chat",
                "data": {"message": "test"},
                "expected_status": 400,
                "content_type": "application/xml"
            }
        ]
        
        for test_config in custom_error_tests:
            try:
                import requests
                
                url = f"{self.base_url}{test_config['path']}"
                headers = {
                    'Content-Type': test_config.get('content_type', 'application/json')
                }
                
                if self.auth_token:
                    headers['Authorization'] = f'Bearer {self.auth_token}'
                
                if test_config['content_type'] == 'application/json':
                    response = requests.post(url, json=test_config['data'], headers=headers, timeout=30)
                else:
                    response = requests.post(url, data=test_config['data'], headers=headers, timeout=30)
                
                success = response.status_code == test_config['expected_status']
                
                tests.append({
                    "name": test_config['name'],
                    "success": success,
                    "status_code": response.status_code,
                    "expected_status": test_config['expected_status'],
                    "error": None if success else f"Expected {test_config['expected_status']}, got {response.status_code}"
                })
                
            except Exception as e:
                tests.append({
                    "name": test_config['name'],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "category": "Error Handling",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_security_scenarios(self) -> Dict[str, Any]:
        """Test security scenarios"""
        
        tests = []
        
        # SQL Injection tests
        sql_injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for injection in sql_injections:
            endpoint = APIEndpoint("POST", "/api/chat", "SQL Injection Test", expected_status=200)
            result = self.tester.test_endpoint(endpoint, data={
                "message": injection,
                "user_id": "test-user"
            })
            
            # Should handle gracefully (not crash)
            tests.append({
                "name": f"SQL Injection: {injection[:30]}...",
                "success": result.status_code in [200, 400],  # Either works or validates
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "handled_gracefully": result.status_code != 500
            })
        
        # XSS tests
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        for payload in xss_payloads:
            endpoint = APIEndpoint("POST", "/api/chat", "XSS Test", expected_status=200)
            result = self.tester.test_endpoint(endpoint, data={
                "message": payload,
                "user_id": "test-user"
            })
            
            tests.append({
                "name": f"XSS: {payload[:30]}...",
                "success": result.status_code in [200, 400],
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "handled_gracefully": result.status_code != 500
            })
        
        return {
            "category": "Security Scenarios",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_performance(self) -> Dict[str, Any]:
        """Test performance and load scenarios"""
        
        tests = []
        
        # Chat endpoint performance
        chat_endpoint = APIEndpoint("POST", "/api/chat", "Chat Performance")
        chat_perf = self.tester.test_performance(
            chat_endpoint,
            data={"message": "Performance test message", "user_id": "test-user"},
            iterations=5
        )
        
        tests.append({
            "name": "Chat Endpoint Performance",
            "success": chat_perf["avg_duration_ms"] < 5000,  # Under 5 seconds
            "avg_duration_ms": chat_perf["avg_duration_ms"],
            "success_rate": chat_perf["success_rate"],
            "iterations": chat_perf["iterations"]
        })
        
        # File upload performance
        file_endpoint = APIEndpoint("POST", "/api/files", "File Upload Performance")
        file_perf = self.tester.test_performance(
            file_endpoint,
            data={"filename": "perf_test.pdf", "file_size": 1024*1024, "user_id": "test-user"},
            iterations=3
        )
        
        tests.append({
            "name": "File Upload Performance",
            "success": file_perf["avg_duration_ms"] < 3000,  # Under 3 seconds
            "avg_duration_ms": file_perf["avg_duration_ms"],
            "success_rate": file_perf["success_rate"],
            "iterations": file_perf["iterations"]
        })
        
        return {
            "category": "Performance & Load",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and boundary conditions"""
        
        tests = []
        
        # Unicode and special characters
        unicode_messages = [
            "Hello 世界",  # Chinese
            "Здравствуй мир",  # Russian
            "مرحبا بالعالم",  # Arabic
            "🚀 Rocket emoji test",  # Emoji
            "Special chars: !@#$%^&*()",  # Special characters
        ]
        
        for message in unicode_messages:
            result = self.tester.test_chat_endpoint(message)
            tests.append({
                "name": f"Unicode Test: {message[:20]}...",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        # Boundary value tests
        boundary_tests = [
            # Minimum message length
            {"message": "a", "user_id": "test-user", "test_name": "Minimum Message Length"},
            # Maximum allowed message length
            {"message": "x" * 4999, "user_id": "test-user", "test_name": "Maximum Message Length"},
            # Minimum file size
            {"filename": "tiny.txt", "file_size": 1, "user_id": "test-user", "test_name": "Minimum File Size"},
            # Maximum file size (just under limit)
            {"filename": "large.pdf", "file_size": 10*1024*1024-1, "user_id": "test-user", "test_name": "Maximum File Size"}
        ]
        
        for test_data in boundary_tests:
            test_name = test_data.pop("test_name")
            
            if "filename" in test_data:
                # File upload test
                result = self.tester.test_file_upload_endpoint(
                    test_data["filename"],
                    test_data["file_size"]
                )
            else:
                # Chat test
                result = self.tester.test_chat_endpoint(test_data["message"])
            
            tests.append({
                "name": test_name,
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        return {
            "category": "Edge Cases",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_integration_scenarios(self) -> Dict[str, Any]:
        """Test integration scenarios across multiple endpoints"""
        
        tests = []
        
        # End-to-end workflow test
        workflow_success = True
        workflow_errors = []
        
        try:
            # 1. Upload a file
            upload_result = self.tester.test_file_upload_endpoint("integration_test.pdf", 1024*1024)
            if not upload_result.success:
                workflow_success = False
                workflow_errors.append(f"File upload failed: {upload_result.error_message}")
            
            # 2. Get files list
            files_result = self.tester.test_get_files_endpoint()
            if not files_result.success:
                workflow_success = False
                workflow_errors.append(f"Get files failed: {files_result.error_message}")
            
            # 3. Send chat message
            chat_result = self.tester.test_chat_endpoint("Tell me about the uploaded document")
            if not chat_result.success:
                workflow_success = False
                workflow_errors.append(f"Chat failed: {chat_result.error_message}")
            
            tests.append({
                "name": "End-to-End Workflow",
                "success": workflow_success,
                "steps_completed": 3 - len(workflow_errors),
                "total_steps": 3,
                "errors": workflow_errors
            })
            
        except Exception as e:
            tests.append({
                "name": "End-to-End Workflow",
                "success": False,
                "error": str(e)
            })
        
        return {
            "category": "Integration Scenarios",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _calculate_summary(self, categories: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall test summary"""
        
        total_tests = 0
        total_passed = 0
        category_summaries = {}
        
        for category_name, category_data in categories.items():
            if "error" in category_data:
                category_summaries[category_name] = {
                    "status": "error",
                    "error": category_data["error"]
                }
                continue
            
            passed = category_data.get("passed", 0)
            total = category_data.get("total", 0)
            
            total_tests += total
            total_passed += passed
            
            category_summaries[category_name] = {
                "passed": passed,
                "total": total,
                "success_rate": (passed / total * 100) if total > 0 else 0,
                "duration_seconds": category_data.get("duration_seconds", 0)
            }
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "overall_success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "categories": category_summaries
        }
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save test results to files"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results as JSON
        detailed_path = os.path.join(self.output_dir, f"comprehensive_test_results_{timestamp}.json")
        with open(detailed_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save summary report
        summary_path = os.path.join(self.output_dir, f"test_summary_{timestamp}.md")
        self._generate_summary_report(results, summary_path)
        
        # Save CSV for analysis
        csv_path = os.path.join(self.output_dir, f"test_results_{timestamp}.csv")
        self._generate_csv_report(results, csv_path)
        
        self.logger.info(f"Test results saved:")
        self.logger.info(f"  Detailed: {detailed_path}")
        self.logger.info(f"  Summary: {summary_path}")
        self.logger.info(f"  CSV: {csv_path}")
    
    def _generate_summary_report(self, results: Dict[str, Any], output_path: str) -> None:
        """Generate markdown summary report"""
        
        content = []
        
        # Header
        content.append("# API Test Summary Report")
        content.append("")
        content.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        content.append(f"**Base URL:** {self.base_url}")
        content.append(f"**Authentication:** {'Provided' if self.auth_token else 'Not provided'}")
        content.append("")
        
        # Overall Results
        summary = results["summary"]
        content.append("## Overall Results")
        content.append("")
        content.append(f"- **Total Tests:** {summary['total_tests']}")
        content.append(f"- **Passed:** {summary['total_passed']}")
        content.append(f"- **Success Rate:** {summary['overall_success_rate']:.1f}%")
        content.append("")
        
        # Status indicator
        success_rate = summary['overall_success_rate']
        if success_rate >= 90:
            status = "🟢 EXCELLENT"
        elif success_rate >= 80:
            status = "🟡 GOOD"
        elif success_rate >= 70:
            status = "🟠 ACCEPTABLE"
        else:
            status = "🔴 NEEDS IMPROVEMENT"
        
        content.append(f"**Status:** {status}")
        content.append("")
        
        # Category Results
        content.append("## Category Results")
        content.append("")
        content.append("| Category | Passed | Total | Success Rate | Duration |")
        content.append("|----------|--------|-------|--------------|----------|")
        
        for category_name, category_data in summary["categories"].items():
            if "error" in category_data:
                content.append(f"| {category_name.replace('_', ' ').title()} | ERROR | - | - | - |")
            else:
                passed = category_data["passed"]
                total = category_data["total"]
                rate = category_data["success_rate"]
                duration = category_data.get("duration_seconds", 0)
                content.append(f"| {category_name.replace('_', ' ').title()} | {passed} | {total} | {rate:.1f}% | {duration:.1f}s |")
        
        content.append("")
        
        # Recommendations
        content.append("## Recommendations")
        content.append("")
        
        if success_rate >= 90:
            content.append("✅ Excellent API health! Continue monitoring and maintain current quality standards.")
        elif success_rate >= 80:
            content.append("⚠️ Good API health with minor issues. Review failed tests and address any patterns.")
        elif success_rate >= 70:
            content.append("🔧 Acceptable but needs improvement. Focus on error handling and validation.")
        else:
            content.append("🚨 Critical issues detected. Immediate attention required for API stability.")
        
        content.append("")
        
        # Failed Tests Summary
        failed_tests = []
        for category_name, category_data in results["categories"].items():
            if "tests" in category_data:
                for test in category_data["tests"]:
                    if not test.get("success", False):
                        failed_tests.append({
                            "category": category_name,
                            "test": test["name"],
                            "error": test.get("error", "Unknown error")
                        })
        
        if failed_tests:
            content.append("## Failed Tests")
            content.append("")
            for failed in failed_tests[:10]:  # Show first 10
                content.append(f"- **{failed['category']}** - {failed['test']}: {failed['error']}")
            
            if len(failed_tests) > 10:
                content.append(f"- ... and {len(failed_tests) - 10} more failed tests")
            
            content.append("")
        
        # Save report
        with open(output_path, 'w') as f:
            f.write("\n".join(content))
    
    def _generate_csv_report(self, results: Dict[str, Any], output_path: str) -> None:
        """Generate CSV report for analysis"""
        
        import csv
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'category', 'test_name', 'success', 'status_code', 
                'duration_ms', 'error', 'timestamp'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for category_name, category_data in results["categories"].items():
                if "tests" in category_data:
                    for test in category_data["tests"]:
                        writer.writerow({
                            'category': category_name,
                            'test_name': test["name"],
                            'success': test.get("success", False),
                            'status_code': test.get("status_code", ""),
                            'duration_ms': test.get("duration_ms", ""),
                            'error': test.get("error", ""),
                            'timestamp': datetime.utcnow().isoformat()
                        })


def main():
    """Main function for command-line usage"""
    
    parser = argparse.ArgumentParser(description="Run comprehensive API tests")
    parser.add_argument("--url", required=True, help="Base URL for API testing")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("--output", default="test_results", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)
    
    # Run tests
    runner = APITestRunner(
        base_url=args.url,
        auth_token=args.token,
        output_dir=args.output
    )
    
    results = runner.run_comprehensive_tests()
    
    # Print summary
    summary = results["summary"]
    print(f"\nTest Results: {summary['total_passed']}/{summary['total_tests']} passed ({summary['overall_success_rate']:.1f}%)")
    
    # Exit with appropriate code
    exit_code = 0 if summary['overall_success_rate'] >= 80 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
"""
Comprehensive API documentation generator
Creates detailed documentation with examples, testing guides, and interactive docs
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .openapi_spec import generate_openapi_spec
from .api_testing import APITester, create_test_data_generator


class APIDocumentationGenerator:
    """Generate comprehensive API documentation"""
    
    def __init__(self, output_dir: str = "docs"):
        """
        Initialize documentation generator
        
        Args:
            output_dir: Directory to save documentation files
        """
        self.output_dir = output_dir
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """Ensure output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_openapi_docs(self) -> Dict[str, str]:
        """
        Generate OpenAPI documentation in multiple formats
        
        Returns:
            Dictionary with file paths for generated docs
        """
        
        spec = generate_openapi_spec()
        
        # Save as JSON
        json_path = os.path.join(self.output_dir, "openapi.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        
        # Save as YAML
        yaml_path = os.path.join(self.output_dir, "openapi.yaml")
        if YAML_AVAILABLE:
            try:
                with open(yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
            except Exception:
                yaml_path = None
        else:
            yaml_path = None
        
        return {
            "json": json_path,
            "yaml": yaml_path
        }
    
    def generate_api_reference(self) -> str:
        """
        Generate comprehensive API reference documentation
        
        Returns:
            Path to generated API reference file
        """
        
        spec = generate_openapi_spec()
        
        markdown_content = self._create_api_reference_markdown(spec)
        
        reference_path = os.path.join(self.output_dir, "api_reference.md")
        with open(reference_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return reference_path
    
    def _create_api_reference_markdown(self, spec: Dict[str, Any]) -> str:
        """Create markdown API reference from OpenAPI spec"""
        
        content = []
        
        # Header
        info = spec.get("info", {})
        content.append(f"# {info.get('title', 'API Reference')}")
        content.append("")
        content.append(info.get('description', ''))
        content.append("")
        content.append(f"**Version:** {info.get('version', '1.0.0')}")
        content.append("")
        
        # Table of Contents
        content.append("## Table of Contents")
        content.append("")
        
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                operation_id = details.get('operationId', f"{method}_{path}")
                summary = details.get('summary', '')
                content.append(f"- [{method.upper()} {path}](#{operation_id.lower()}) - {summary}")
        
        content.append("")
        
        # Authentication
        content.append("## Authentication")
        content.append("")
        content.append("The API uses JWT Bearer token authentication:")
        content.append("")
        content.append("```")
        content.append("Authorization: Bearer <your-jwt-token>")
        content.append("```")
        content.append("")
        content.append("For testing purposes, you can include `user_id` in the request body.")
        content.append("")
        
        # Error Handling
        content.append("## Error Handling")
        content.append("")
        content.append("All API errors follow a standardized format:")
        content.append("")
        content.append("```json")
        content.append(json.dumps({
            "success": False,
            "error": {
                "code": "ERROR_CODE",
                "message": "User-friendly error message",
                "details": {},
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }, indent=2))
        content.append("```")
        content.append("")
        
        # Common Error Codes
        content.append("### Common Error Codes")
        content.append("")
        error_codes = [
            ("VALIDATION_ERROR", "400", "Request validation failed"),
            ("UNAUTHORIZED", "401", "Authentication required"),
            ("FORBIDDEN", "403", "Access denied"),
            ("RESOURCE_NOT_FOUND", "404", "Resource not found"),
            ("PROCESSING_FAILED", "422", "File or data processing failed"),
            ("INTERNAL_ERROR", "500", "Internal server error"),
            ("SERVICE_UNAVAILABLE", "503", "External service unavailable"),
            ("BEDROCK_ERROR", "503", "AI service temporarily unavailable")
        ]
        
        content.append("| Code | HTTP Status | Description |")
        content.append("|------|-------------|-------------|")
        for code, status, desc in error_codes:
            content.append(f"| `{code}` | {status} | {desc} |")
        
        content.append("")
        
        # API Endpoints
        content.append("## API Endpoints")
        content.append("")
        
        for path, methods in paths.items():
            for method, details in methods.items():
                content.extend(self._create_endpoint_documentation(method, path, details))
        
        return "\n".join(content)
    
    def _create_endpoint_documentation(self, method: str, path: str, details: Dict[str, Any]) -> List[str]:
        """Create documentation for a single endpoint"""
        
        content = []
        
        # Endpoint header
        operation_id = details.get('operationId', f"{method}_{path}")
        summary = details.get('summary', '')
        
        content.append(f"### {method.upper()} {path}")
        content.append("")
        content.append(f"**Operation ID:** `{operation_id}`")
        content.append("")
        content.append(f"**Summary:** {summary}")
        content.append("")
        
        description = details.get('description', '')
        if description:
            content.append(f"**Description:** {description}")
            content.append("")
        
        # Tags
        tags = details.get('tags', [])
        if tags:
            content.append(f"**Tags:** {', '.join(tags)}")
            content.append("")
        
        # Parameters
        parameters = details.get('parameters', [])
        if parameters:
            content.append("**Parameters:**")
            content.append("")
            content.append("| Name | Type | Required | Description | Example |")
            content.append("|------|------|----------|-------------|---------|")
            
            for param in parameters:
                name = param.get('name', '')
                param_type = param.get('schema', {}).get('type', 'string')
                required = param.get('required', False)
                desc = param.get('description', '')
                example = param.get('schema', {}).get('example', '')
                
                required_str = "Yes" if required else "No"
                content.append(f"| `{name}` | {param_type} | {required_str} | {desc} | `{example}` |")
            
            content.append("")
        
        # Request Body
        request_body = details.get('requestBody')
        if request_body:
            content.append("**Request Body:**")
            content.append("")
            
            json_content = request_body.get('content', {}).get('application/json', {})
            schema = json_content.get('schema', {})
            
            if schema:
                content.append("```json")
                content.append(json.dumps(self._create_example_from_schema(schema), indent=2))
                content.append("```")
                content.append("")
        
        # Responses
        responses = details.get('responses', {})
        if responses:
            content.append("**Responses:**")
            content.append("")
            
            for status_code, response_details in responses.items():
                desc = response_details.get('description', '')
                content.append(f"**{status_code}** - {desc}")
                content.append("")
                
                response_content = response_details.get('content', {}).get('application/json', {})
                if response_content:
                    example = response_content.get('example')
                    if example:
                        content.append("```json")
                        content.append(json.dumps(example, indent=2))
                        content.append("```")
                        content.append("")
        
        # Example Usage
        content.append("**Example Usage:**")
        content.append("")
        content.append("```bash")
        
        if method.upper() == 'GET':
            query_params = []
            for param in parameters:
                if param.get('in') == 'query':
                    example = param.get('schema', {}).get('example', 'value')
                    query_params.append(f"{param['name']}={example}")
            
            query_string = '?' + '&'.join(query_params) if query_params else ''
            content.append(f"curl -X GET 'https://api.lms.example.com{path}{query_string}' \\")
            content.append("  -H 'Authorization: Bearer <your-token>'")
        
        else:
            content.append(f"curl -X {method.upper()} 'https://api.lms.example.com{path}' \\")
            content.append("  -H 'Content-Type: application/json' \\")
            content.append("  -H 'Authorization: Bearer <your-token>' \\")
            
            if request_body:
                json_content = request_body.get('content', {}).get('application/json', {})
                schema = json_content.get('schema', {})
                example_data = self._create_example_from_schema(schema)
                
                content.append("  -d '" + json.dumps(example_data, separators=(',', ':')) + "'")
        
        content.append("```")
        content.append("")
        content.append("---")
        content.append("")
        
        return content
    
    def _create_example_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create example data from JSON schema"""
        
        if schema.get('type') == 'object':
            example = {}
            properties = schema.get('properties', {})
            
            for prop_name, prop_schema in properties.items():
                if 'example' in prop_schema:
                    example[prop_name] = prop_schema['example']
                elif prop_schema.get('type') == 'string':
                    example[prop_name] = f"example_{prop_name}"
                elif prop_schema.get('type') == 'integer':
                    example[prop_name] = 123
                elif prop_schema.get('type') == 'number':
                    example[prop_name] = 123.45
                elif prop_schema.get('type') == 'boolean':
                    example[prop_name] = True
                elif prop_schema.get('type') == 'array':
                    example[prop_name] = []
                else:
                    example[prop_name] = None
            
            return example
        
        return {}
    
    def generate_testing_guide(self) -> str:
        """
        Generate comprehensive testing guide
        
        Returns:
            Path to generated testing guide file
        """
        
        content = []
        
        # Header
        content.append("# API Testing Guide")
        content.append("")
        content.append("This guide provides comprehensive instructions for testing the LMS API.")
        content.append("")
        content.append("## Table of Contents")
        content.append("")
        content.append("1. [Quick Start](#quick-start)")
        content.append("2. [Manual Testing](#manual-testing)")
        content.append("3. [Automated Testing](#automated-testing)")
        content.append("4. [Test Scenarios](#test-scenarios)")
        content.append("5. [Error Testing](#error-testing)")
        content.append("6. [Performance Testing](#performance-testing)")
        content.append("7. [Security Testing](#security-testing)")
        content.append("8. [Troubleshooting](#troubleshooting)")
        content.append("")
        
        # Quick Start
        content.append("## Quick Start")
        content.append("")
        content.append("### 1. Set up environment")
        content.append("")
        content.append("```bash")
        content.append("# Install dependencies")
        content.append("pip install requests pytest")
        content.append("")
        content.append("# Set environment variables")
        content.append("export API_BASE_URL=https://api.lms.example.com")
        content.append("export AUTH_TOKEN=your-jwt-token")
        content.append("```")
        content.append("")
        
        # Manual Testing
        content.append("### 2. Manual Testing")
        content.append("")
        content.append("#### Health Check")
        content.append("```bash")
        content.append("curl -X GET '$API_BASE_URL/health'")
        content.append("```")
        content.append("")
        
        content.append("#### Chat Message")
        content.append("```bash")
        content.append("curl -X POST '$API_BASE_URL/api/chat' \\")
        content.append("  -H 'Content-Type: application/json' \\")
        content.append("  -H 'Authorization: Bearer $AUTH_TOKEN' \\")
        content.append("  -d '{")
        content.append('    "message": "Hello, how are you?",')
        content.append('    "user_id": "test-user"')
        content.append("  }'")
        content.append("```")
        content.append("")
        
        content.append("#### File Upload")
        content.append("```bash")
        content.append("curl -X POST '$API_BASE_URL/api/files' \\")
        content.append("  -H 'Content-Type: application/json' \\")
        content.append("  -H 'Authorization: Bearer $AUTH_TOKEN' \\")
        content.append("  -d '{")
        content.append('    "filename": "test_document.pdf",')
        content.append('    "file_size": 1048576,')
        content.append('    "user_id": "test-user"')
        content.append("  }'")
        content.append("```")
        content.append("")
        
        # Automated Testing
        content.append("## Automated Testing")
        content.append("")
        content.append("### Using the API Tester")
        content.append("")
        content.append("```python")
        content.append("from src.shared.api_testing import APITester")
        content.append("")
        content.append("# Initialize tester")
        content.append("tester = APITester('https://api.lms.example.com', auth_token='your-token')")
        content.append("")
        content.append("# Run comprehensive tests")
        content.append("summary = tester.run_comprehensive_tests()")
        content.append("")
        content.append("# Generate report")
        content.append("tester.generate_test_report('test_report.json')")
        content.append("```")
        content.append("")
        
        # Test Scenarios
        content.append("## Test Scenarios")
        content.append("")
        
        test_scenarios = [
            ("Basic Functionality", [
                "Health check returns 200",
                "Chat message returns valid response",
                "File upload generates presigned URL",
                "Get files returns user files list"
            ]),
            ("Validation Errors", [
                "Missing required fields return 400",
                "Invalid file types return 400",
                "Files too large return 400",
                "Empty messages return 400"
            ]),
            ("Authentication", [
                "Missing token returns 401",
                "Invalid token returns 401",
                "Expired token returns 401"
            ]),
            ("Error Handling", [
                "Non-existent resources return 404",
                "Service unavailable returns 503",
                "Internal errors return 500"
            ]),
            ("Performance", [
                "Response times under 3 seconds",
                "Concurrent requests handled properly",
                "Large file uploads work correctly"
            ])
        ]
        
        for scenario_name, tests in test_scenarios:
            content.append(f"### {scenario_name}")
            content.append("")
            for test in tests:
                content.append(f"- {test}")
            content.append("")
        
        # Error Testing
        content.append("## Error Testing Examples")
        content.append("")
        
        content.append("### Validation Errors")
        content.append("")
        content.append("```bash")
        content.append("# Missing message field")
        content.append("curl -X POST '$API_BASE_URL/api/chat' \\")
        content.append("  -H 'Content-Type: application/json' \\")
        content.append("  -H 'Authorization: Bearer $AUTH_TOKEN' \\")
        content.append("  -d '{\"user_id\": \"test-user\"}'")
        content.append("")
        content.append("# Expected: 400 Bad Request with validation error")
        content.append("```")
        content.append("")
        
        content.append("### Authentication Errors")
        content.append("")
        content.append("```bash")
        content.append("# No authentication token")
        content.append("curl -X POST '$API_BASE_URL/api/chat' \\")
        content.append("  -H 'Content-Type: application/json' \\")
        content.append("  -d '{\"message\": \"Hello\", \"user_id\": \"test-user\"}'")
        content.append("")
        content.append("# Expected: 401 Unauthorized")
        content.append("```")
        content.append("")
        
        # Performance Testing
        content.append("## Performance Testing")
        content.append("")
        content.append("### Load Testing with curl")
        content.append("")
        content.append("```bash")
        content.append("# Test concurrent requests")
        content.append("for i in {1..10}; do")
        content.append("  curl -X GET '$API_BASE_URL/health' &")
        content.append("done")
        content.append("wait")
        content.append("```")
        content.append("")
        
        content.append("### Using Apache Bench")
        content.append("")
        content.append("```bash")
        content.append("# 100 requests with 10 concurrent connections")
        content.append("ab -n 100 -c 10 -H 'Authorization: Bearer $AUTH_TOKEN' \\")
        content.append("  '$API_BASE_URL/health'")
        content.append("```")
        content.append("")
        
        content.append("### Comprehensive Performance Testing")
        content.append("")
        content.append("```python")
        content.append("from src.shared.api_test_runner import APITestRunner")
        content.append("")
        content.append("# Run performance tests")
        content.append("runner = APITestRunner('https://api.lms.example.com', 'your-token')")
        content.append("results = runner.run_comprehensive_tests()")
        content.append("")
        content.append("# Check performance metrics")
        content.append("perf_category = results['categories']['performance_&_load']")
        content.append("for test in perf_category['tests']:")
        content.append("    print(f\"{test['name']}: {test.get('avg_duration_ms', 'N/A')}ms\")")
        content.append("```")
        content.append("")
        
        # Security Testing
        content.append("## Security Testing")
        content.append("")
        content.append("### SQL Injection Testing")
        content.append("")
        content.append("```bash")
        content.append("# Test SQL injection attempts")
        content.append("curl -X POST '$API_BASE_URL/api/chat' \\")
        content.append("  -H 'Content-Type: application/json' \\")
        content.append("  -H 'Authorization: Bearer $AUTH_TOKEN' \\")
        content.append("  -d '{")
        content.append("    \"message\": \"\\'; DROP TABLE users; --\",")
        content.append("    \"user_id\": \"test-user\"")
        content.append("  }'")
        content.append("")
        content.append("# Should return 200 with safe handling or 400 with validation error")
        content.append("```")
        content.append("")
        
        content.append("### XSS Testing")
        content.append("")
        content.append("```bash")
        content.append("# Test XSS attempts")
        content.append("curl -X POST '$API_BASE_URL/api/chat' \\")
        content.append("  -H 'Content-Type: application/json' \\")
        content.append("  -H 'Authorization: Bearer $AUTH_TOKEN' \\")
        content.append("  -d '{")
        content.append("    \"message\": \"<script>alert(\\\"xss\\\")</script>\",")
        content.append("    \"user_id\": \"test-user\"")
        content.append("  }'")
        content.append("")
        content.append("# Should handle gracefully without executing script")
        content.append("```")
        content.append("")
        
        content.append("### File Upload Security")
        content.append("")
        content.append("```bash")
        content.append("# Test malicious file upload")
        content.append("curl -X POST '$API_BASE_URL/api/files' \\")
        content.append("  -H 'Content-Type: application/json' \\")
        content.append("  -H 'Authorization: Bearer $AUTH_TOKEN' \\")
        content.append("  -d '{")
        content.append("    \"filename\": \"../../../etc/passwd\",")
        content.append("    \"file_size\": 1024,")
        content.append("    \"user_id\": \"test-user\"")
        content.append("  }'")
        content.append("")
        content.append("# Should return 400 with validation error")
        content.append("```")
        content.append("")
        
        # Troubleshooting
        content.append("## Troubleshooting")
        content.append("")
        
        troubleshooting_items = [
            ("503 Service Unavailable", "Check AWS service status and credentials"),
            ("401 Unauthorized", "Verify JWT token is valid and not expired"),
            ("400 Bad Request", "Check request format and required fields"),
            ("Timeout errors", "Check network connectivity and service health"),
            ("Rate limiting", "Reduce request frequency or contact support")
        ]
        
        content.append("| Error | Solution |")
        content.append("|-------|----------|")
        for error, solution in troubleshooting_items:
            content.append(f"| {error} | {solution} |")
        
        content.append("")
        
        # Save testing guide
        guide_path = os.path.join(self.output_dir, "testing_guide.md")
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
        
        return guide_path
    
    def generate_postman_collection(self) -> str:
        """
        Generate Postman collection for API testing
        
        Returns:
            Path to generated Postman collection file
        """
        
        spec = generate_openapi_spec()
        
        collection = {
            "info": {
                "name": spec["info"]["title"],
                "description": spec["info"]["description"],
                "version": spec["info"]["version"],
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{auth_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "https://api.lms.example.com",
                    "type": "string"
                },
                {
                    "key": "auth_token",
                    "value": "your-jwt-token-here",
                    "type": "string"
                }
            ],
            "item": []
        }
        
        # Convert OpenAPI paths to Postman requests
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                request_item = self._create_postman_request(method, path, details)
                collection["item"].append(request_item)
        
        # Save Postman collection
        collection_path = os.path.join(self.output_dir, "postman_collection.json")
        with open(collection_path, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=2)
        
        return collection_path
    
    def _create_postman_request(self, method: str, path: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Create Postman request from OpenAPI endpoint"""
        
        request_item = {
            "name": details.get('summary', f"{method.upper()} {path}"),
            "request": {
                "method": method.upper(),
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json",
                        "type": "text"
                    }
                ],
                "url": {
                    "raw": "{{base_url}}" + path,
                    "host": ["{{base_url}}"],
                    "path": path.strip('/').split('/')
                }
            }
        }
        
        # Add authentication if required
        if not details.get('security') == []:
            request_item["request"]["auth"] = {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{auth_token}}",
                        "type": "string"
                    }
                ]
            }
        
        # Add query parameters
        parameters = details.get('parameters', [])
        query_params = [p for p in parameters if p.get('in') == 'query']
        if query_params:
            request_item["request"]["url"]["query"] = []
            for param in query_params:
                request_item["request"]["url"]["query"].append({
                    "key": param["name"],
                    "value": param.get("schema", {}).get("example", ""),
                    "description": param.get("description", "")
                })
        
        # Add request body
        request_body = details.get('requestBody')
        if request_body:
            json_content = request_body.get('content', {}).get('application/json', {})
            schema = json_content.get('schema', {})
            example_data = self._create_example_from_schema(schema)
            
            request_item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(example_data, indent=2),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
        
        return request_item
    
    def generate_all_documentation(self) -> Dict[str, str]:
        """
        Generate all documentation formats
        
        Returns:
            Dictionary with paths to all generated files
        """
        
        print("Generating comprehensive API documentation...")
        
        results = {}
        
        # OpenAPI specs
        openapi_files = self.generate_openapi_docs()
        results.update(openapi_files)
        
        # API reference
        results["api_reference"] = self.generate_api_reference()
        
        # Testing guide
        results["testing_guide"] = self.generate_testing_guide()
        
        # Postman collection
        results["postman_collection"] = self.generate_postman_collection()
        
        print(f"Documentation generated in {self.output_dir}/")
        for doc_type, file_path in results.items():
            if file_path:
                print(f"  {doc_type}: {file_path}")
        
        return results


if __name__ == "__main__":
    # Generate all documentation
    generator = APIDocumentationGenerator()
    generator.generate_all_documentation()
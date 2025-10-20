# API Testing Guide

This guide provides comprehensive instructions for testing the LMS API.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Manual Testing](#manual-testing)
3. [Automated Testing](#automated-testing)
4. [Test Scenarios](#test-scenarios)
5. [Error Testing](#error-testing)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Set up environment

```bash
# Install dependencies
pip install requests pytest

# Set environment variables
export API_BASE_URL=https://api.lms.example.com
export AUTH_TOKEN=your-jwt-token
```

### 2. Manual Testing

#### Health Check
```bash
curl -X GET '$API_BASE_URL/health'
```

#### Chat Message
```bash
curl -X POST '$API_BASE_URL/api/chat' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $AUTH_TOKEN' \
  -d '{
    "message": "Hello, how are you?",
    "user_id": "test-user"
  }'
```

#### File Upload
```bash
curl -X POST '$API_BASE_URL/api/files' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $AUTH_TOKEN' \
  -d '{
    "filename": "test_document.pdf",
    "file_size": 1048576,
    "user_id": "test-user"
  }'
```

## Automated Testing

### Using the API Tester

```python
from src.shared.api_testing import APITester

# Initialize tester
tester = APITester('https://api.lms.example.com', auth_token='your-token')

# Run comprehensive tests
summary = tester.run_comprehensive_tests()

# Generate report
tester.generate_test_report('test_report.json')
```

## Test Scenarios

### Basic Functionality

- Health check returns 200
- Chat message returns valid response
- File upload generates presigned URL
- Get files returns user files list

### Validation Errors

- Missing required fields return 400
- Invalid file types return 400
- Files too large return 400
- Empty messages return 400

### Authentication

- Missing token returns 401
- Invalid token returns 401
- Expired token returns 401

### Error Handling

- Non-existent resources return 404
- Service unavailable returns 503
- Internal errors return 500

### Performance

- Response times under 3 seconds
- Concurrent requests handled properly
- Large file uploads work correctly

## Error Testing Examples

### Validation Errors

```bash
# Missing message field
curl -X POST '$API_BASE_URL/api/chat' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $AUTH_TOKEN' \
  -d '{"user_id": "test-user"}'

# Expected: 400 Bad Request with validation error
```

### Authentication Errors

```bash
# No authentication token
curl -X POST '$API_BASE_URL/api/chat' \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello", "user_id": "test-user"}'

# Expected: 401 Unauthorized
```

## Performance Testing

### Load Testing with curl

```bash
# Test concurrent requests
for i in {1..10}; do
  curl -X GET '$API_BASE_URL/health' &
done
wait
```

### Using Apache Bench

```bash
# 100 requests with 10 concurrent connections
ab -n 100 -c 10 -H 'Authorization: Bearer $AUTH_TOKEN' \
  '$API_BASE_URL/health'
```

### Comprehensive Performance Testing

```python
from src.shared.api_test_runner import APITestRunner

# Run performance tests
runner = APITestRunner('https://api.lms.example.com', 'your-token')
results = runner.run_comprehensive_tests()

# Check performance metrics
perf_category = results['categories']['performance_&_load']
for test in perf_category['tests']:
    print(f"{test['name']}: {test.get('avg_duration_ms', 'N/A')}ms")
```

## Security Testing

### SQL Injection Testing

```bash
# Test SQL injection attempts
curl -X POST '$API_BASE_URL/api/chat' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $AUTH_TOKEN' \
  -d '{
    "message": "\'; DROP TABLE users; --",
    "user_id": "test-user"
  }'

# Should return 200 with safe handling or 400 with validation error
```

### XSS Testing

```bash
# Test XSS attempts
curl -X POST '$API_BASE_URL/api/chat' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $AUTH_TOKEN' \
  -d '{
    "message": "<script>alert(\"xss\")</script>",
    "user_id": "test-user"
  }'

# Should handle gracefully without executing script
```

### File Upload Security

```bash
# Test malicious file upload
curl -X POST '$API_BASE_URL/api/files' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $AUTH_TOKEN' \
  -d '{
    "filename": "../../../etc/passwd",
    "file_size": 1024,
    "user_id": "test-user"
  }'

# Should return 400 with validation error
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| 503 Service Unavailable | Check AWS service status and credentials |
| 401 Unauthorized | Verify JWT token is valid and not expired |
| 400 Bad Request | Check request format and required fields |
| Timeout errors | Check network connectivity and service health |
| Rate limiting | Reduce request frequency or contact support |

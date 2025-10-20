# LMS AI Backend API


# Learning Management System AI Backend API

A comprehensive API for an AI-powered Learning Management System built on AWS Bedrock AgentCore.

## Features

- **AI Chat**: Intelligent conversations with RAG-enhanced responses
- **File Processing**: Upload and process educational documents with AWS Textract
- **Quiz Generation**: AI-generated quizzes from uploaded content
- **Voice Interviews**: Real-time voice interviews with AI
- **Learning Analytics**: Track progress and generate insights
- **Multi-language Support**: Translation and language detection

## Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

For testing purposes, you can also include `user_id` in the request body.

## Error Handling

All errors follow a standardized format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": {},
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse. Current limits:
- 100 requests per minute per user
- 10 file uploads per hour per user
- 5 concurrent voice interview sessions per user
            

**Version:** 1.0.0

## Table of Contents

- [GET /health](#gethealth) - Health check
- [POST /api/chat](#sendchatmessage) - Send chat message
- [GET /api/chat/history](#getchathistory) - Get conversation history
- [POST /api/files](#uploadfile) - Upload file
- [GET /api/files](#getuserfiles) - Get user files
- [POST /api/files/process](#processfile) - Process uploaded file
- [POST /api/quiz/generate](#generatequiz) - Generate quiz
- [POST /api/quiz/submit](#submitquiz) - Submit quiz answers
- [GET /api/analytics](#getlearninganalytics) - Get learning analytics
- [POST /api/interview/start](#startvoiceinterview) - Start voice interview

## Authentication

The API uses JWT Bearer token authentication:

```
Authorization: Bearer <your-jwt-token>
```

For testing purposes, you can include `user_id` in the request body.

## Error Handling

All API errors follow a standardized format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": {},
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Access denied |
| `RESOURCE_NOT_FOUND` | 404 | Resource not found |
| `PROCESSING_FAILED` | 422 | File or data processing failed |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable |
| `BEDROCK_ERROR` | 503 | AI service temporarily unavailable |

## API Endpoints

### GET /health

**Operation ID:** `getHealth`

**Summary:** Health check

**Description:** Check the health status of the API and its dependencies

**Tags:** Health

**Responses:**

**200** - System is healthy

```json
{
  "success": true,
  "status": "healthy",
  "services": {
    "dynamodb": "healthy",
    "s3": "healthy",
    "bedrock": "healthy",
    "pinecone": "configured"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**503** - System is degraded or unhealthy

```json
{
  "success": true,
  "status": "degraded",
  "services": {
    "dynamodb": "healthy",
    "s3": "unhealthy: Access denied",
    "bedrock": "healthy",
    "pinecone": "not configured"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Example Usage:**

```bash
curl -X GET 'https://api.lms.example.com/health' \
  -H 'Authorization: Bearer <your-token>'
```

---

### POST /api/chat

**Operation ID:** `sendChatMessage`

**Summary:** Send chat message

**Description:** Send a message to the AI assistant and get a response with RAG enhancement

**Tags:** Chat

**Request Body:**

```json
{}
```

**Responses:**

**200** - Chat response generated successfully

**400** - 

**401** - 

**500** - 

**503** - 

**Example Usage:**

```bash
curl -X POST 'https://api.lms.example.com/api/chat' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{}'
```

---

### GET /api/chat/history

**Operation ID:** `getChatHistory`

**Summary:** Get conversation history

**Description:** Retrieve conversation history for a user or specific conversation

**Tags:** Chat

**Parameters:**

| Name | Type | Required | Description | Example |
|------|------|----------|-------------|---------|
| `user_id` | string | No | User ID (for testing without auth) | `` |
| `conversation_id` | string | No | Specific conversation ID | `` |
| `limit` | integer | No | Maximum number of messages to return | `` |

**Responses:**

**200** - Conversation history retrieved successfully

**401** - 

**404** - 

**500** - 

**Example Usage:**

```bash
curl -X GET 'https://api.lms.example.com/api/chat/history?user_id=value&conversation_id=value&limit=value' \
  -H 'Authorization: Bearer <your-token>'
```

---

### POST /api/files

**Operation ID:** `uploadFile`

**Summary:** Upload file

**Description:** Generate presigned URL for file upload and create file metadata

**Tags:** Files

**Request Body:**

```json
{}
```

**Responses:**

**200** - Upload URL generated successfully

**400** - 

**401** - 

**500** - 

**Example Usage:**

```bash
curl -X POST 'https://api.lms.example.com/api/files' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{}'
```

---

### GET /api/files

**Operation ID:** `getUserFiles`

**Summary:** Get user files

**Description:** Retrieve list of files uploaded by the user

**Tags:** Files

**Parameters:**

| Name | Type | Required | Description | Example |
|------|------|----------|-------------|---------|
| `user_id` | string | No | User ID (for testing without auth) | `` |

**Responses:**

**200** - Files retrieved successfully

**401** - 

**500** - 

**Example Usage:**

```bash
curl -X GET 'https://api.lms.example.com/api/files?user_id=value' \
  -H 'Authorization: Bearer <your-token>'
```

---

### POST /api/files/process

**Operation ID:** `processFile`

**Summary:** Process uploaded file

**Description:** Process uploaded file for RAG with text extraction and vector storage

**Tags:** Files

**Request Body:**

```json
{
  "file_id": "file-123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user-123"
}
```

**Responses:**

**200** - File processed successfully

**400** - 

**401** - 

**404** - 

**422** - Processing failed

**500** - 

**Example Usage:**

```bash
curl -X POST 'https://api.lms.example.com/api/files/process' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{"file_id":"file-123e4567-e89b-12d3-a456-426614174000","user_id":"user-123"}'
```

---

### POST /api/quiz/generate

**Operation ID:** `generateQuiz`

**Summary:** Generate quiz

**Description:** Generate AI-powered quiz questions from uploaded documents

**Tags:** Quiz

**Request Body:**

```json
{
  "subject_id": "physics101",
  "document_ids": [
    "file-123",
    "file-456"
  ],
  "num_questions": 123,
  "difficulty": "example_difficulty",
  "user_id": "user-123"
}
```

**Responses:**

**200** - Quiz generated successfully

**400** - 

**401** - 

**500** - 

**503** - 

**Example Usage:**

```bash
curl -X POST 'https://api.lms.example.com/api/quiz/generate' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{"subject_id":"physics101","document_ids":["file-123","file-456"],"num_questions":123,"difficulty":"example_difficulty","user_id":"user-123"}'
```

---

### POST /api/quiz/submit

**Operation ID:** `submitQuiz`

**Summary:** Submit quiz answers

**Description:** Submit quiz answers and get scoring results

**Tags:** Quiz

**Request Body:**

```json
{
  "quiz_id": "quiz-123e4567-e89b-12d3-a456-426614174000",
  "answers": {
    "q1": "A",
    "q2": "C",
    "q3": "B"
  },
  "user_id": "user-123"
}
```

**Responses:**

**200** - Quiz submitted and scored successfully

**400** - 

**401** - 

**404** - 

**500** - 

**Example Usage:**

```bash
curl -X POST 'https://api.lms.example.com/api/quiz/submit' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{"quiz_id":"quiz-123e4567-e89b-12d3-a456-426614174000","answers":{"q1":"A","q2":"C","q3":"B"},"user_id":"user-123"}'
```

---

### GET /api/analytics

**Operation ID:** `getLearningAnalytics`

**Summary:** Get learning analytics

**Description:** Retrieve learning progress and analytics for the user

**Tags:** Analytics

**Parameters:**

| Name | Type | Required | Description | Example |
|------|------|----------|-------------|---------|
| `user_id` | string | No | User ID (for testing without auth) | `` |
| `subject_id` | string | No | Subject filter | `` |
| `date_from` | string | No | Start date (ISO format) | `` |
| `date_to` | string | No | End date (ISO format) | `` |

**Responses:**

**200** - Analytics retrieved successfully

**401** - 

**500** - 

**Example Usage:**

```bash
curl -X GET 'https://api.lms.example.com/api/analytics?user_id=value&subject_id=value&date_from=value&date_to=value' \
  -H 'Authorization: Bearer <your-token>'
```

---

### POST /api/interview/start

**Operation ID:** `startVoiceInterview`

**Summary:** Start voice interview

**Description:** Start a voice interview session and get WebSocket connection details

**Tags:** Voice

**Request Body:**

```json
{
  "subject_id": "physics101",
  "interview_type": "general",
  "duration_minutes": 123,
  "user_id": "user-123"
}
```

**Responses:**

**200** - Interview session started successfully

**400** - 

**401** - 

**500** - 

**Example Usage:**

```bash
curl -X POST 'https://api.lms.example.com/api/interview/start' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <your-token>' \
  -d '{"subject_id":"physics101","interview_type":"general","duration_minutes":123,"user_id":"user-123"}'
```

---

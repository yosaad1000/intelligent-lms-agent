# 🔌 LMS AI Agent - API Documentation

## 📊 API Overview

The LMS AI Agent provides a comprehensive RESTful API built on AWS serverless architecture. The API enables intelligent learning management through AI-powered chat, document processing, quiz generation, voice interviews, and learning analytics.

### 🏗️ Architecture
- **Base URL**: `https://api.lms.example.com`
- **Protocol**: HTTPS only
- **Format**: JSON
- **Authentication**: JWT Bearer tokens
- **Rate Limiting**: 100 requests/minute per user

### 🔐 Authentication

All API endpoints (except health check) require JWT authentication:

```bash
curl -H "Authorization: Bearer <your-jwt-token>" \
     -H "Content-Type: application/json" \
     https://api.lms.example.com/api/chat
```

For development/testing, you can include `user_id` in the request body instead of using JWT tokens.

## 🎯 Core Endpoints

### 1. Health Check

**GET** `/health`

Check the health status of the API and its dependencies.

**No authentication required**

```bash
curl https://api.lms.example.com/health
```

**Response:**
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

### 2. AI Chat

**POST** `/api/chat`

Send a message to the AI assistant and receive an intelligent response with RAG enhancement.

**Request:**
```json
{
  "message": "What is machine learning?",
  "conversation_id": "conv-123e4567-e89b-12d3-a456-426614174000",
  "subject_id": "cs101",
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed...",
  "conversation_id": "conv-123e4567-e89b-12d3-a456-426614174000",
  "citations": [
    {
      "source": "machine_learning_basics.pdf",
      "chunk_index": 2,
      "score": 0.95,
      "page": 15
    }
  ],
  "rag_documents_used": 3,
  "rag_enhanced": true,
  "bedrock_agent_used": true,
  "subject_context": "cs101",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X POST https://api.lms.example.com/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "subject_id": "physics101"
  }'
```

### 3. Chat History

**GET** `/api/chat/history`

Retrieve conversation history for a user or specific conversation.

**Query Parameters:**
- `user_id` (string, optional): User ID for testing
- `conversation_id` (string, optional): Specific conversation ID
- `limit` (integer, optional): Max messages to return (default: 20)

**Response:**
```json
{
  "success": true,
  "conversation_id": "conv-123e4567-e89b-12d3-a456-426614174000",
  "messages": [
    {
      "message_id": "msg-123",
      "message_type": "user",
      "content": "What is machine learning?",
      "timestamp": 1704067200,
      "citations": []
    },
    {
      "message_id": "msg-124",
      "message_type": "assistant",
      "content": "Machine learning is...",
      "timestamp": 1704067205,
      "citations": [
        {
          "source": "ml_textbook.pdf",
          "score": 0.92
        }
      ]
    }
  ],
  "total_messages": 2
}
```

### 4. File Upload

**POST** `/api/files`

Generate a presigned URL for file upload and create file metadata.

**Request:**
```json
{
  "filename": "machine_learning_lecture.pdf",
  "file_size": 2048576,
  "subject_id": "cs101",
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "file_id": "file-123e4567-e89b-12d3-a456-426614174000",
  "upload_url": "https://s3.amazonaws.com/bucket/key?signature=...",
  "status": "ready_for_upload",
  "process_url": "/api/files/process",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Upload Process:**
1. Call `/api/files` to get presigned URL
2. Upload file directly to S3 using the presigned URL
3. Call `/api/files/process` to process the file for RAG

**S3 Upload Example:**
```bash
# Step 1: Get presigned URL
RESPONSE=$(curl -X POST https://api.lms.example.com/api/files \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"filename": "notes.pdf", "file_size": 1024000}')

# Step 2: Extract upload URL
UPLOAD_URL=$(echo $RESPONSE | jq -r '.upload_url')

# Step 3: Upload file to S3
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: application/pdf" \
  --data-binary @notes.pdf

# Step 4: Process file
FILE_ID=$(echo $RESPONSE | jq -r '.file_id')
curl -X POST https://api.lms.example.com/api/files/process \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\": \"$FILE_ID\"}"
```

### 5. File Processing

**POST** `/api/files/process`

Process uploaded file for RAG with text extraction and vector storage.

**Request:**
```json
{
  "file_id": "file-123e4567-e89b-12d3-a456-426614174000",
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "file_id": "file-123e4567-e89b-12d3-a456-426614174000",
  "status": "processed",
  "chunks_created": 25,
  "vectors_stored": 25,
  "message": "File processed successfully and ready for RAG queries"
}
```

### 6. Get User Files

**GET** `/api/files`

Retrieve list of files uploaded by the user.

**Query Parameters:**
- `user_id` (string, optional): User ID for testing

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "file_id": "file-123",
      "filename": "lecture_notes.pdf",
      "status": "processed",
      "processing_status": "completed",
      "upload_timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1
}
```

### 7. Quiz Generation

**POST** `/api/quiz/generate`

Generate AI-powered quiz questions from uploaded documents.

**Request:**
```json
{
  "subject_id": "physics101",
  "document_ids": ["file-123", "file-456"],
  "num_questions": 5,
  "difficulty": "intermediate",
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "quiz_id": "quiz-123e4567-e89b-12d3-a456-426614174000",
  "questions": [
    {
      "question_id": "q1",
      "question_text": "What is the fundamental principle of quantum mechanics?",
      "options": [
        {
          "option_id": "A",
          "text": "Wave-particle duality",
          "is_correct": true
        },
        {
          "option_id": "B",
          "text": "Conservation of energy",
          "is_correct": false
        },
        {
          "option_id": "C",
          "text": "Newton's laws",
          "is_correct": false
        },
        {
          "option_id": "D",
          "text": "Thermodynamics",
          "is_correct": false
        }
      ],
      "explanation": "Wave-particle duality is indeed the fundamental principle that describes how quantum objects exhibit both wave and particle properties.",
      "source_document": "quantum_physics.pdf",
      "difficulty": "intermediate"
    }
  ],
  "subject_id": "physics101",
  "created_at": "2024-01-01T12:00:00Z",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 8. Quiz Submission

**POST** `/api/quiz/submit`

Submit quiz answers and get scoring results.

**Request:**
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

**Response:**
```json
{
  "success": true,
  "quiz_id": "quiz-123e4567-e89b-12d3-a456-426614174000",
  "score": 80.0,
  "total_questions": 5,
  "correct_answers": 4,
  "results": [
    {
      "question_id": "q1",
      "user_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "explanation": "Correct! Wave-particle duality is the fundamental principle."
    },
    {
      "question_id": "q2",
      "user_answer": "C",
      "correct_answer": "B",
      "is_correct": false,
      "explanation": "The correct answer is B. Energy quantization is key to understanding atomic structure."
    }
  ],
  "submitted_at": "2024-01-01T12:00:00Z",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 9. Learning Analytics

**GET** `/api/analytics`

Retrieve learning progress and analytics for the user.

**Query Parameters:**
- `user_id` (string, optional): User ID for testing
- `subject_id` (string, optional): Subject filter
- `date_from` (string, optional): Start date (ISO format)
- `date_to` (string, optional): End date (ISO format)

**Response:**
```json
{
  "success": true,
  "user_id": "user-123",
  "total_interactions": 150,
  "documents_processed": 12,
  "quizzes_taken": 8,
  "average_score": 85.5,
  "study_time_hours": 24.5,
  "concept_masteries": [
    {
      "concept": "Machine Learning Basics",
      "mastery_level": 0.85,
      "interaction_count": 25,
      "last_interaction": "2024-01-01T12:00:00Z"
    },
    {
      "concept": "Neural Networks",
      "mastery_level": 0.72,
      "interaction_count": 18,
      "last_interaction": "2024-01-01T11:30:00Z"
    }
  ],
  "recommendations": [
    "Focus more on deep learning concepts",
    "Practice with more advanced neural network architectures",
    "Review backpropagation algorithm"
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 10. Voice Interview

**POST** `/api/interview/start`

Start a voice interview session and get WebSocket connection details.

**Request:**
```json
{
  "subject_id": "physics101",
  "interview_type": "general",
  "duration_minutes": 15,
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "interview-123e4567-e89b-12d3-a456-426614174000",
  "websocket_url": "wss://api.lms.example.com/ws/interview/interview-123e4567-e89b-12d3-a456-426614174000",
  "initial_question": "Hello! Let's start with a basic question about physics. Can you explain what force is?",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔧 Advanced Features

### Bedrock Agent Integration

The API integrates with AWS Bedrock AgentCore for advanced AI capabilities:

**Agent Proxy Endpoint:**
**POST** `/api/agent/invoke`

```json
{
  "message": "Analyze this document and create a study plan",
  "session_id": "session-123",
  "user_id": "user-123",
  "context": {
    "documents": ["file-123", "file-456"],
    "subject": "machine-learning"
  }
}
```

**Response:**
```json
{
  "success": true,
  "response": "Based on your uploaded documents, I've created a personalized study plan...",
  "session_id": "session-123",
  "citations": [
    {
      "source": "Knowledge Base",
      "confidence": 0.95,
      "content": "Machine learning fundamentals...",
      "metadata": {"document": "ml_textbook.pdf"}
    }
  ],
  "tools_used": ["document_processor", "quiz_generator"],
  "trace_data": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "type": "knowledge_base",
      "retrieval_count": 5
    }
  ],
  "timestamp": "2024-01-01T12:00:00Z",
  "agent_id": "ZTBBVSC6Y1",
  "message_id": "msg-uuid"
}
```

### Session Management

**GET** `/api/session/history?session_id=session-123`

Get conversation history for a specific session:

```json
{
  "success": true,
  "session_id": "session-123",
  "conversation_history": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "user_message": "Explain neural networks",
      "agent_response": "Neural networks are...",
      "tools_used": ["knowledge_base_retrieval"]
    }
  ],
  "message_count": 1,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### File Upload with Presigned URLs

**POST** `/api/upload/presigned`

Generate presigned URL for direct S3 upload:

```json
{
  "file_name": "lecture_notes.pdf",
  "content_type": "application/pdf",
  "user_id": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "upload_url": "https://s3.amazonaws.com/bucket/users/user-123/documents/uuid-lecture_notes.pdf?signature=...",
  "file_key": "users/user-123/documents/uuid-lecture_notes.pdf",
  "bucket": "lms-documents-dev",
  "expires_in": 3600
}
```

### Document Management

**GET** `/api/documents?user_id=user-123`

List user's uploaded documents:

```json
{
  "success": true,
  "documents": [
    {
      "key": "users/user-123/documents/uuid-notes.pdf",
      "filename": "notes.pdf",
      "size": 2048576,
      "last_modified": "2024-01-01T12:00:00Z",
      "download_url": "https://s3.amazonaws.com/bucket/key?signature=..."
    }
  ],
  "count": 1,
  "user_id": "user-123",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🚨 Error Handling

All API endpoints return standardized error responses:

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": {},
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Access denied |
| `RESOURCE_NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | External service error |

### Error Examples

**400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided data is invalid",
    "details": {
      "field": "message",
      "reason": "Required field missing"
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Please log in to access this resource",
    "details": {},
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**503 Service Unavailable:**
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "A service is temporarily unavailable. Please try again later.",
    "details": {
      "service": "bedrock"
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## 📊 Rate Limiting

The API implements rate limiting to ensure fair usage:

- **General Endpoints**: 100 requests per minute per user
- **File Upload**: 10 uploads per hour per user
- **Voice Interview**: 5 concurrent sessions per user
- **Quiz Generation**: 20 quizzes per hour per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067260
```

## 🔍 Testing & Development

### Development Environment

For testing without authentication, include `user_id` in request bodies:

```bash
curl -X POST https://api.lms.example.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "user_id": "test-user-123"
  }'
```

### Health Check for Dependencies

The health endpoint provides detailed status of all dependencies:

```bash
curl https://api.lms.example.com/health
```

**Healthy Response:**
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

**Degraded Response:**
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

### Capabilities Endpoint

**GET** `/api/capabilities`

Get information about agent capabilities:

```json
{
  "success": true,
  "capabilities": [
    "Document Analysis & Summarization",
    "Quiz Generation from Content",
    "Learning Analytics & Progress Tracking",
    "Voice Interview Practice",
    "Multi-language Support",
    "Citation-backed Responses",
    "Contextual Learning Assistance"
  ],
  "agent_info": {
    "agent_id": "ZTBBVSC6Y1",
    "alias_id": "TSTALIASID",
    "version": "1.0.0"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 📚 SDK Examples

### Python SDK Example

```python
import requests
import json

class LMSClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json'
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    def chat(self, message, conversation_id=None, subject_id=None, user_id=None):
        """Send a chat message to the AI assistant"""
        data = {'message': message}
        if conversation_id:
            data['conversation_id'] = conversation_id
        if subject_id:
            data['subject_id'] = subject_id
        if user_id:
            data['user_id'] = user_id
        
        response = requests.post(
            f'{self.base_url}/api/chat',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def upload_file(self, filename, file_size, subject_id=None, user_id=None):
        """Get presigned URL for file upload"""
        data = {
            'filename': filename,
            'file_size': file_size
        }
        if subject_id:
            data['subject_id'] = subject_id
        if user_id:
            data['user_id'] = user_id
        
        response = requests.post(
            f'{self.base_url}/api/files',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def generate_quiz(self, subject_id, num_questions=5, difficulty='intermediate', user_id=None):
        """Generate a quiz"""
        data = {
            'subject_id': subject_id,
            'num_questions': num_questions,
            'difficulty': difficulty
        }
        if user_id:
            data['user_id'] = user_id
        
        response = requests.post(
            f'{self.base_url}/api/quiz/generate',
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage
client = LMSClient('https://api.lms.example.com', token='your-jwt-token')

# Chat with AI
response = client.chat('What is machine learning?', subject_id='cs101')
print(response['response'])

# Upload file
upload_info = client.upload_file('notes.pdf', 1024000, subject_id='cs101')
print(f"Upload URL: {upload_info['upload_url']}")

# Generate quiz
quiz = client.generate_quiz('cs101', num_questions=3)
print(f"Generated {len(quiz['questions'])} questions")
```

### JavaScript SDK Example

```javascript
class LMSClient {
    constructor(baseUrl, token = null) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json'
        };
        if (token) {
            this.headers['Authorization'] = `Bearer ${token}`;
        }
    }

    async chat(message, options = {}) {
        const data = { message, ...options };
        
        const response = await fetch(`${this.baseUrl}/api/chat`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return response.json();
    }

    async uploadFile(filename, fileSize, options = {}) {
        const data = { 
            filename, 
            file_size: fileSize, 
            ...options 
        };
        
        const response = await fetch(`${this.baseUrl}/api/files`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return response.json();
    }

    async generateQuiz(subjectId, options = {}) {
        const data = { 
            subject_id: subjectId,
            num_questions: 5,
            difficulty: 'intermediate',
            ...options 
        };
        
        const response = await fetch(`${this.baseUrl}/api/quiz/generate`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        
        return response.json();
    }
}

// Usage
const client = new LMSClient('https://api.lms.example.com', 'your-jwt-token');

// Chat with AI
const chatResponse = await client.chat('Explain quantum physics', {
    subject_id: 'physics101'
});
console.log(chatResponse.response);

// Generate quiz
const quiz = await client.generateQuiz('physics101', {
    num_questions: 3,
    difficulty: 'beginner'
});
console.log(`Generated ${quiz.questions.length} questions`);
```

## 🔗 WebSocket API (Voice Interviews)

For real-time voice interviews, the API provides WebSocket connections:

### Connection
```javascript
const ws = new WebSocket('wss://api.lms.example.com/ws/interview/session-id');

ws.onopen = () => {
    console.log('Connected to voice interview');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Send audio data
ws.send(JSON.stringify({
    type: 'audio',
    data: base64AudioData
}));
```

### WebSocket Message Types

**Audio Input:**
```json
{
  "type": "audio",
  "data": "base64-encoded-audio-data",
  "timestamp": 1704067200
}
```

**Transcription Result:**
```json
{
  "type": "transcription",
  "text": "The user said this",
  "confidence": 0.95,
  "timestamp": 1704067205
}
```

**AI Response:**
```json
{
  "type": "response",
  "text": "That's a great answer! Let me ask you about...",
  "audio_url": "https://s3.amazonaws.com/bucket/audio-response.mp3",
  "timestamp": 1704067210
}
```

---

## 📖 Additional Resources

- **OpenAPI Specification**: [Download JSON](docs/openapi.json) | [Download YAML](docs/openapi.yaml)
- **Postman Collection**: [Import Collection](docs/postman_collection.json)
- **Testing Guide**: [Manual Testing Instructions](TESTING_INSTRUCTIONS.md)
- **Architecture Documentation**: [System Architecture](ARCHITECTURE.md)
- **Deployment Guide**: [AWS Deployment](DEPLOYMENT.md)

## 🆘 Support

For API support and questions:
- **Documentation**: This guide and linked resources
- **GitHub Issues**: [Report bugs or request features](https://github.com/yosaad1000/intelligent-lms-agent/issues)
- **Email**: support@lms-api.com

---

**🚀 Ready to build intelligent learning experiences with our AI-powered API!**
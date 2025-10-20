# Subject and Assignment Integration API Specification

## Overview

This document specifies the API endpoints for subject-specific AI chat, file management, assignment-based quiz generation, teacher dashboard analytics, and student progress tracking.

## Authentication

All endpoints require authentication via Supabase JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## API Endpoints

### Subject-Specific Chat

#### POST /api/chat/subjects/{subject_id}
Start or continue a subject-specific AI chat conversation.

**Parameters:**
- `subject_id` (path): Subject identifier

**Request Body:**
```json
{
  "message": "Explain Newton's first law of motion",
  "conversation_id": "optional_existing_conversation_id"
}
```

**Response:**
```json
{
  "conversation_id": "subj_physics101_user123_20241020",
  "response": "Newton's first law states that an object at rest stays at rest...",
  "subject_context": {
    "subject_name": "Physics 101",
    "recent_topics": ["mechanics", "forces", "motion"]
  },
  "citations": [
    {
      "source": "physics_notes.pdf",
      "content": "Newton's laws of motion..."
    }
  ]
}
```

#### GET /api/chat/subjects/{subject_id}/history
Get chat history for a subject.

**Parameters:**
- `subject_id` (path): Subject identifier
- `limit` (query, optional): Number of conversations to return (default: 20)

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "subj_physics101_user123_20241020",
      "last_message": "Explain Newton's first law",
      "last_response": "Newton's first law states...",
      "timestamp": "2024-10-20T10:30:00Z",
      "message_count": 5
    }
  ],
  "total_conversations": 15
}
```

### Subject File Management

#### GET /api/files/subjects/{subject_id}
Get files associated with a specific subject.

**Parameters:**
- `subject_id` (path): Subject identifier

**Response:**
```json
{
  "files": [
    {
      "file_id": "file_123",
      "filename": "physics_notes.pdf",
      "file_type": "subject_material",
      "assignment_id": null,
      "upload_timestamp": "2024-10-20T09:00:00Z",
      "processed_content": {
        "summary": "Document covers Newton's laws of motion...",
        "key_concepts": ["force", "acceleration", "inertia"],
        "subject_relevance": 0.95
      }
    }
  ],
  "total_files": 5
}
```

#### POST /api/files/subjects/{subject_id}
Upload and process a file for a specific subject.

**Parameters:**
- `subject_id` (path): Subject identifier

**Request Body:**
```json
{
  "file_key": "s3_key_from_presigned_upload",
  "file_name": "physics_chapter1.pdf",
  "assignment_id": "optional_assignment_id"
}
```

**Response:**
```json
{
  "file_id": "file_456",
  "status": "processed",
  "subject_context": {
    "subject_name": "Physics 101",
    "subject_id": "physics_101"
  },
  "processed_content": {
    "summary": "Chapter 1 introduces fundamental concepts...",
    "key_concepts": ["motion", "velocity", "acceleration"],
    "subject_relevance": 0.92
  }
}
```

### Assignment Quiz Generation

#### POST /api/quizzes/assignments/{assignment_id}/generate
Generate a quiz based on assignment content (teachers only).

**Parameters:**
- `assignment_id` (path): Assignment identifier

**Request Body:**
```json
{
  "quiz_config": {
    "num_questions": 5,
    "difficulty": "medium",
    "quiz_type": "multiple_choice",
    "focus_areas": ["newton_laws", "forces"],
    "due_date": "2024-10-25T23:59:59Z",
    "max_attempts": 3,
    "time_limit": 30,
    "show_correct_answers": true,
    "randomize_questions": false
  }
}
```

**Response:**
```json
{
  "quiz_id": "quiz_789",
  "assignment_id": "assign_123",
  "subject_id": "physics_101",
  "quiz_data": {
    "questions": [
      {
        "question_id": "q1",
        "question_text": "What is Newton's first law of motion?",
        "options": [
          {"option_id": "A", "text": "An object at rest stays at rest"},
          {"option_id": "B", "text": "Force equals mass times acceleration"},
          {"option_id": "C", "text": "For every action there is an equal reaction"},
          {"option_id": "D", "text": "Energy cannot be created or destroyed"}
        ],
        "correct_answer": "A",
        "explanation": "Newton's first law is about inertia...",
        "difficulty": "medium",
        "concept": "newton_laws"
      }
    ],
    "total_questions": 5,
    "estimated_time": 10
  },
  "status": "generated",
  "created_at": "2024-10-20T11:00:00Z"
}
```

#### GET /api/quizzes/assignments/{assignment_id}
Get quizzes for an assignment.

**Parameters:**
- `assignment_id` (path): Assignment identifier

**Response:**
```json
{
  "quizzes": [
    {
      "quiz_id": "quiz_789",
      "created_at": "2024-10-20T11:00:00Z",
      "total_questions": 5,
      "due_date": "2024-10-25T23:59:59Z",
      "max_attempts": 3,
      "status": "active"
    }
  ]
}
```

#### PUT /api/quizzes/{quiz_id}/settings
Update quiz settings (teachers only).

**Parameters:**
- `quiz_id` (path): Quiz identifier

**Request Body:**
```json
{
  "due_date": "2024-10-26T23:59:59Z",
  "max_attempts": 5,
  "time_limit": 45,
  "show_correct_answers": false
}
```

**Response:**
```json
{
  "status": "updated",
  "quiz_id": "quiz_789"
}
```

### Quiz Attempts (Students)

#### POST /api/quizzes/{quiz_id}/attempts
Start a new quiz attempt.

**Parameters:**
- `quiz_id` (path): Quiz identifier

**Response:**
```json
{
  "attempt_id": "attempt_456",
  "quiz_id": "quiz_789",
  "questions": [
    {
      "question_id": "q1",
      "question_text": "What is Newton's first law of motion?",
      "options": [
        {"option_id": "A", "text": "An object at rest stays at rest"},
        {"option_id": "B", "text": "Force equals mass times acceleration"},
        {"option_id": "C", "text": "For every action there is an equal reaction"},
        {"option_id": "D", "text": "Energy cannot be created or destroyed"}
      ]
    }
  ],
  "time_limit": 30,
  "total_questions": 5,
  "started_at": "2024-10-20T12:00:00Z"
}
```

#### POST /api/quizzes/attempts/{attempt_id}/submit
Submit quiz answers.

**Parameters:**
- `attempt_id` (path): Attempt identifier

**Request Body:**
```json
{
  "answers": {
    "q1": "A",
    "q2": "B",
    "q3": "C"
  }
}
```

**Response:**
```json
{
  "attempt_id": "attempt_456",
  "score": 8,
  "max_score": 10,
  "percentage": 80.0,
  "correct_answers": 4,
  "total_questions": 5,
  "feedback": [
    {
      "question_id": "q1",
      "question_text": "What is Newton's first law?",
      "student_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "explanation": "Correct! Newton's first law is about inertia."
    }
  ],
  "submitted_at": "2024-10-20T12:15:00Z"
}
```

### Teacher Dashboard

#### GET /api/dashboard/subjects/{subject_id}
Get comprehensive dashboard data for a subject (teachers only).

**Parameters:**
- `subject_id` (path): Subject identifier

**Response:**
```json
{
  "subject_info": {
    "subject_id": "physics_101",
    "name": "Physics 101",
    "description": "Introduction to Physics"
  },
  "students": {
    "total_enrolled": 25,
    "active_students": 20,
    "engagement_levels": {
      "high": 8,
      "medium": 12,
      "low": 5
    },
    "students_list": [
      {
        "student_id": "student_123",
        "name": "John Doe",
        "engagement_score": 0.85,
        "engagement_level": "high",
        "total_interactions": 45,
        "last_activity": "2024-10-20T10:30:00Z"
      }
    ]
  },
  "quiz_performance": {
    "total_quizzes": 3,
    "total_attempts": 75,
    "average_score": 78.5,
    "score_distribution": {
      "A": 15,
      "B": 25,
      "C": 20,
      "D": 10,
      "F": 5
    }
  },
  "file_metrics": {
    "total_files": 45,
    "assignment_files": 15,
    "student_files": 30,
    "recent_uploads": [
      {
        "filename": "homework1.pdf",
        "user_id": "student_123",
        "upload_timestamp": "2024-10-20T09:00:00Z"
      }
    ]
  },
  "learning_progress": {
    "overall_progress": 0.72,
    "students_on_track": 18,
    "students_struggling": 3,
    "concept_mastery": {
      "newton_laws": 0.85,
      "forces": 0.78,
      "momentum": 0.65
    }
  },
  "ai_insights": {
    "ai_generated_insights": "Students are performing well overall. Focus on momentum concepts as they show lower mastery levels...",
    "generated_at": "2024-10-20T12:00:00Z"
  }
}
```

#### GET /api/dashboard/overview
Get overview dashboard for all teacher's subjects.

**Response:**
```json
{
  "total_subjects": 3,
  "subjects": [
    {
      "subject_id": "physics_101",
      "subject_name": "Physics 101",
      "student_count": 25,
      "active_students": 20,
      "quiz_count": 3,
      "file_count": 45,
      "engagement_score": 0.78
    }
  ],
  "overall_stats": {
    "total_students": 75,
    "total_quizzes": 9,
    "total_files": 135,
    "avg_engagement": 0.76
  }
}
```

### Student Progress

#### GET /api/progress/subjects/{subject_id}
Get student's progress in a specific subject.

**Parameters:**
- `subject_id` (path): Subject identifier

**Response:**
```json
{
  "student_id": "student_123",
  "subject_info": {
    "subject_id": "physics_101",
    "name": "Physics 101"
  },
  "overall_progress": {
    "overall_score": 0.75,
    "level": "good",
    "components": {
      "analytics": 0.78,
      "quiz_performance": 0.80,
      "concept_mastery": 0.72,
      "engagement": 0.70
    }
  },
  "learning_analytics": {
    "overall_progress": 0.78,
    "engagement_score": 0.70,
    "learning_velocity": 0.05,
    "total_interactions": 45
  },
  "quiz_performance": {
    "total_attempts": 8,
    "average_score": 80.0,
    "highest_score": 95.0,
    "improvement_trend": "improving",
    "recent_attempts": [
      {
        "quiz_id": "quiz_789",
        "score": 8,
        "max_score": 10,
        "percentage": 80.0,
        "submitted_at": "2024-10-20T12:15:00Z"
      }
    ]
  },
  "concept_mastery": {
    "newton_laws": 0.85,
    "forces": 0.78,
    "momentum": 0.65,
    "energy": 0.70
  },
  "learning_trajectory": {
    "trend": "improving",
    "velocity": 0.05,
    "trajectory_points": [
      {
        "timestamp": "2024-10-15T00:00:00Z",
        "overall_progress": 0.65,
        "engagement_score": 0.60
      },
      {
        "timestamp": "2024-10-20T00:00:00Z",
        "overall_progress": 0.78,
        "engagement_score": 0.70
      }
    ]
  },
  "recommendations": {
    "ai_recommendations": "Focus on momentum concepts as they show lower mastery. Consider reviewing energy conservation principles...",
    "focus_areas": ["momentum", "energy"],
    "difficulty_adjustment": "maintain"
  }
}
```

#### GET /api/progress/subjects/{subject_id}/students
Get progress summary for all students in a subject (teachers only).

**Parameters:**
- `subject_id` (path): Subject identifier
- `student_id` (query, optional): Get specific student's progress

**Response:**
```json
{
  "subject_id": "physics_101",
  "subject_info": {
    "name": "Physics 101"
  },
  "overall_metrics": {
    "total_students": 25,
    "students_on_track": 18,
    "students_struggling": 3,
    "average_progress": 0.72,
    "concept_mastery_overview": {
      "newton_laws": 0.85,
      "forces": 0.78,
      "momentum": 0.65
    }
  },
  "student_progress": [
    {
      "student_id": "student_123",
      "name": "John Doe",
      "overall_progress": 0.78,
      "quiz_average": 80.0,
      "interaction_count": 45,
      "last_activity": "2024-10-20T10:30:00Z",
      "status": "on_track",
      "concept_mastery": {
        "newton_laws": 0.85,
        "forces": 0.78
      }
    }
  ]
}
```

## Error Responses

All endpoints return standard HTTP status codes and error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request parameters",
  "details": "Missing required field: message"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required",
  "details": "Invalid or missing JWT token"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions",
  "details": "Only teachers can generate assignment quizzes"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "details": "Subject with ID 'physics_101' not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "details": "Failed to process request"
}
```

## Rate Limiting

- Chat endpoints: 60 requests per minute per user
- File upload endpoints: 10 requests per minute per user
- Quiz generation: 5 requests per minute per teacher
- Dashboard endpoints: 30 requests per minute per user

## Data Models

### Subject Context
```json
{
  "subject_id": "string",
  "subject_name": "string",
  "description": "string",
  "recent_sessions": [
    {
      "session_id": "string",
      "title": "string",
      "date": "string",
      "topics": ["string"]
    }
  ],
  "recent_assignments": [
    {
      "assignment_id": "string",
      "title": "string",
      "due_date": "string",
      "type": "string"
    }
  ]
}
```

### Quiz Question
```json
{
  "question_id": "string",
  "question_text": "string",
  "options": [
    {
      "option_id": "string",
      "text": "string"
    }
  ],
  "correct_answer": "string",
  "explanation": "string",
  "difficulty": "easy|medium|hard",
  "concept": "string"
}
```

### Learning Analytics
```json
{
  "overall_progress": "number (0-1)",
  "concept_mastery": {
    "concept_name": "number (0-1)"
  },
  "engagement_score": "number (0-1)",
  "learning_velocity": "number",
  "total_interactions": "number",
  "difficulty_preference": "easy|medium|hard",
  "learning_style": "visual|auditory|kinesthetic|balanced"
}
```

## Integration Notes

### Bedrock Agent Integration
- All AI responses are generated using AWS Bedrock Agent
- Subject context is passed as session attributes
- Agent tools are used for specialized tasks (summarization, quiz generation)

### Supabase Integration
- Read-only access to existing subject, assignment, and user tables
- No schema modifications required
- Authentication handled via JWT token validation

### DynamoDB Storage
- Chat history stored in `lms-chat-history` table
- File metadata in `lms-user-files` table
- Quiz data in `lms-quizzes` and `lms-quiz-attempts` tables
- Learning analytics in `lms-learning-analytics` table

### S3 File Storage
- Original files stored in `raw-files/` prefix
- Processed content in `processed-chunks/` prefix
- Subject-specific organization with `subject_{subject_id}/` folders
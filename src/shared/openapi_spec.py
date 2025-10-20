"""
OpenAPI specification generator for LMS API
Generates comprehensive API documentation with examples
"""

import json
from typing import Dict, Any, List
from datetime import datetime


def generate_openapi_spec() -> Dict[str, Any]:
    """
    Generate complete OpenAPI 3.0 specification for LMS API
    
    Returns:
        OpenAPI specification dictionary
    """
    
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "LMS AI Backend API",
            "description": """
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
            """,
            "version": "1.0.0",
            "contact": {
                "name": "LMS API Support",
                "email": "support@lms-api.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "https://api.lms.example.com",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.lms.example.com",
                "description": "Staging server"
            },
            {
                "url": "http://localhost:3000",
                "description": "Local development server"
            }
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token for user authentication"
                }
            },
            "responses": {},
            "examples": {}
        },
        "security": [
            {"BearerAuth": []}
        ],
        "tags": [
            {
                "name": "Health",
                "description": "System health and status endpoints"
            },
            {
                "name": "Chat",
                "description": "AI chat and conversation management"
            },
            {
                "name": "Files",
                "description": "File upload and processing"
            },
            {
                "name": "Quiz",
                "description": "Quiz generation and submission"
            },
            {
                "name": "Voice",
                "description": "Voice interview functionality"
            },
            {
                "name": "Analytics",
                "description": "Learning analytics and progress tracking"
            }
        ]
    }
    
    # Add schemas
    spec["components"]["schemas"] = generate_schemas()
    
    # Add responses
    spec["components"]["responses"] = generate_responses()
    
    # Add examples
    spec["components"]["examples"] = generate_examples()
    
    # Add paths
    spec["paths"] = generate_paths()
    
    return spec


def generate_schemas() -> Dict[str, Any]:
    """Generate OpenAPI schemas from Pydantic models"""
    
    return {
        "ErrorDetail": {
            "type": "object",
            "required": ["code", "message", "timestamp"],
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Error code",
                    "example": "VALIDATION_ERROR"
                },
                "message": {
                    "type": "string",
                    "description": "User-friendly error message",
                    "example": "The provided data is invalid"
                },
                "details": {
                    "type": "object",
                    "description": "Additional error details",
                    "example": {"field": "email", "reason": "Invalid format"}
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Error timestamp",
                    "example": "2024-01-01T12:00:00Z"
                }
            }
        },
        "ErrorResponse": {
            "type": "object",
            "required": ["success", "error"],
            "properties": {
                "success": {
                    "type": "boolean",
                    "enum": [False],
                    "description": "Always false for error responses"
                },
                "error": {
                    "$ref": "#/components/schemas/ErrorDetail"
                }
            }
        },
        "ChatMessageRequest": {
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 5000,
                    "description": "Chat message content",
                    "example": "What is machine learning?"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Existing conversation ID",
                    "example": "conv-123e4567-e89b-12d3-a456-426614174000"
                },
                "subject_id": {
                    "type": "string",
                    "description": "Subject context for the chat",
                    "example": "cs101"
                },
                "user_id": {
                    "type": "string",
                    "description": "User ID (for testing without auth)",
                    "example": "user-123"
                }
            }
        },
        "Citation": {
            "type": "object",
            "required": ["source"],
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source document name",
                    "example": "machine_learning_basics.pdf"
                },
                "chunk_index": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Chunk index in document",
                    "example": 2
                },
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Relevance score",
                    "example": 0.95
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Page number if available",
                    "example": 15
                }
            }
        },
        "ChatMessageResponse": {
            "type": "object",
            "required": ["success", "response", "conversation_id", "timestamp"],
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the request was successful",
                    "example": True
                },
                "response": {
                    "type": "string",
                    "description": "AI response content",
                    "example": "Machine learning is a subset of artificial intelligence..."
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID",
                    "example": "conv-123e4567-e89b-12d3-a456-426614174000"
                },
                "citations": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/Citation"},
                    "description": "Source citations"
                },
                "rag_documents_used": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Number of RAG documents used",
                    "example": 3
                },
                "rag_enhanced": {
                    "type": "boolean",
                    "description": "Whether RAG was used",
                    "example": True
                },
                "bedrock_agent_used": {
                    "type": "boolean",
                    "description": "Whether Bedrock Agent was used",
                    "example": True
                },
                "subject_context": {
                    "type": "string",
                    "description": "Subject context",
                    "example": "cs101"
                },
                "agent_metadata": {
                    "type": "object",
                    "description": "Agent metadata"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Response timestamp"
                }
            }
        },
        "FileUploadRequest": {
            "type": "object",
            "required": ["filename", "file_size"],
            "properties": {
                "filename": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 255,
                    "description": "Original filename",
                    "example": "lecture_notes.pdf"
                },
                "file_size": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10485760,
                    "description": "File size in bytes",
                    "example": 2048576
                },
                "subject_id": {
                    "type": "string",
                    "description": "Associated subject ID",
                    "example": "physics101"
                },
                "user_id": {
                    "type": "string",
                    "description": "User ID (for testing without auth)",
                    "example": "user-123"
                }
            }
        },
        "FileUploadResponse": {
            "type": "object",
            "required": ["success", "file_id", "upload_url", "status", "process_url"],
            "properties": {
                "success": {
                    "type": "boolean",
                    "example": True
                },
                "file_id": {
                    "type": "string",
                    "description": "Unique file ID",
                    "example": "file-123e4567-e89b-12d3-a456-426614174000"
                },
                "upload_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Presigned URL for file upload",
                    "example": "https://s3.amazonaws.com/bucket/key?signature=..."
                },
                "status": {
                    "type": "string",
                    "description": "Upload status",
                    "example": "ready_for_upload"
                },
                "process_url": {
                    "type": "string",
                    "description": "URL to trigger processing",
                    "example": "/api/files/process"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time"
                }
            }
        },
        "HealthResponse": {
            "type": "object",
            "required": ["success", "status", "services", "timestamp"],
            "properties": {
                "success": {
                    "type": "boolean",
                    "example": True
                },
                "status": {
                    "type": "string",
                    "enum": ["healthy", "degraded", "unhealthy"],
                    "description": "Overall system status",
                    "example": "healthy"
                },
                "services": {
                    "type": "object",
                    "description": "Individual service statuses",
                    "example": {
                        "dynamodb": "healthy",
                        "s3": "healthy",
                        "bedrock": "healthy",
                        "pinecone": "configured"
                    }
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time"
                }
            }
        }
    }


def generate_responses() -> Dict[str, Any]:
    """Generate common response definitions"""
    
    return {
        "BadRequest": {
            "description": "Bad Request - Invalid input data",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "The provided data is invalid",
                            "details": {"field": "message", "reason": "Required field missing"},
                            "timestamp": "2024-01-01T12:00:00Z"
                        }
                    }
                }
            }
        },
        "Unauthorized": {
            "description": "Unauthorized - Authentication required",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Please log in to access this resource",
                            "details": {},
                            "timestamp": "2024-01-01T12:00:00Z"
                        }
                    }
                }
            }
        },
        "Forbidden": {
            "description": "Forbidden - Access denied",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": {
                            "code": "FORBIDDEN",
                            "message": "You don't have permission to access this resource",
                            "details": {},
                            "timestamp": "2024-01-01T12:00:00Z"
                        }
                    }
                }
            }
        },
        "NotFound": {
            "description": "Not Found - Resource not found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": {
                            "code": "RESOURCE_NOT_FOUND",
                            "message": "The requested resource could not be found",
                            "details": {"resource_type": "conversation", "resource_id": "conv-123"},
                            "timestamp": "2024-01-01T12:00:00Z"
                        }
                    }
                }
            }
        },
        "InternalServerError": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected error occurred. Please try again.",
                            "details": {},
                            "timestamp": "2024-01-01T12:00:00Z"
                        }
                    }
                }
            }
        },
        "ServiceUnavailable": {
            "description": "Service Unavailable - External service error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "success": False,
                        "error": {
                            "code": "SERVICE_UNAVAILABLE",
                            "message": "A service is temporarily unavailable. Please try again later.",
                            "details": {"service": "bedrock"},
                            "timestamp": "2024-01-01T12:00:00Z"
                        }
                    }
                }
            }
        }
    }


def generate_examples() -> Dict[str, Any]:
    """Generate example requests and responses"""
    
    return {
        "ChatMessageExample": {
            "summary": "Basic chat message",
            "value": {
                "message": "What is machine learning?",
                "subject_id": "cs101"
            }
        },
        "ChatWithDocumentExample": {
            "summary": "Chat about uploaded document",
            "value": {
                "message": "Summarize the key points from my physics notes",
                "conversation_id": "conv-123e4567-e89b-12d3-a456-426614174000"
            }
        },
        "FileUploadExample": {
            "summary": "Upload PDF file",
            "value": {
                "filename": "machine_learning_lecture.pdf",
                "file_size": 2048576,
                "subject_id": "cs101"
            }
        },
        "QuizGenerationExample": {
            "summary": "Generate quiz from documents",
            "value": {
                "subject_id": "physics101",
                "num_questions": 5,
                "difficulty": "intermediate"
            }
        }
    }


def generate_paths() -> Dict[str, Any]:
    """Generate API path definitions"""
    
    return {
        "/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Health check",
                "description": "Check the health status of the API and its dependencies",
                "operationId": "getHealth",
                "responses": {
                    "200": {
                        "description": "System is healthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthResponse"}
                            }
                        }
                    },
                    "503": {
                        "description": "System is degraded or unhealthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/chat": {
            "post": {
                "tags": ["Chat"],
                "summary": "Send chat message",
                "description": "Send a message to the AI assistant and get a response with RAG enhancement",
                "operationId": "sendChatMessage",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ChatMessageRequest"},
                            "examples": {
                                "basic": {"$ref": "#/components/examples/ChatMessageExample"},
                                "document": {"$ref": "#/components/examples/ChatWithDocumentExample"}
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Chat response generated successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatMessageResponse"}
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "500": {"$ref": "#/components/responses/InternalServerError"},
                    "503": {"$ref": "#/components/responses/ServiceUnavailable"}
                }
            }
        },
        "/api/chat/history": {
            "get": {
                "tags": ["Chat"],
                "summary": "Get conversation history",
                "description": "Retrieve conversation history for a user or specific conversation",
                "operationId": "getChatHistory",
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "query",
                        "description": "User ID (for testing without auth)",
                        "schema": {"type": "string"},
                        "example": "user-123"
                    },
                    {
                        "name": "conversation_id",
                        "in": "query",
                        "description": "Specific conversation ID",
                        "schema": {"type": "string"},
                        "example": "conv-123e4567-e89b-12d3-a456-426614174000"
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of messages to return",
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Conversation history retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "conversation_id": {"type": "string"},
                                        "messages": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "message_id": {"type": "string"},
                                                    "message_type": {"type": "string", "enum": ["user", "assistant"]},
                                                    "content": {"type": "string"},
                                                    "timestamp": {"type": "integer"},
                                                    "citations": {"type": "array", "items": {"$ref": "#/components/schemas/Citation"}}
                                                }
                                            }
                                        },
                                        "total_messages": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        },
        "/api/files": {
            "post": {
                "tags": ["Files"],
                "summary": "Upload file",
                "description": "Generate presigned URL for file upload and create file metadata",
                "operationId": "uploadFile",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/FileUploadRequest"},
                            "examples": {
                                "pdf": {"$ref": "#/components/examples/FileUploadExample"}
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Upload URL generated successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/FileUploadResponse"}
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            },
            "get": {
                "tags": ["Files"],
                "summary": "Get user files",
                "description": "Retrieve list of files uploaded by the user",
                "operationId": "getUserFiles",
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "query",
                        "description": "User ID (for testing without auth)",
                        "schema": {"type": "string"},
                        "example": "user-123"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Files retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "files": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "file_id": {"type": "string"},
                                                    "filename": {"type": "string"},
                                                    "file_size": {"type": "integer"},
                                                    "status": {"type": "string"},
                                                    "processing_status": {"type": "string"},
                                                    "upload_timestamp": {"type": "string"}
                                                }
                                            }
                                        },
                                        "total": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        },
        "/api/files/process": {
            "post": {
                "tags": ["Files"],
                "summary": "Process uploaded file",
                "description": "Process uploaded file for RAG with text extraction and vector storage",
                "operationId": "processFile",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["file_id"],
                                "properties": {
                                    "file_id": {
                                        "type": "string",
                                        "description": "File ID to process",
                                        "example": "file-123e4567-e89b-12d3-a456-426614174000"
                                    },
                                    "user_id": {
                                        "type": "string",
                                        "description": "User ID (for testing without auth)",
                                        "example": "user-123"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "File processed successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "file_id": {"type": "string"},
                                        "status": {"type": "string"},
                                        "chunks_created": {"type": "integer"},
                                        "vectors_stored": {"type": "integer"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/BadRequest"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "422": {
                        "description": "Processing failed",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {"$ref": "#/components/responses/InternalServerError"}
                }
            }
        }
    }


def save_openapi_spec(output_file: str = "openapi.json") -> None:
    """
    Save OpenAPI specification to file
    
    Args:
        output_file: Output file path
    """
    
    spec = generate_openapi_spec()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"OpenAPI specification saved to {output_file}")


if __name__ == "__main__":
    # Generate and save OpenAPI spec
    save_openapi_spec("docs/openapi.json")
    
    # Also save as YAML for better readability
    try:
        import yaml
        spec = generate_openapi_spec()
        with open("docs/openapi.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
        print("OpenAPI specification also saved as YAML")
    except ImportError:
        print("PyYAML not installed, skipping YAML output")
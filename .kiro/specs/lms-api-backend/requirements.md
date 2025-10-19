# LMS API Backend Requirements

## Introduction

This document outlines the requirements for a simple LMS (Learning Management System) API backend that integrates with an existing React frontend and Supabase Google authentication. The backend will provide core LMS functionality including file processing, AI-powered chat, quiz generation, and real-time voice interviews using AWS Bedrock services.

## Technical Architecture Notes

### Real-time Voice Interview Implementation
The voice interview system will work as follows:

1. **Client Side (React)**: 
   - Captures audio using Web Audio API
   - Establishes WebSocket connection to `/api/interview/ws`
   - Streams audio chunks in real-time as base64 encoded data
   - Handles text-to-speech for AI responses using browser APIs

2. **Server Side (API)**:
   - Maintains WebSocket connections for real-time audio streaming
   - Uses AWS Transcribe Streaming API for real-time speech-to-text
   - Processes transcribed text through Bedrock Agent for intelligent responses
   - Returns text responses via WebSocket for client-side speech synthesis

3. **Data Flow**:
   ```
   React App → WebSocket → API Server → AWS Transcribe → Bedrock Agent → Response → WebSocket → React App → Text-to-Speech
   ```

This approach keeps the API stateless while enabling real-time voice interaction through WebSocket connections.

## Requirements

### Requirement 1: File Upload and Processing API

**User Story:** As a student or teacher, I want to upload educational documents through the API, so that the system can process and make them available for AI-powered interactions.

#### Acceptance Criteria

1. WHEN a user uploads a file via POST /api/files THEN the system SHALL accept PDF, DOCX, and TXT files up to 10MB
2. WHEN a file is uploaded THEN the system SHALL extract text content and store it in AWS S3
3. WHEN text extraction is complete THEN the system SHALL index the content in AWS Bedrock Knowledge Base
4. WHEN file processing fails THEN the system SHALL return appropriate error messages with status codes
5. WHEN a user requests GET /api/files THEN the system SHALL return a list of their uploaded files with metadata

### Requirement 2: AI Chat API

**User Story:** As a user, I want to chat with an AI about my uploaded documents, so that I can get answers and insights from my educational materials.

#### Acceptance Criteria

1. WHEN a user sends POST /api/chat with a message THEN the system SHALL use AWS Bedrock Agent to generate responses
2. WHEN generating responses THEN the system SHALL reference the user's uploaded documents from the Knowledge Base
3. WHEN a chat response is generated THEN the system SHALL include source citations from relevant documents
4. WHEN a user requests GET /api/chat/history THEN the system SHALL return their conversation history
5. WHEN the AI cannot find relevant information THEN the system SHALL provide a helpful fallback response

### Requirement 3: Quiz Generation API

**User Story:** As a teacher or student, I want to generate quizzes from my uploaded documents, so that I can test knowledge and understanding of the material.

#### Acceptance Criteria

1. WHEN a user requests POST /api/quiz/generate with document references THEN the system SHALL create multiple-choice questions using AWS Bedrock
2. WHEN generating quizzes THEN the system SHALL create 5-10 questions with 4 answer choices each
3. WHEN a quiz is generated THEN the system SHALL store it with a unique ID for later retrieval
4. WHEN a user submits POST /api/quiz/submit with answers THEN the system SHALL score the quiz and provide feedback
5. WHEN a user requests GET /api/quiz/results THEN the system SHALL return their quiz history and scores

### Requirement 4: User Data Management API

**User Story:** As a user authenticated through Supabase, I want my data to be properly managed and isolated, so that my files and conversations remain private and secure.

#### Acceptance Criteria

1. WHEN a request includes a valid Supabase JWT token THEN the system SHALL authenticate the user
2. WHEN accessing any resource THEN the system SHALL ensure users can only access their own data
3. WHEN storing user data THEN the system SHALL use the Supabase user ID as the primary identifier
4. WHEN a user is not authenticated THEN the system SHALL return 401 Unauthorized
5. WHEN a user accesses unauthorized resources THEN the system SHALL return 403 Forbidden

### Requirement 5: Group Chat API

**User Story:** As a student or teacher, I want to participate in group chats with AI assistance, so that I can collaborate with others and get AI insights during group discussions.

#### Acceptance Criteria

1. WHEN a user creates POST /api/groups THEN the system SHALL create a new group chat with the user as admin
2. WHEN a user joins POST /api/groups/{id}/join THEN the system SHALL add them to the group if they have permission
3. WHEN a user sends POST /api/groups/{id}/messages THEN the system SHALL broadcast the message to all group members
4. WHEN AI is mentioned in group chat THEN the system SHALL provide contextual responses using Bedrock Agent
5. WHEN a user requests GET /api/groups/{id}/messages THEN the system SHALL return the group conversation history

### Requirement 6: Learning Graph API

**User Story:** As a user, I want to visualize my learning progress and knowledge connections, so that I can understand my educational journey and identify knowledge gaps.

#### Acceptance Criteria

1. WHEN a user interacts with content THEN the system SHALL track learning activities and knowledge nodes
2. WHEN generating learning graphs THEN the system SHALL create connections between related topics and documents
3. WHEN a user requests GET /api/learning-graph THEN the system SHALL return their personalized learning graph data
4. WHEN new content is processed THEN the system SHALL update the learning graph with new knowledge connections
5. WHEN displaying progress THEN the system SHALL show mastery levels and recommended learning paths

### Requirement 7: Voice Interview API

**User Story:** As a student, I want to participate in AI-conducted voice interviews, so that I can practice speaking skills and receive feedback on my responses.

#### Acceptance Criteria

1. WHEN a user starts POST /api/interview/start THEN the system SHALL create a WebSocket connection for real-time audio streaming
2. WHEN receiving audio chunks via WebSocket THEN the system SHALL use AWS Transcribe streaming API for real-time speech-to-text
3. WHEN transcription is complete THEN the system SHALL send the text to Bedrock Agent for response generation
4. WHEN AI generates a response THEN the system SHALL send text back to client for text-to-speech conversion (client-side)
5. WHEN an interview session ends THEN the system SHALL close WebSocket and store complete transcript with performance analysis

### Requirement 7.1: Real-time Audio Processing

**User Story:** As a user, I want real-time voice interaction during interviews, so that the conversation feels natural and responsive.

#### Acceptance Criteria

1. WHEN audio is streamed THEN the system SHALL process audio chunks in real-time with <2 second latency
2. WHEN using WebSocket connection THEN the system SHALL handle audio data in base64 encoded chunks
3. WHEN transcription is partial THEN the system SHALL provide interim results to show processing progress
4. WHEN connection drops THEN the system SHALL attempt reconnection and resume from last processed audio
5. WHEN audio quality is poor THEN the system SHALL request user to repeat or improve audio input

### Requirement 8: Health and Status API

**User Story:** As a system administrator, I want to monitor the API health and AWS service connectivity, so that I can ensure the system is functioning properly.

#### Acceptance Criteria

1. WHEN requesting GET /api/health THEN the system SHALL return API status and AWS service connectivity
2. WHEN AWS services are unavailable THEN the system SHALL report degraded status
3. WHEN all services are operational THEN the system SHALL return 200 OK with service status details
4. WHEN checking service health THEN the system SHALL verify Bedrock, S3, DynamoDB, and Transcribe connectivity
5. WHEN health checks fail THEN the system SHALL log errors for debugging
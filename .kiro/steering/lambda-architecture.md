# LMS Lambda Architecture - Serverless Backend

## Pure Lambda Serverless Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │    File     │ │   AI Chat   │ │    Quiz     │ │ Voice  ││
│  │   Upload    │ │ Interface   │ │ Interface   │ │Interview││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Lambda Functions Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │    File     │ │   AI Chat   │ │    Quiz     │ │ Voice  ││
│  │ Processing  │ │   Lambda    │ │  Generator  │ │Interview││
│  │   Lambda    │ │             │ │   Lambda    │ │ Lambda ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Services Layer                             │
│  S3 Storage   DynamoDB    Bedrock Agents    Transcribe     │
│  Pinecone     Knowledge   Multiple Agents   Real-time      │
│  Vectors      Base        Specialized AI    Processing     │
└─────────────────────────────────────────────────────────────┘
```

## Serverless Lambda Strategy
- **Individual Lambda Functions**: Each service as separate Lambda function
- **API Gateway Integration**: RESTful API endpoints routing to Lambda
- **Event-Driven Architecture**: S3 triggers, DynamoDB streams, SQS queues
- **Stateless Design**: All state managed in AWS services (DynamoDB, S3)

## Key Technology Stack
- **Frontend**: React application with existing UI components
- **API Layer**: AWS API Gateway with Lambda integration
- **Authentication**: Supabase Auth with Lambda authorizer
- **Database**: DynamoDB for sessions, Supabase for persistent data
- **Intelligence**: Multiple specialized Bedrock Agents
- **Storage**: S3 for files, Pinecone for vectors
- **Real-time**: WebSocket API Gateway for voice interviews
- **Deployment**: AWS SAM for Infrastructure as Code

## Lambda Functions Architecture

### Core Lambda Functions
1. **File Processing Lambda** (`src/file_processing/file_handler.py`)
   - File upload presigned URLs
   - Text extraction and chunking
   - Vector embedding generation
   - Pinecone storage integration

2. **AI Chat Lambda** (`src/chat/chat_handler.py`)
   - Conversation management
   - RAG-enhanced responses
   - Bedrock Agent integration
   - Chat history persistence

3. **Quiz Generator Lambda** (`src/quiz_generator/quiz_handler.py`)
   - AI-powered quiz generation
   - Question validation
   - Scoring and analytics
   - Progress tracking

4. **Voice Interview Lambda** (`src/voice_interview/interview_handler.py`)
   - Real-time audio processing
   - Transcription via AWS Transcribe
   - AI-powered interview analysis
   - Performance feedback

5. **Auth Lambda** (`src/auth/authorizer.py`)
   - Supabase JWT validation
   - User authorization
   - Role-based access control

## Security Requirements
- Lambda authorizer for all API endpoints
- Supabase JWT token validation
- IAM least privilege policies for each Lambda
- S3 server-side encryption (SSE-S3)
- DynamoDB encryption at rest
- API Gateway CORS configuration
- Secrets Manager for API keys and credentials
- CloudWatch logging and monitoring

## Deployment Strategy
- **AWS SAM**: Infrastructure as Code deployment
- **Individual Lambda packages**: Separate deployment units
- **Environment-based**: dev/staging/prod separation
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring**: CloudWatch dashboards and alarms
- **Cost Optimization**: Pay-per-request serverless model
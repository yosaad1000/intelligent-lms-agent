# LMS Bedrock AgentCore Architecture - Managed AI Backend

## Bedrock AgentCore + Lambda Hybrid Architecture
```
┌─────────────────────────────────────────────────────────────┐
│              External Systems (Optional)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │   Mobile    │ │    Web      │ │   Desktop   │ │  API   ││
│  │    Apps     │ │    Apps     │ │    Apps     │ │Clients ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              API Gateway (Optional)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Bedrock AgentCore (Managed)                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  LMS Learning Assistant Agent (Production Alias)       ││
│  │  • Knowledge Base Integration                           ││
│  │  • Action Groups (Custom Tools)                        ││
│  │  • Bedrock Flows (Complex Workflows)                   ││
│  │  • Built-in Memory & Session Management                ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            Lambda Action Groups (Custom Tools)             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │ Document    │ │ Quiz        │ │ Analytics   │ │ Voice  ││
│  │ Processor   │ │ Generator   │ │ Tracker     │ │Processor││
│  │ (Textract)  │ │ (Bedrock)   │ │ (DynamoDB)  │ │(Transcr)││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Managed Services Layer                     │
│  S3 Storage   DynamoDB    Bedrock Models    OpenSearch     │
│  Knowledge    Session     Claude/Nova       Serverless     │
│  Base         Memory      Foundation LLMs   Vector Store   │
└─────────────────────────────────────────────────────────────┘
```

## Bedrock AgentCore Strategy
- **Managed Agent Deployment**: Production-grade agents on AWS AgentCore
- **Lambda Action Groups**: Custom tools as Lambda functions called by agent
- **Knowledge Base Integration**: Managed RAG with S3 data sources
- **Bedrock Flows**: Visual workflow orchestration for complex logic
- **Built-in Session Management**: No custom memory implementation needed

## Key Technology Stack
- **Frontend**: React application with Bedrock Agent integration
- **API Layer**: AWS API Gateway with Bedrock Agent Runtime
- **AI Core**: Amazon Bedrock AgentCore (fully managed)
- **Authentication**: AWS Cognito with IAM roles
- **Database**: DynamoDB for user data, built-in agent memory
- **Intelligence**: Single LMS Agent with multiple action groups
- **Storage**: S3 for files, Bedrock Knowledge Base for vectors
- **Workflows**: Bedrock Flows for complex conditional logic
- **Deployment**: AWS SAM + Bedrock Agent deployment

## Bedrock Agent + Lambda Action Groups Architecture

### Core Bedrock Agent
**LMS Learning Assistant Agent** (Deployed on AgentCore)
- **Foundation Model**: Amazon Nova Micro (development), Nova Pro (production)
- **Knowledge Base**: S3-backed document repository with vector search
- **Session Management**: Built-in conversation memory and context
- **Production Alias**: Stable endpoint for frontend integration

### Lambda Action Groups (Custom Tools)
1. **Document Processor Action Group** (`src/actions/document_processor.py`)
   - Textract integration for advanced document parsing
   - Comprehend analysis for entity extraction
   - S3 upload handling and metadata extraction
   - Knowledge Base data source synchronization

2. **Quiz Generator Action Group** (`src/actions/quiz_generator.py`)
   - Content-based quiz generation using Bedrock
   - Question difficulty adjustment
   - Answer validation and scoring
   - Progress analytics integration

3. **Analytics Tracker Action Group** (`src/actions/analytics_tracker.py`)
   - Learning progress monitoring
   - Performance metrics calculation
   - Recommendation engine integration
   - DynamoDB data persistence

4. **Voice Processor Action Group** (`src/actions/voice_processor.py`)
   - AWS Transcribe integration
   - Real-time audio processing
   - Interview analysis and feedback
   - Multi-language support

5. **API Gateway Proxy** (`src/api/agent_proxy.py`)
   - Bedrock Agent Runtime integration
   - Authentication and authorization
   - Request/response formatting
   - Error handling and logging

## Security Requirements
- Lambda authorizer for all API endpoints
- Supabase JWT token validation (development), AWS Cognito (production)
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
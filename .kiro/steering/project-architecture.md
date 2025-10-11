# Intelligent LMS Architecture Guidelines

## MVP Microservices Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Gradio Frontend                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │    Auth     │ │File Processor│ │  AI Chat    │ │  Quiz  ││
│  │  Interface  │ │  Interface   │ │ Interface   │ │Interface││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    Auth     │ │    File     │ │   AI Chat   │ │    Quiz     │
│Microservice │ │ Processor   │ │Microservice │ │ Generator   │
│             │ │Microservice │ │             │ │Microservice │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Services Layer                       │
│  Cognito     S3 + Bedrock KB    Bedrock Agent    Bedrock   │
└─────────────────────────────────────────────────────────────┘
```

## Microservices Strategy
- **4 Independent Services**: Auth, File Processing, AI Chat, Quiz Generation
- **Gradio Integration**: Each service has Gradio interface for rapid testing
- **Parallel Development**: Team members can work on different services
- **Fast Merge**: Combine into single Gradio app for MVP demo

## Key Technology Stack
- **Frontend**: Gradio (Python-based web interface per service)
- **Microservices**: Independent Python modules with clear APIs
- **Intelligence**: Bedrock Agent with Nova LLM + Knowledge Base
- **Storage**: S3 (files), DynamoDB (user data), Cognito (auth)
- **Integration**: Single main app combining all microservices
- **Deployment**: Can run as single app or separate services

## Security Requirements
- AWS Cognito with MFA optional
- IAM least privilege policies
- S3 server-side encryption (SSE-S3)
- DynamoDB encryption at rest
- API Gateway rate limiting and CORS
- Secrets Manager for API keys
- CloudWatch logging (no PII)

## Development Approach
- Incremental deployment (9 steps)
- Build → Test → Improve → Next Step
- Each step fully tested before proceeding
- Security-first implementation
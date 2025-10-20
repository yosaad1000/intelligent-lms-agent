# Unified LMS Architecture - Resolved Contradictions

## Architecture Overview
This document resolves all contradictions between steering documents and provides a unified approach for the LMS AI Agent system.

## Core Technology Stack (FINAL)

### AI Agent Framework
- **Primary Platform**: Amazon Bedrock AgentCore (fully managed)
- **Workflow Engine**: LangGraph + LangChain for agent logic
- **Foundation Model**: Amazon Nova Micro (development), Nova Pro (production)
- **Deployment**: LangGraph workflows packaged as Lambda action groups on Bedrock AgentCore

### Authentication & Authorization (SIMPLIFIED)
- **Authentication**: Supabase Auth (consistent across all environments)
- **Authorization**: JWT tokens with IAM role-based authorization
- **API Security**: Lambda authorizers for endpoint protection

### Data & Storage
- **Vector Storage**: Bedrock Knowledge Base with OpenSearch Serverless
- **Document Storage**: S3 with intelligent tiering
- **User Data**: DynamoDB with encryption at rest
- **Session Memory**: Built-in Bedrock Agent memory + DynamoDB backup

### Workflow Architecture (UNIFIED)
```
User Request
    ↓
Bedrock Agent (Nova Micro/Pro)
    ↓
LangGraph Action Group (Lambda)
    ↓
Intent Detection → Conditional Routing → Processing Nodes
    ↓
Response Synthesis → Citations → Final Response
```

## Implementation Phases (CLARIFIED)

### Phase 1: Foundation (Tasks 1-3)
- ✅ Bedrock Agent creation with Nova Micro model
- ✅ Knowledge Base setup with S3 data source
- ✅ Basic LangGraph workflow implementation

### Phase 2: Core Workflows (Tasks 4-6)
- 🔄 **Current Task**: LangGraph action group deployment
- Document processing with Textract + Comprehend
- RAG retrieval with Knowledge Base integration

### Phase 3: Advanced Features (Tasks 7-10)
- Quiz generation workflows
- Learning analytics tracking
- Voice processing integration
- Multi-language support

### Phase 4: Production Deployment (Tasks 11-14)
- Production alias creation
- Cognito migration (if needed)
- Performance optimization
- Monitoring and alerting

## Resolved Contradictions

### 1. Authentication Strategy
**BEFORE**: Conflicting between Cognito vs Supabase
**AFTER**: 
- Unified: Supabase Auth for all environments (simple and effective)
- No migration needed - consistent authentication layer

### 2. Model Selection
**BEFORE**: Conflicting between Claude vs Nova models
**AFTER**: 
- Development: Nova Micro (cost-effective, current)
- Production: Nova Pro (performance optimized)
- Consistent Nova family usage

### 3. Workflow Framework
**BEFORE**: Conflicting between Bedrock Flows vs LangGraph
**AFTER**: 
- Primary: LangGraph for complex workflows
- Deployment: LangGraph packaged as Bedrock Agent action groups
- Bedrock Flows reserved for simple conditional logic only

### 4. Architecture Approach
**BEFORE**: Mixed serverless vs managed service approaches
**AFTER**: 
- Hybrid: LangGraph flexibility + Bedrock AgentCore reliability
- Lambda action groups for custom logic
- Bedrock AgentCore for managed infrastructure

## Development Guidelines (UNIFIED)

### Code Organization
```
src/
├── bedrock_agent/          # Agent deployment and management
├── chat/                   # LangGraph workflow implementations
├── shared/                 # Common utilities and services
├── file_processing/        # Document processing workflows
└── auth/                   # Authentication abstraction layer
```

### Model Configuration
```python
# Development
BEDROCK_MODEL_ID = "amazon.nova-micro-v1:0"

# Production
BEDROCK_MODEL_ID = "amazon.nova-pro-v1:0"
```

### Authentication Abstraction
```python
class AuthService:
    def __init__(self):
        self.provider = "supabase" if DEVELOPMENT else "cognito"
    
    def validate_token(self, token):
        if self.provider == "supabase":
            return self.validate_supabase_token(token)
        else:
            return self.validate_cognito_token(token)
```

## Testing Strategy (COMPREHENSIVE)

### Unit Tests
- LangGraph workflow nodes
- Lambda action group functions
- Authentication service abstraction

### Integration Tests
- Bedrock Agent + LangGraph workflows
- Knowledge Base retrieval accuracy
- End-to-end user scenarios

### Performance Tests
- Agent response times
- Concurrent user handling
- Cost optimization validation

## Deployment Standards (FINAL)

### Infrastructure as Code
- **Primary**: AWS SAM templates
- **Alternative**: AWS CDK for complex scenarios
- **Version Control**: Git-based deployment pipelines

### Environment Management
- **Development**: Single-stack deployment
- **Staging**: Production-like with test data
- **Production**: Multi-AZ, auto-scaling configuration

### Monitoring & Observability
- **Agent Metrics**: Bedrock AgentCore built-in monitoring
- **Custom Metrics**: CloudWatch dashboards
- **Tracing**: X-Ray for request flow analysis
- **Logging**: Structured JSON logs in CloudWatch

## Migration Path

### Current State (Task 5) - COMPLETED ✅
- ✅ Supabase authentication
- ✅ Nova Micro model  
- ✅ Bedrock Agent deployed (ID: ZTBBVSC6Y1)
- ✅ Agent tested and working (100% success rate)
- ✅ Simple architecture with minimal Lambda (when needed)

### Production Readiness
1. **Model Upgrade**: Nova Micro → Nova Pro (when needed)
2. **Security Hardening**: IAM policies, encryption
3. **Performance Optimization**: Caching, connection pooling
4. **Monitoring Enhancement**: Advanced CloudWatch dashboards

## Success Metrics

### Technical Metrics
- Agent response time < 3 seconds
- 99.9% availability
- Cost per interaction < $0.01

### Functional Metrics
- Intent detection accuracy > 95%
- User satisfaction score > 4.5/5
- Knowledge retrieval relevance > 90%

This unified architecture resolves all contradictions and provides a clear path forward for development and production deployment.
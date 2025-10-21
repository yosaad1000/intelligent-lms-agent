# Design Document

## Overview

The Hybrid Agent Testing system provides a streamlined approach for testing AWS Bedrock Agent functionality in a local development environment. The design focuses on minimal setup, maximum testing capability, and zero risk to production systems by using mock authentication with direct AWS service integration.

## Architecture

### High-Level Architecture

```
Local Frontend (React)
├── Mock Authentication Layer
├── Direct Agent Service (New)
├── Existing UI Components (Unchanged)
└── AWS SDK Integration

Direct Agent Service
├── AWS Bedrock Agent Runtime
├── Session Management
├── Error Handling
└── Response Formatting

AWS Services (Production)
├── Bedrock Agent (ZTBBVSC6Y1)
├── Lambda Functions (Deployed)
├── S3 Document Storage
└── DynamoDB (Session Data)
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Mock Auth     │  │  Existing UI    │  │ Agent Test  │ │
│  │   Context       │  │  Components     │  │ Interface   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│           │                     │                   │       │
│           └─────────────────────┼───────────────────┘       │
│                                 │                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            Direct Agent Service                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │   Session   │  │   Request   │  │    Response     │ │ │
│  │  │  Manager    │  │  Handler    │  │   Formatter     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS SDK                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Bedrock       │  │      S3         │  │  DynamoDB   │ │
│  │   Agent         │  │   Document      │  │   Session   │ │
│  │   Runtime       │  │   Storage       │  │   Storage   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Bedrock Agent (Production)                 │
│                    Agent ID: ZTBBVSC6Y1                     │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Direct Agent Service

**Purpose**: Provides simplified, direct access to AWS Bedrock Agent without complex authentication flows.

**Interface**:
```typescript
interface DirectAgentService {
  // Core agent communication
  sendMessage(message: string, sessionId?: string): Promise<AgentResponse>;
  
  // Document processing
  analyzeDocument(documentUrl: string, query: string): Promise<DocumentAnalysis>;
  
  // Quiz generation
  generateQuiz(content: string, options: QuizOptions): Promise<Quiz>;
  
  // Interview simulation
  startInterview(topic: string): Promise<InterviewSession>;
  conductInterview(sessionId: string, response: string): Promise<InterviewFeedback>;
  
  // Session management
  createSession(): string;
  getSession(sessionId: string): AgentSession;
  clearSession(sessionId: string): void;
}
```

**Key Features**:
- Direct AWS SDK integration
- Automatic session management
- Error handling and retry logic
- Response formatting for UI consumption
- Logging for debugging

### Agent Testing Interface

**Purpose**: Provides dedicated UI components for testing agent functionality.

**Components**:
1. **AgentTester**: Main testing interface with quick test buttons
2. **ChatTester**: Dedicated chat testing with conversation history
3. **DocumentTester**: Document upload and analysis testing
4. **QuizTester**: Quiz generation and validation testing
5. **InterviewTester**: Interview simulation testing

### Environment Configuration

**Testing Mode Detection**:
```typescript
const isAgentTestingMode = 
  import.meta.env.VITE_USE_MOCK_AUTH === 'true' && 
  import.meta.env.VITE_USE_MOCK_AGENT === 'false';
```

**Configuration Options**:
```bash
# Hybrid Testing Mode
VITE_USE_MOCK_AUTH=true          # Mock authentication
VITE_USE_MOCK_AGENT=false        # Real Bedrock Agent
VITE_USE_DUMMY_DATA=true         # Mock UI data
VITE_AWS_REGION=us-east-1        # AWS region
VITE_BEDROCK_AGENT_ID=ZTBBVSC6Y1 # Agent ID
VITE_BEDROCK_AGENT_ALIAS_ID=TSTALIASID # Agent alias
```

## Data Models

### Agent Response Model
```typescript
interface AgentResponse {
  sessionId: string;
  messageId: string;
  content: string;
  timestamp: Date;
  metadata?: {
    tokensUsed?: number;
    processingTime?: number;
    confidence?: number;
  };
  citations?: Citation[];
  error?: string;
}
```

### Document Analysis Model
```typescript
interface DocumentAnalysis {
  documentId: string;
  summary: string;
  keyPoints: string[];
  insights: string[];
  suggestedQuestions: string[];
  confidence: number;
  processingTime: number;
}
```

### Quiz Model
```typescript
interface Quiz {
  id: string;
  title: string;
  questions: QuizQuestion[];
  metadata: {
    difficulty: 'easy' | 'medium' | 'hard';
    estimatedTime: number;
    topics: string[];
  };
}

interface QuizQuestion {
  id: string;
  type: 'multiple-choice' | 'true-false' | 'short-answer';
  question: string;
  options?: string[];
  correctAnswer: string;
  explanation: string;
}
```

### Interview Session Model
```typescript
interface InterviewSession {
  sessionId: string;
  topic: string;
  questions: InterviewQuestion[];
  responses: InterviewResponse[];
  feedback: InterviewFeedback[];
  status: 'active' | 'completed' | 'paused';
  startTime: Date;
  endTime?: Date;
}
```

## Error Handling

### Error Categories
1. **AWS Authentication Errors**: Invalid credentials, insufficient permissions
2. **Agent Communication Errors**: Network issues, service unavailable
3. **Request Validation Errors**: Invalid input, missing parameters
4. **Processing Errors**: Document processing failures, generation errors

### Error Handling Strategy
```typescript
class AgentError extends Error {
  constructor(
    message: string,
    public code: string,
    public category: 'auth' | 'network' | 'validation' | 'processing',
    public retryable: boolean = false
  ) {
    super(message);
  }
}

// Error handling with user-friendly messages
const handleAgentError = (error: AgentError) => {
  switch (error.category) {
    case 'auth':
      return 'Please check your AWS credentials configuration';
    case 'network':
      return 'Network connection issue. Please try again.';
    case 'validation':
      return 'Invalid input provided. Please check your request.';
    case 'processing':
      return 'Processing failed. Please try with different content.';
  }
};
```

## Testing Strategy

### Unit Testing
- Direct Agent Service methods
- Response formatting functions
- Error handling logic
- Session management

### Integration Testing
- AWS Bedrock Agent communication
- Document processing pipeline
- Quiz generation workflow
- Interview simulation flow

### User Acceptance Testing
- Complete agent testing workflows
- Error scenario handling
- Performance under load
- UI responsiveness

### Testing Scenarios
1. **Happy Path Testing**: All features work as expected
2. **Error Scenario Testing**: Network failures, invalid inputs
3. **Performance Testing**: Response times, concurrent requests
4. **Security Testing**: Credential handling, data privacy

## Performance Considerations

### Optimization Strategies
1. **Connection Pooling**: Reuse AWS SDK connections
2. **Response Caching**: Cache agent responses for repeated queries
3. **Lazy Loading**: Load agent service only when needed
4. **Request Batching**: Combine multiple requests where possible

### Performance Targets
- Agent response time: < 3 seconds for simple queries
- Document analysis: < 10 seconds for standard PDFs
- Quiz generation: < 5 seconds for 5-question quiz
- UI responsiveness: < 100ms for user interactions

## Security Considerations

### Data Protection
- No sensitive data stored locally
- AWS credentials handled securely through AWS CLI
- Session data encrypted in transit
- No persistent storage of user conversations

### Access Control
- AWS IAM permissions for Bedrock access only
- No production data access
- Isolated testing environment
- Audit logging for all agent interactions

## Deployment and Configuration

### Prerequisites
- Node.js 18+ installed
- AWS CLI configured with appropriate credentials
- Access to AWS Bedrock service
- React development environment

### Setup Process
1. Configure AWS CLI credentials
2. Update environment variables
3. Install dependencies
4. Start development server
5. Verify agent connectivity

### Configuration Validation
```typescript
const validateConfiguration = async () => {
  // Check AWS credentials
  const credentials = await AWS.config.credentialProvider.resolve();
  
  // Test Bedrock Agent access
  const testResponse = await bedrockAgentRuntime.invokeAgent({
    agentId: process.env.VITE_BEDROCK_AGENT_ID,
    agentAliasId: process.env.VITE_BEDROCK_AGENT_ALIAS_ID,
    sessionId: 'test-session',
    inputText: 'Hello'
  });
  
  return testResponse.completion ? 'success' : 'failed';
};
```

This design provides a comprehensive solution for rapid agent testing while maintaining simplicity and safety.
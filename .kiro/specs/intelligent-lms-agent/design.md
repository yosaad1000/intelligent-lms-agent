# Design Document

## Overview

The Intelligent LMS AI Agent is built as a serverless, microservices-based architecture on AWS, leveraging Bedrock for AI capabilities, Cognito for authentication, and a combination of Lambda functions and API Gateway for business logic. The system follows a hub-and-spoke pattern with DynamoDB as the central data store and S3 for file storage, ensuring scalability and cost-effectiveness.

## Architecture

### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│  Student UI          Teacher Dashboard         Mobile App            │
│  - Upload Notes      - Analytics               - Offline Mode        │
│  - Chat Interface    - Feedback View           - Sync Service        │
│  - Voice Record      - Student Progress        - Cache Manager       │
│  - Quiz Taking       - Class Insights                                │
└─────────────┬───────────────────────┬───────────────────────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION & API LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│  AWS Cognito              API Gateway (REST + WebSocket)             │
│  - User Pools             - Cognito Authorizer                       │
│  - JWT Tokens             - Rate Limiting                            │
│  - MFA (Optional)         - Request Validation                       │
└─────────────┬───────────────────────┬───────────────────────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│              AWS Bedrock Agent (Central Intelligence)                │
│              ┌──────────────────────────────────┐                    │
│              │  Agent Orchestration Logic       │                    │
│              │  - Task Routing                  │                    │
│              │  - Tool Selection                │                    │
│              │  - Context Management            │                    │
│              └──────────┬───────────────────────┘                    │
│                         │                                            │
│         ┌───────────────┼───────────────┬──────────────┐            │
│         ▼               ▼               ▼              ▼            │
│   ┌─────────┐    ┌──────────┐    ┌──────────┐  ┌──────────┐        │
│   │ Bedrock │    │ Bedrock  │    │SageMaker │  │ Lambda   │        │
│   │   LLM   │    │    KB    │    │ Endpoint │  │  Tools   │        │
│   └─────────┘    └──────────┘    └──────────┘  └──────────┘        │
└─────────────┬───────────────────────┬───────────────────────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │   Amazon S3     │  │   DynamoDB       │  │   OpenSearch     │   │
│  ├─────────────────┤  ├──────────────────┤  ├──────────────────┤   │
│  │ • Raw Notes     │  │ • ChatHistory    │  │ • Student        │   │
│  │ • Audio Files   │  │ • StudentProfile │  │   Embeddings     │   │
│  │ • Transcripts   │  │ • QuizResults    │  │ • Similarity     │   │
│  │ • Quiz Data     │  │ • GroupChats     │  │   Search         │   │
│  │ • Cache Assets  │  │ • Assignments    │  │ • Peer Matching  │   │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘   │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐                          │
│  │  SageMaker      │  │  Secrets         │                          │
│  │  Feature Store  │  │  Manager         │                          │
│  ├─────────────────┤  ├──────────────────┤                          │
│  │ • Intelligence  │  │ • API Keys       │                          │
│  │   Tracking      │  │ • YouTube API    │                          │
│  │ • Performance   │  │ • Credentials    │                          │
│  │   History       │  └──────────────────┘                          │
│  └─────────────────┘                                                 │
└─────────────┬───────────────────────┬───────────────────────────────┘
              │                       │
              ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MICROSERVICES LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│  Lambda Function 1: Note Processor                                   │
│  Lambda Function 2: Chat Handler                                     │
│  Lambda Function 3: Voice Interview Processor                        │
│  Lambda Function 4: Quiz Generator                                   │
│  Lambda Function 5: Learning Path Generator                           │
│  Lambda Function 6: Group Chat Manager                               │
│  Lambda Function 7: Peer Matcher                                     │
│  Lambda Function 8: Sync Service (Offline Mode)                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Intelligence Embedding Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE FLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Student Interaction → Generate Embedding → Update Profile           │
│         │                      │                    │                │
│         ▼                      ▼                    ▼                │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │   Chat      │    │    Bedrock      │    │   DynamoDB      │      │
│  │ Conversation│    │   Embeddings    │    │ StudentProfile  │      │
│  │             │    │                 │    │                 │      │
│  │   Quiz      │    │   SageMaker     │    │   OpenSearch    │      │
│  │  Results    │    │   Models        │    │   Index         │      │
│  │             │    │                 │    │                 │      │
│  │   Voice     │    │   Weighted      │    │   Similarity    │      │
│  │ Interview   │    │   Averaging     │    │   Matching      │      │
│  └─────────────┘    └─────────────────┘    └─────────────────┘      │
│                                                                      │
│  Embedding Update Formula:                                           │
│  new_embedding = 0.9 * old_embedding + 0.1 * interaction_embedding  │
└─────────────────────────────────────────────────────────────────────┘
```

### Group Chat Clustering Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GROUP CHAT INTELLIGENCE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Student A: "Why does entropy increase?"                             │
│  Student B: "Explain second law of thermodynamics"                   │
│         │                      │                                     │
│         ▼                      ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │           WebSocket API Gateway                         │        │
│  │    Connection IDs stored in DynamoDB                    │        │
│  └─────────────┬───────────────────────────────────────────┘        │
│                │                                                     │
│                ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │         Lambda: Group Chat Manager                      │        │
│  │  1. Generate embeddings for each question               │        │
│  │  2. Calculate cosine similarity                         │        │
│  │  3. If similarity > 0.85 → Cluster questions           │        │
│  │  4. Wait 30 seconds for more similar questions          │        │
│  │  5. Generate comprehensive answer via Bedrock           │        │
│  │  6. Broadcast to all students in cluster                │        │
│  └─────────────┬───────────────────────────────────────────┘        │
│                │                                                     │
│                ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │              DynamoDB: GroupChats                       │        │
│  │  Store: clusterId, embeddings, responses, timestamps    │        │
│  └─────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Authentication Service
**Technology**: AWS Cognito + Lambda
**Responsibilities**:
- User registration and verification
- JWT token management
- Role-based access control (Student/Teacher)
- Session management

**Key Interfaces**:
```typescript
interface AuthService {
  register(email: string, password: string, role: UserRole): Promise<AuthResult>
  login(email: string, password: string): Promise<AuthResult>
  refreshToken(refreshToken: string): Promise<AuthResult>
  logout(userId: string): Promise<void>
}

interface AuthResult {
  accessToken: string
  refreshToken: string
  user: UserProfile
}
```

### 2. File Processing Service
**Technology**: Lambda + S3 + Bedrock Knowledge Base
**Responsibilities**:
- File upload handling
- Text extraction (PDF, DOCX, TXT)
- Content indexing in Bedrock KB
- Metadata storage

**Key Interfaces**:
```typescript
interface FileService {
  uploadFile(file: File, userId: string): Promise<UploadResult>
  processFile(fileId: string): Promise<ProcessingResult>
  getFileStatus(fileId: string): Promise<FileStatus>
  deleteFile(fileId: string, userId: string): Promise<void>
}

interface ProcessingResult {
  fileId: string
  extractedText: string
  concepts: string[]
  embeddingStatus: 'processing' | 'completed' | 'failed'
}
```

### 3. AI Agent Service
**Technology**: Bedrock Agent + Knowledge Base + Lambda
**Responsibilities**:
- Question answering using student's notes
- Context retrieval and response generation
- Chat history management
- Conversation flow control

**Key Interfaces**:
```typescript
interface AIAgentService {
  askQuestion(question: string, userId: string): Promise<AgentResponse>
  getChatHistory(userId: string, limit?: number): Promise<ChatMessage[]>
  generateQuiz(userId: string, topic?: string): Promise<Quiz>
}

interface AgentResponse {
  answer: string
  sources: DocumentSource[]
  confidence: number
  conversationId: string
}
```

### 4. Voice Processing Service
**Technology**: Amazon Transcribe + Lambda + Bedrock
**Responsibilities**:
- Audio file processing
- Speech-to-text conversion
- Response analysis and scoring
- Learning profile updates

**Key Interfaces**:
```typescript
interface VoiceService {
  startInterview(userId: string): Promise<InterviewSession>
  uploadAudio(sessionId: string, audioFile: File): Promise<TranscriptionResult>
  analyzeResponse(transcription: string, question: string): Promise<AnalysisResult>
}

interface AnalysisResult {
  score: number
  conceptsIdentified: string[]
  strengths: string[]
  improvements: string[]
}
```

### 5. Assessment Engine
**Technology**: Lambda + Bedrock + DynamoDB
**Responsibilities**:
- Dynamic quiz generation
- Answer evaluation
- Performance tracking
- Adaptive difficulty adjustment

**Key Interfaces**:
```typescript
interface AssessmentService {
  generateQuiz(userId: string, difficulty: string): Promise<Quiz>
  submitAnswers(quizId: string, answers: Answer[]): Promise<QuizResult>
  getPerformanceHistory(userId: string): Promise<PerformanceData[]>
}

interface Quiz {
  id: string
  questions: Question[]
  timeLimit?: number
  difficulty: 'easy' | 'medium' | 'hard'
}
```

### 6. Intelligence Embedding Service
**Technology**: Bedrock Embeddings + SageMaker + OpenSearch
**Responsibilities**:
- Generate and update student intelligence embeddings
- Track concept mastery over time
- Enable similarity-based peer matching
- Store embeddings for fast retrieval

**Key Interfaces**:
```typescript
interface IntelligenceService {
  updateStudentEmbedding(userId: string, interaction: LearningInteraction): Promise<EmbeddingUpdate>
  findSimilarStudents(userId: string, subject: string): Promise<StudentMatch[]>
  getConceptMastery(userId: string): Promise<ConceptMasteryMap>
  trackPerformanceHistory(userId: string, results: QuizResult): Promise<void>
}

interface LearningInteraction {
  type: 'chat' | 'quiz' | 'voice_interview'
  content: string
  subject: string
  concepts: string[]
  performance?: number
}

interface EmbeddingUpdate {
  oldEmbedding: number[]
  newEmbedding: number[]
  confidenceScore: number
  conceptsUpdated: string[]
}
```

### 7. Group Chat Management Service
**Technology**: API Gateway WebSocket + Lambda + DynamoDB
**Responsibilities**:
- Real-time message handling via WebSocket
- Question similarity detection and clustering
- AI-powered group responses
- Chat history with embeddings

**Key Interfaces**:
```typescript
interface GroupChatService {
  handleMessage(connectionId: string, message: ChatMessage): Promise<ChatResponse>
  clusterSimilarQuestions(message: ChatMessage): Promise<ClusterResult>
  generateGroupResponse(clusteredQuestions: ChatMessage[]): Promise<AIResponse>
  broadcastToCluster(clusterId: string, response: AIResponse): Promise<void>
}

interface ClusterResult {
  clusterId: string
  similarityScore: number
  waitingPeriod: number
  relatedMessages: ChatMessage[]
}
```

### 8. Peer Matching Service
**Technology**: OpenSearch + Lambda + DynamoDB
**Responsibilities**:
- Find students with complementary knowledge
- Route questions to capable peers
- Track peer assistance success rates
- Manage study group formation

**Key Interfaces**:
```typescript
interface PeerMatchingService {
  findPeerHelpers(question: string, concepts: string[]): Promise<PeerMatch[]>
  routeQuestionToPeer(questionId: string, peerId: string): Promise<RoutingResult>
  trackPeerAssistance(helperId: string, questionId: string, success: boolean): Promise<void>
  suggestStudyGroups(userId: string): Promise<StudyGroup[]>
}

interface PeerMatch {
  peerId: string
  matchScore: number
  strongConcepts: string[]
  availabilityStatus: 'online' | 'offline' | 'busy'
  helpSuccessRate: number
}
```

### 9. Learning Path Generator
**Technology**: Bedrock Agent + Lambda + DynamoDB
**Responsibilities**:
- Analyze student performance patterns
- Generate personalized study sequences
- Recommend practice exercises based on weak areas
- Create adaptive learning schedules

**Key Interfaces**:
```typescript
interface LearningPathService {
  generateLearningPath(userId: string, targetConcepts: string[]): Promise<LearningPath>
  getPersonalizedRecommendations(userId: string): Promise<LearningRecommendation[]>
  analyzeConceptGaps(userId: string): Promise<ConceptGap[]>
  createStudySchedule(userId: string, timeAvailable: number): Promise<StudySchedule>
}

interface LearningPath {
  pathId: string
  userId: string
  concepts: ConceptStep[]
  estimatedDuration: number
  difficulty: 'beginner' | 'intermediate' | 'advanced'
}

interface ConceptStep {
  concept: string
  order: number
  resources: LearningResource[]
  exercises: Exercise[]
  prerequisites: string[]
}
```

## Data Models

### User Profile
```typescript
interface UserProfile {
  userId: string
  email: string
  role: 'student' | 'teacher'
  createdAt: Date
  lastLoginAt: Date
  preferences: UserPreferences
  learningProfile?: LearningProfile
}

interface LearningProfile {
  conceptMastery: Record<string, number> // concept -> mastery level (0-1)
  learningStyle: 'visual' | 'auditory' | 'kinesthetic' | 'mixed'
  performanceHistory: PerformanceMetric[]
  weakAreas: string[]
  strongAreas: string[]
}
```

### File Metadata
```typescript
interface FileMetadata {
  fileId: string
  userId: string
  fileName: string
  fileType: string
  uploadedAt: Date
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
  s3Key: string
  extractedConcepts: string[]
  knowledgeBaseId?: string
}
```

### Enhanced Chat History with Embeddings
```typescript
interface ChatMessage {
  messageId: string
  userId: string
  conversationId: string
  type: 'user' | 'agent'
  content: string
  timestamp: Date
  subject: string
  topic: string
  embedding: string // base64 encoded vector
  sentiment: 'positive' | 'neutral' | 'negative'
  contextUsed: string[] // note IDs used for context
  sources?: DocumentSource[]
  metadata?: Record<string, any>
}

interface GroupChatMessage {
  chatRoomId: string
  timestamp: number
  userId: string
  message: string
  embedding: number[]
  clusterId?: string
  similarMessages?: string[]
  aiResponse?: string
  responseTimestamp?: number
}
```

### Student Intelligence Profile
```typescript
interface StudentProfile {
  userId: string
  personalInfo: {
    name: string
    grade: string
  }
  intelligenceEmbeddings: {
    [subject: string]: {
      embedding: number[]
      lastUpdated: Date
      confidence: number
    }
  }
  conceptMastery: Record<string, number> // concept -> mastery level (0-1)
  learningStyle: 'visual' | 'auditory' | 'kinesthetic' | 'mixed'
  weakConcepts: string[]
  totalQuizzesTaken: number
  averageScore: number
  peerHelpStats: {
    questionsAsked: number
    questionsAnswered: number
    helpSuccessRate: number
  }
}

interface OpenSearchStudentIndex {
  userId: string
  subject: string
  embedding_vector: number[]
  performance_score: number
  last_activity: Date
  availability_status: 'online' | 'offline' | 'busy'
}
```

### Quiz Data
```typescript
interface Question {
  id: string
  text: string
  options: string[]
  correctAnswer: number
  explanation: string
  concept: string
  difficulty: number
}

interface QuizResult {
  quizId: string
  userId: string
  score: number
  totalQuestions: number
  correctAnswers: number
  completedAt: Date
  timeSpent: number
  conceptScores: Record<string, number>
}
```

## Error Handling

### Error Categories and Responses

1. **Authentication Errors**
   - Invalid credentials → 401 Unauthorized
   - Expired tokens → 401 with refresh instruction
   - Insufficient permissions → 403 Forbidden

2. **File Processing Errors**
   - Unsupported file format → 400 Bad Request
   - File too large → 413 Payload Too Large
   - Processing timeout → 408 Request Timeout
   - S3 upload failure → 500 Internal Server Error

3. **AI Service Errors**
   - Bedrock rate limiting → 429 Too Many Requests with retry-after
   - Knowledge base not ready → 503 Service Unavailable
   - Invalid query format → 400 Bad Request

4. **Voice Processing Errors**
   - Transcription failure → 422 Unprocessable Entity
   - Audio format not supported → 415 Unsupported Media Type
   - Audio too long/short → 400 Bad Request

### Error Response Format
```typescript
interface ErrorResponse {
  error: {
    code: string
    message: string
    details?: Record<string, any>
    retryable: boolean
    retryAfter?: number
  }
  requestId: string
  timestamp: Date
}
```

### Retry and Circuit Breaker Patterns
- Exponential backoff for Bedrock API calls
- Circuit breaker for Bedrock Agent API
- Dead letter queues for failed processing jobs
- Graceful degradation when AI services are unavailable

## Testing Strategy

### Unit Testing
- **Lambda Functions**: Mock AWS SDK calls, test business logic
- **Frontend Components**: Jest + React Testing Library
- **API Endpoints**: Supertest for integration testing
- **Coverage Target**: 80% code coverage minimum

### Integration Testing
- **API Gateway → Lambda**: End-to-end request flow
- **S3 → Lambda Triggers**: File processing workflows
- **Bedrock Integration**: Knowledge base queries and responses
- **Cognito Authentication**: Token validation and user flows

### End-to-End Testing
- **User Journeys**: Complete workflows from UI to database
- **Cross-Service Communication**: Multi-service transaction testing
- **Performance Testing**: Load testing with 500+ concurrent users
- **Security Testing**: Penetration testing and vulnerability scans

### Test Data Management
- **Synthetic Data**: Generated test files and user profiles
- **Isolated Environments**: Separate test AWS accounts
- **Data Cleanup**: Automated test data removal
- **Seed Data**: Consistent test scenarios across environments

## AWS Services Architecture Mapping

### Core AI & Intelligence Stack
| Feature | AWS Services Used | Purpose |
|---------|------------------|---------|
| **Central Intelligence** | Bedrock Agent + Claude LLM | Task routing, tool selection, context management |
| **Knowledge Base** | Bedrock KB (S3 data source) | Student note indexing and retrieval |
| **Embeddings Generation** | Bedrock Titan Embeddings | Convert text to vectors for similarity |
| **ML Intelligence Tracking** | SageMaker (Feature Store + Endpoints) | Track learning patterns and predictions |
| **Vector Similarity Search** | OpenSearch Service | Find similar students and content |
| **Voice Processing** | Amazon Transcribe | Speech-to-text for interviews |

### Data & Storage Architecture
| Data Type | Storage Service | Access Pattern |
|-----------|----------------|----------------|
| **Raw Files** | S3 (user-specific folders) | Upload → Process → Archive |
| **Chat History** | DynamoDB (with embeddings) | Real-time read/write with GSI |
| **Student Profiles** | DynamoDB + OpenSearch | Profile updates + similarity queries |
| **Group Chat** | DynamoDB + WebSocket API | Real-time messaging with clustering |
| **Performance Data** | SageMaker Feature Store | ML model training and inference |
| **API Secrets** | Secrets Manager | Bedrock API keys and credentials |

### Microservices Lambda Functions
| Function | Trigger | Purpose | AWS Services Used |
|----------|---------|---------|-------------------|
| **Note Processor** | S3 Event | Extract text → Generate embeddings → Index in KB | S3, Bedrock, DynamoDB |
| **Chat Handler** | API Gateway | Process questions → Retrieve context → Generate responses | Bedrock Agent, DynamoDB |
| **Voice Processor** | S3 Event | Transcribe → Analyze → Update profile | Transcribe, Bedrock, DynamoDB |
| **Quiz Generator** | API Request | Fetch profile → Generate questions → Adapt difficulty | Bedrock, SageMaker, DynamoDB |
| **Learning Path Generator** | API Request | Analyze gaps → Generate sequence → Create schedule | Bedrock Agent, DynamoDB |
| **Group Chat Manager** | WebSocket API | Cluster questions → Generate responses → Broadcast | API Gateway WS, DynamoDB |
| **Peer Matcher** | API Request | Query embeddings → Find similar students → Route questions | OpenSearch, DynamoDB |
| **Sync Service** | API Request | Handle offline data → Merge conflicts → Update cloud | DynamoDB, S3 |

### Real-Time & Communication
| Feature | AWS Service | Configuration |
|---------|-------------|---------------|
| **WebSocket Chat** | API Gateway WebSocket | Connection management + message routing |
| **Real-time Updates** | API Gateway WebSocket | Broadcast to connection IDs stored in DynamoDB |
| **Notifications** | SNS (optional) | Push notifications for peer help requests |

### Security & Access Control
| Security Layer | AWS Service | Implementation |
|----------------|-------------|----------------|
| **Authentication** | Cognito User Pools | JWT tokens with role-based access |
| **API Authorization** | API Gateway Cognito Authorizer | Validate tokens on each request |
| **Data Encryption** | S3 SSE + DynamoDB encryption | Encrypt at rest and in transit |
| **IAM Policies** | IAM Roles | Least privilege for Lambda functions |
| **Rate Limiting** | API Gateway | Prevent abuse and manage costs |

### Intelligence Update Flow
```
Student Interaction → Lambda Function → Generate Embedding → Update Profile
                                    ↓
                            Weighted Average Calculation
                                    ↓
                    Store in DynamoDB + Index in OpenSearch
                                    ↓
                        Enable Similarity-Based Features
```

### Group Chat Clustering Algorithm
```python
def cluster_similar_questions(new_message, recent_messages):
    new_embedding = bedrock_titan.generate_embedding(new_message)
    
    for msg in recent_messages:
        similarity = cosine_similarity(new_embedding, msg['embedding'])
        
        if similarity > 0.85:  # Highly similar
            return msg['clusterId']
    
    # Create new cluster if no similar questions found
    return create_new_cluster()
```

### Personalization Engine Logic
```python
def personalize_content(user_id, content_type):
    # Fetch student intelligence profile
    profile = dynamodb.get_item(Key={'userId': user_id})
    
    # Get weak concepts from embeddings
    weak_concepts = identify_weak_areas(profile['intelligenceEmbeddings'])
    
    if content_type == 'note_indexing':
        # Prioritize weak concept sections in Bedrock KB
        return prioritize_weak_concepts(weak_concepts)
    
    elif content_type == 'quiz_generation':
        # Use SageMaker to adjust difficulty
        return sagemaker_endpoint.invoke(profile, weak_concepts)
    
    elif content_type == 'learning_path':
        # Generate personalized learning sequence
        return bedrock_agent.generate_learning_path(weak_concepts)
```

### Monitoring and Observability
- **CloudWatch Dashboards**: Real-time metrics and alerts
- **X-Ray Tracing**: Distributed request tracing across microservices
- **Custom Metrics**: Business KPIs (chat engagement, quiz completion rates)
- **Log Aggregation**: Centralized logging with structured formats (no PII)
- **Health Checks**: Automated service health monitoring
- **Cost Monitoring**: Track Bedrock API usage and OpenSearch costs

### Performance Targets
- **API Response Time**: < 2 seconds for 95th percentile
- **File Processing**: < 30 seconds for documents up to 10MB
- **Quiz Generation**: < 5 seconds for 10-question quiz
- **Voice Transcription**: < 60 seconds for 5-minute audio
- **Embedding Updates**: < 1 second for profile updates
- **Peer Matching**: < 3 seconds for similarity search
- **Group Chat Clustering**: < 30 seconds clustering window
- **Concurrent Users**: Support 500+ simultaneous users
import { BedrockAgentRuntimeClient, InvokeAgentCommand } from '@aws-sdk/client-bedrock-agent-runtime';
import { S3Client } from '@aws-sdk/client-s3';
import { v4 as uuidv4 } from 'uuid';
import type { ConfigurationStatus } from './configurationService';
import { configurationService } from './configurationService';
import { errorHandlingService, AgentError } from './errorHandlingService';
import { performanceMonitor } from './performanceMonitor';

// Types for agent communication
export interface AgentResponse {
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

export interface Citation {
  source: string;
  content: string;
  confidence: number;
}

export interface DocumentAnalysis {
  documentId: string;
  summary: string;
  keyPoints: string[];
  insights: string[];
  suggestedQuestions: string[];
  confidence: number;
  processingTime: number;
}

export interface Quiz {
  id: string;
  title: string;
  questions: QuizQuestion[];
  metadata: {
    difficulty: 'easy' | 'medium' | 'hard';
    estimatedTime: number;
    topics: string[];
  };
}

export interface QuizQuestion {
  id: string;
  type: 'multiple-choice' | 'true-false' | 'short-answer';
  question: string;
  options?: string[];
  correctAnswer: string;
  explanation: string;
}

export interface QuizOptions {
  difficulty: 'easy' | 'medium' | 'hard';
  questionCount: number;
  topics?: string[];
  questionTypes?: ('multiple-choice' | 'true-false' | 'short-answer')[];
}

export interface InterviewSession {
  sessionId: string;
  topic: string;
  questions: InterviewQuestion[];
  responses: InterviewResponse[];
  feedback: InterviewFeedback[];
  status: 'active' | 'completed' | 'paused';
  startTime: Date;
  endTime?: Date;
}

export interface InterviewQuestion {
  id: string;
  question: string;
  expectedPoints: string[];
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface InterviewResponse {
  questionId: string;
  response: string;
  timestamp: Date;
  audioUrl?: string;
}

export interface InterviewFeedback {
  questionId: string;
  score: number;
  feedback: string;
  suggestions: string[];
  strengths: string[];
  improvements: string[];
}

// Re-export AgentError from error handling service
export { AgentError } from './errorHandlingService';

// Session management
class SessionManager {
  private sessions: Map<string, any> = new Map();

  createSession(): string {
    const sessionId = uuidv4();
    this.sessions.set(sessionId, {
      id: sessionId,
      createdAt: new Date(),
      lastActivity: new Date(),
      messages: []
    });
    return sessionId;
  }

  getSession(sessionId: string) {
    return this.sessions.get(sessionId);
  }

  updateSession(sessionId: string, data: any) {
    const session = this.sessions.get(sessionId);
    if (session) {
      this.sessions.set(sessionId, { ...session, ...data, lastActivity: new Date() });
    }
  }

  clearSession(sessionId: string) {
    this.sessions.delete(sessionId);
  }

  cleanupOldSessions() {
    const now = new Date();
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours

    for (const [sessionId, session] of this.sessions.entries()) {
      if (now.getTime() - session.lastActivity.getTime() > maxAge) {
        this.sessions.delete(sessionId);
      }
    }
  }
}

// Main Direct Agent Service
class DirectAgentService {
  private sessionManager: SessionManager;
  private agentId: string;
  private agentAliasId: string;
  private region: string;

  constructor() {
    this.region = import.meta.env.VITE_AWS_REGION || 'us-east-1';
    this.agentId = import.meta.env.VITE_BEDROCK_AGENT_ID || '';
    this.agentAliasId = import.meta.env.VITE_BEDROCK_AGENT_ALIAS_ID || '';

    this.sessionManager = new SessionManager();

    // Cleanup old sessions periodically
    setInterval(() => {
      this.sessionManager.cleanupOldSessions();
    }, 60 * 60 * 1000); // Every hour
  }

  // Get Bedrock client with connection pooling
  private getBedrockClient(): BedrockAgentRuntimeClient {
    const clientKey = `bedrock-${this.region}`;
    
    return performanceMonitor.getConnection(clientKey, () => {
      return new BedrockAgentRuntimeClient({
        region: this.region,
        credentials: {
          accessKeyId: import.meta.env.VITE_AWS_ACCESS_KEY_ID || '',
          secretAccessKey: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY || ''
        },
        maxAttempts: 3,
        requestHandler: {
          requestTimeout: 30000, // 30 second timeout
          httpsAgent: {
            keepAlive: true,
            maxSockets: 50
          }
        }
      });
    });
  }

  // Get S3 client with connection pooling
  private getS3Client(): S3Client {
    const clientKey = `s3-${this.region}`;
    
    return performanceMonitor.getConnection(clientKey, () => {
      return new S3Client({
        region: this.region,
        credentials: {
          accessKeyId: import.meta.env.VITE_AWS_ACCESS_KEY_ID || '',
          secretAccessKey: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY || ''
        },
        maxAttempts: 3,
        requestHandler: {
          requestTimeout: 30000,
          httpsAgent: {
            keepAlive: true,
            maxSockets: 50
          }
        }
      });
    });
  }

  // Validate configuration using the configuration service
  async validateConfiguration(): Promise<ConfigurationStatus> {
    return await configurationService.validateConfiguration();
  }

  // Get configuration status
  getConfigurationStatus(): ConfigurationStatus | null {
    return configurationService['cachedStatus'];
  }

  // Check if hybrid testing mode is enabled
  isHybridTestingMode(): boolean {
    return configurationService.isHybridTestingMode();
  }

  // Core agent communication with retry logic and performance monitoring
  async sendMessage(
    message: string, 
    sessionId?: string, 
    isTest: boolean = false
  ): Promise<AgentResponse> {
    const actualSessionId = sessionId || this.sessionManager.createSession();
    const messageId = uuidv4();

    // Check cache first for non-test messages
    if (!isTest) {
      const cacheKey = `message-${actualSessionId}-${message.substring(0, 100)}`;
      const cachedResponse = performanceMonitor.getCache(cacheKey);
      if (cachedResponse) {
        console.log('📦 Using cached response');
        return {
          ...cachedResponse,
          messageId: uuidv4(), // New message ID for each request
          timestamp: new Date()
        };
      }
    }

    return await performanceMonitor.measureOperation(
      'sendMessage',
      async () => {
        return await errorHandlingService.executeWithRetry(
          async () => {
            const startTime = Date.now();
            console.log(`🤖 Sending message to agent: "${message.substring(0, 50)}..."`);

            const command = new InvokeAgentCommand({
              agentId: this.agentId,
              agentAliasId: this.agentAliasId,
              sessionId: actualSessionId,
              inputText: message
            });

            const bedrockClient = this.getBedrockClient();
            const response = await bedrockClient.send(command);
          
          // Process streaming response
          let content = '';
          const citations: Citation[] = [];

          if (response.completion) {
            for await (const chunk of response.completion) {
              if (chunk.chunk?.bytes) {
                const chunkText = new TextDecoder().decode(chunk.chunk.bytes);
                content += chunkText;
              }
              
              // Extract citations if available
              if (chunk.trace?.trace?.orchestrationTrace?.observation?.finalResponse?.text) {
                // Process citations from trace
              }
            }
          }

          const processingTime = Date.now() - startTime;

          // Update session
          if (!isTest) {
            this.sessionManager.updateSession(actualSessionId, {
              messages: [
                ...(this.sessionManager.getSession(actualSessionId)?.messages || []),
                { role: 'user', content: message, timestamp: new Date() },
                { role: 'assistant', content, timestamp: new Date() }
              ]
            });
          }

          const agentResponse: AgentResponse = {
            sessionId: actualSessionId,
            messageId,
            content: content || 'No response received from agent',
            timestamp: new Date(),
            metadata: {
              processingTime,
              tokensUsed: content.length // Approximate
            },
            citations
          };

          // Cache successful responses (but not test messages)
          if (!isTest && content) {
            const cacheKey = `message-${actualSessionId}-${message.substring(0, 100)}`;
            performanceMonitor.setCache(cacheKey, agentResponse, 5 * 60 * 1000); // 5 minute cache
          }

          console.log(`✅ Agent response received (${processingTime}ms):`, content.substring(0, 100));
          return agentResponse;
          },
          'sendMessage',
          { maxRetries: 2 } // Fewer retries for interactive messages
        );
      },
      {
        messageLength: message.length,
        sessionId: actualSessionId,
        isTest
      }
    );

    } catch (error) {
      console.error('❌ Agent communication error:', error);
      
      const agentError = error instanceof AgentError ? error : errorHandlingService.processError(error, {
        operation: 'sendMessage',
        sessionId: actualSessionId,
        messageId,
        message: message.substring(0, 100)
      });
      
      return {
        sessionId: actualSessionId,
        messageId,
        content: '',
        timestamp: new Date(),
        error: agentError.details.userMessage
      };
    }
  }

  // Session management methods
  createSession(): string {
    return this.sessionManager.createSession();
  }

  getSession(sessionId: string) {
    return this.sessionManager.getSession(sessionId);
  }

  clearSession(sessionId: string): void {
    this.sessionManager.clearSession(sessionId);
  }

  // Error handling - delegate to error handling service
  private handleError(error: any, context?: Record<string, any>): AgentError {
    return errorHandlingService.processError(error, context);
  }

  // Get error display information
  getErrorDisplayInfo(error: AgentError) {
    return errorHandlingService.getErrorDisplayInfo(error);
  }

  // Get recent errors for debugging
  getRecentErrors(limit?: number) {
    return errorHandlingService.getRecentErrors(limit);
  }

  // Get error statistics
  getErrorStatistics() {
    return errorHandlingService.getErrorStatistics();
  }

  // Document processing with retry logic and performance monitoring
  async analyzeDocument(documentUrl: string, query: string = "Analyze this document"): Promise<DocumentAnalysis> {
    const documentId = uuidv4();

    // Check cache first
    const cacheKey = `document-${documentUrl}-${query.substring(0, 50)}`;
    const cachedAnalysis = performanceMonitor.getCache(cacheKey);
    if (cachedAnalysis) {
      console.log('📦 Using cached document analysis');
      return {
        ...cachedAnalysis,
        documentId: uuidv4() // New document ID for each request
      };
    }

    return await performanceMonitor.measureOperation(
      'analyzeDocument',
      async () => {
        return await errorHandlingService.executeWithRetry(
        async () => {
          const startTime = Date.now();
          console.log(`📄 Analyzing document: ${documentUrl}`);

          const analysisPrompt = `Please analyze the document at ${documentUrl} and provide:
1. A comprehensive summary
2. Key points and main topics
3. Important insights and takeaways
4. Suggested questions for further exploration

Query: ${query}`;

          const response = await this.sendMessage(analysisPrompt);
          
          if (response.error) {
            throw new AgentError(response.error, 'ANALYSIS_ERROR', 'processing');
          }

          // Parse the response to extract structured data
          const analysis = this.parseDocumentAnalysis(response.content);
          
          const documentAnalysis = {
            documentId,
            summary: analysis.summary,
            keyPoints: analysis.keyPoints,
            insights: analysis.insights,
            suggestedQuestions: analysis.suggestedQuestions,
            confidence: 0.85, // Default confidence
            processingTime: Date.now() - startTime
          };

          // Cache the analysis result
          performanceMonitor.setCache(cacheKey, documentAnalysis, 15 * 60 * 1000); // 15 minute cache

          return documentAnalysis;
        },
        'analyzeDocument',
        { maxRetries: 1 } // Document analysis is expensive, limit retries
      );
    },
    {
      documentUrl,
      queryLength: query.length
    }
  );

    } catch (error) {
      console.error('❌ Document analysis error:', error);
      throw this.handleError(error, { operation: 'analyzeDocument', documentUrl, query });
    }
  }

  // Quiz generation with retry logic
  async generateQuiz(content: string, options: QuizOptions): Promise<Quiz> {
    const quizId = uuidv4();

    try {
      return await errorHandlingService.executeWithRetry(
        async () => {
          console.log(`📝 Generating quiz with ${options.questionCount} questions`);

          const quizPrompt = `Create a ${options.difficulty} difficulty quiz with ${options.questionCount} questions based on the following content:

${content}

Requirements:
- Difficulty: ${options.difficulty}
- Question types: ${options.questionTypes?.join(', ') || 'multiple-choice'}
- Topics: ${options.topics?.join(', ') || 'general'}

Format the response as a JSON object with the following structure:
{
  "title": "Quiz Title",
  "questions": [
    {
      "id": "unique_id",
      "type": "multiple-choice|true-false|short-answer",
      "question": "Question text",
      "options": ["option1", "option2", "option3", "option4"] (for multiple-choice),
      "correctAnswer": "correct answer",
      "explanation": "explanation of the answer"
    }
  ]
}`;

          const response = await this.sendMessage(quizPrompt);
          
          if (response.error) {
            throw new AgentError(response.error, 'QUIZ_ERROR', 'processing');
          }

          // Parse the quiz from the response
          const quiz = this.parseQuizResponse(response.content, quizId, options);
          
          console.log(`✅ Quiz generated with ${quiz.questions.length} questions`);
          return quiz;
        },
        'generateQuiz',
        { maxRetries: 1 } // Quiz generation is expensive, limit retries
      );

    } catch (error) {
      console.error('❌ Quiz generation error:', error);
      throw this.handleError(error, { 
        operation: 'generateQuiz', 
        contentLength: content.length, 
        options 
      });
    }
  }

  // Interview simulation with retry logic
  async startInterview(topic: string): Promise<InterviewSession> {
    const sessionId = this.createSession();
    
    try {
      return await errorHandlingService.executeWithRetry(
        async () => {
          console.log(`🎤 Starting interview on topic: ${topic}`);

          const interviewPrompt = `Start an interview session on the topic: ${topic}

Please:
1. Introduce yourself as an AI interviewer
2. Explain the interview process
3. Ask the first question
4. Keep questions relevant to ${topic}
5. Provide constructive feedback after each response

Begin the interview now.`;

          const response = await this.sendMessage(interviewPrompt, sessionId);
          
          if (response.error) {
            throw new AgentError(response.error, 'INTERVIEW_ERROR', 'processing');
          }

          const session: InterviewSession = {
            sessionId,
            topic,
            questions: [{
              id: uuidv4(),
              question: response.content,
              expectedPoints: [],
              difficulty: 'medium'
            }],
            responses: [],
            feedback: [],
            status: 'active',
            startTime: new Date()
          };

          console.log(`✅ Interview session started: ${sessionId}`);
          return session;
        },
        'startInterview',
        { maxRetries: 1 }
      );

    } catch (error) {
      console.error('❌ Interview start error:', error);
      throw this.handleError(error, { operation: 'startInterview', topic, sessionId });
    }
  }

  async conductInterview(sessionId: string, response: string): Promise<InterviewFeedback> {
    try {
      return await errorHandlingService.executeWithRetry(
        async () => {
          console.log(`🎤 Processing interview response for session: ${sessionId}`);

          const feedbackPrompt = `The candidate provided this response: "${response}"

Please provide:
1. A score from 1-10
2. Detailed feedback on the response
3. Specific suggestions for improvement
4. Strengths demonstrated in the response
5. Areas that need improvement
6. The next interview question (if continuing)

Format as JSON:
{
  "score": number,
  "feedback": "detailed feedback",
  "suggestions": ["suggestion1", "suggestion2"],
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"],
  "nextQuestion": "next question text"
}`;

          const agentResponse = await this.sendMessage(feedbackPrompt, sessionId);
          
          if (agentResponse.error) {
            throw new AgentError(agentResponse.error, 'FEEDBACK_ERROR', 'processing');
          }

          const feedback = this.parseInterviewFeedback(agentResponse.content);
          
          console.log(`✅ Interview feedback generated (Score: ${feedback.score}/10)`);
          return feedback;
        },
        'conductInterview',
        { maxRetries: 1 }
      );

    } catch (error) {
      console.error('❌ Interview feedback error:', error);
      throw this.handleError(error, { 
        operation: 'conductInterview', 
        sessionId, 
        responseLength: response.length 
      });
    }
  }

  // Helper methods for parsing responses
  private parseDocumentAnalysis(content: string): {
    summary: string;
    keyPoints: string[];
    insights: string[];
    suggestedQuestions: string[];
  } {
    // Simple parsing - in production, this would be more sophisticated
    const lines = content.split('\n').filter(line => line.trim());
    
    return {
      summary: lines.find(line => line.toLowerCase().includes('summary')) || content.substring(0, 200),
      keyPoints: lines.filter(line => line.includes('•') || line.includes('-')).slice(0, 5),
      insights: lines.filter(line => line.toLowerCase().includes('insight')).slice(0, 3),
      suggestedQuestions: lines.filter(line => line.includes('?')).slice(0, 3)
    };
  }

  private parseQuizResponse(content: string, quizId: string, options: QuizOptions): Quiz {
    try {
      // Try to parse JSON response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          id: quizId,
          title: parsed.title || `${options.difficulty} Quiz`,
          questions: parsed.questions.map((q: any) => ({
            ...q,
            id: q.id || uuidv4()
          })),
          metadata: {
            difficulty: options.difficulty,
            estimatedTime: options.questionCount * 2, // 2 minutes per question
            topics: options.topics || []
          }
        };
      }
    } catch (error) {
      console.warn('Failed to parse JSON quiz response, using fallback');
    }

    // Fallback parsing
    return {
      id: quizId,
      title: `${options.difficulty} Quiz`,
      questions: [{
        id: uuidv4(),
        type: 'short-answer',
        question: content.substring(0, 200),
        correctAnswer: 'Generated from AI response',
        explanation: 'This question was generated from the AI response'
      }],
      metadata: {
        difficulty: options.difficulty,
        estimatedTime: options.questionCount * 2,
        topics: options.topics || []
      }
    };
  }

  private parseInterviewFeedback(content: string): InterviewFeedback {
    try {
      // Try to parse JSON response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          questionId: uuidv4(),
          score: parsed.score || 5,
          feedback: parsed.feedback || content,
          suggestions: parsed.suggestions || [],
          strengths: parsed.strengths || [],
          improvements: parsed.improvements || []
        };
      }
    } catch (error) {
      console.warn('Failed to parse JSON feedback response, using fallback');
    }

    // Fallback parsing
    return {
      questionId: uuidv4(),
      score: 5,
      feedback: content,
      suggestions: [],
      strengths: [],
      improvements: []
    };
  }

  // Get user-friendly error message (deprecated - use getErrorDisplayInfo instead)
  getErrorMessage(error: AgentError): string {
    return this.getErrorDisplayInfo(error).message;
  }
}

// Export singleton instance
export const directAgentService = new DirectAgentService();

// Export for testing
export { DirectAgentService, SessionManager };
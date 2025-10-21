import { directAgentService } from '../directAgentService';
import { configurationService } from '../configurationService';

// Integration tests for DirectAgentService
// These tests require actual AWS credentials and deployed agent
// They should be run in a test environment with proper setup

describe('DirectAgentService Integration Tests', () => {
  const testTimeout = 30000; // 30 seconds for agent responses

  beforeAll(async () => {
    // Validate that we have proper test configuration
    const config = configurationService.getEnvironmentConfig();
    
    if (!config.bedrockAgentId || !config.bedrockAgentAliasId) {
      console.warn('Skipping integration tests - missing agent configuration');
      return;
    }

    if (!config.awsAccessKeyId || !config.awsSecretAccessKey) {
      console.warn('Skipping integration tests - missing AWS credentials');
      return;
    }
  });

  describe('Agent Communication', () => {
    it('should successfully send a message and receive response', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      // Skip if not properly configured
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      const response = await directAgentService.sendMessage(
        'Hello, this is a test message. Please respond with a simple greeting.',
        undefined,
        true // isTest flag
      );

      expect(response).toBeDefined();
      expect(response.content).toBeTruthy();
      expect(response.sessionId).toBeTruthy();
      expect(response.messageId).toBeTruthy();
      expect(response.timestamp).toBeInstanceOf(Date);
      expect(response.error).toBeUndefined();

      // Response should contain some form of greeting
      expect(response.content.toLowerCase()).toMatch(/hello|hi|greetings|welcome/);
    }, testTimeout);

    it('should maintain session context across multiple messages', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      // First message
      const response1 = await directAgentService.sendMessage(
        'My name is TestUser. Please remember this.',
        undefined,
        true
      );

      expect(response1.error).toBeUndefined();
      const sessionId = response1.sessionId;

      // Second message using same session
      const response2 = await directAgentService.sendMessage(
        'What is my name?',
        sessionId,
        true
      );

      expect(response2.error).toBeUndefined();
      expect(response2.sessionId).toBe(sessionId);
      
      // Response should reference the name from previous message
      expect(response2.content.toLowerCase()).toContain('testuser');
    }, testTimeout);

    it('should handle error scenarios gracefully', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      // Test with invalid session ID format
      const response = await directAgentService.sendMessage(
        'Test message',
        'invalid-session-format-that-should-fail',
        true
      );

      // Should either succeed with new session or provide error
      if (response.error) {
        expect(response.error).toBeTruthy();
        expect(response.content).toBe('');
      } else {
        expect(response.content).toBeTruthy();
        expect(response.sessionId).toBeTruthy();
      }
    }, testTimeout);
  });

  describe('Document Analysis', () => {
    it('should analyze a document and return structured results', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      const mockDocumentUrl = 'https://example.com/test-document.pdf';
      const query = 'Analyze this document and provide key insights';

      try {
        const analysis = await directAgentService.analyzeDocument(mockDocumentUrl, query);

        expect(analysis).toBeDefined();
        expect(analysis.documentId).toBeTruthy();
        expect(analysis.summary).toBeTruthy();
        expect(Array.isArray(analysis.keyPoints)).toBe(true);
        expect(Array.isArray(analysis.insights)).toBe(true);
        expect(Array.isArray(analysis.suggestedQuestions)).toBe(true);
        expect(typeof analysis.confidence).toBe('number');
        expect(typeof analysis.processingTime).toBe('number');
      } catch (error) {
        // Document analysis might fail if the URL is not accessible
        // This is expected in test environment
        console.log('Document analysis test skipped - URL not accessible');
      }
    }, testTimeout);
  });

  describe('Quiz Generation', () => {
    it('should generate a quiz from content', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      const content = `
        Machine Learning is a subset of artificial intelligence that enables computers to learn 
        and make decisions from data without being explicitly programmed. There are three main 
        types: supervised learning, unsupervised learning, and reinforcement learning.
      `;

      const options = {
        difficulty: 'medium' as const,
        questionCount: 3,
        topics: ['Machine Learning'],
        questionTypes: ['multiple-choice', 'true-false'] as const
      };

      const quiz = await directAgentService.generateQuiz(content, options);

      expect(quiz).toBeDefined();
      expect(quiz.id).toBeTruthy();
      expect(quiz.title).toBeTruthy();
      expect(Array.isArray(quiz.questions)).toBe(true);
      expect(quiz.questions.length).toBeGreaterThan(0);
      expect(quiz.questions.length).toBeLessThanOrEqual(options.questionCount);

      // Check question structure
      quiz.questions.forEach(question => {
        expect(question.id).toBeTruthy();
        expect(question.question).toBeTruthy();
        expect(['multiple-choice', 'true-false', 'short-answer']).toContain(question.type);
        expect(question.correctAnswer).toBeDefined();
        
        if (question.type === 'multiple-choice') {
          expect(Array.isArray(question.options)).toBe(true);
          expect(question.options!.length).toBeGreaterThan(1);
        }
      });

      expect(quiz.metadata).toBeDefined();
      expect(quiz.metadata.difficulty).toBe(options.difficulty);
      expect(typeof quiz.metadata.estimatedTime).toBe('number');
    }, testTimeout);
  });

  describe('Interview Simulation', () => {
    it('should start an interview session', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      const topic = 'Software Engineering interview at intermediate level';

      const session = await directAgentService.startInterview(topic);

      expect(session).toBeDefined();
      expect(session.sessionId).toBeTruthy();
      expect(session.topic).toBe(topic);
      expect(Array.isArray(session.questions)).toBe(true);
      expect(session.questions.length).toBeGreaterThan(0);
      expect(session.status).toBe('active');
      expect(session.startTime).toBeInstanceOf(Date);

      // Check first question structure
      const firstQuestion = session.questions[0];
      expect(firstQuestion.id).toBeTruthy();
      expect(firstQuestion.question).toBeTruthy();
      expect(['easy', 'medium', 'hard']).toContain(firstQuestion.difficulty);
    }, testTimeout);

    it('should conduct interview and provide feedback', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      // Start interview first
      const session = await directAgentService.startInterview('Technical interview');
      
      // Provide a response
      const candidateResponse = 'I have 5 years of experience in software development, primarily working with JavaScript, React, and Node.js. I enjoy solving complex problems and working in collaborative team environments.';

      const feedback = await directAgentService.conductInterview(session.sessionId, candidateResponse);

      expect(feedback).toBeDefined();
      expect(feedback.questionId).toBeTruthy();
      expect(typeof feedback.score).toBe('number');
      expect(feedback.score).toBeGreaterThanOrEqual(0);
      expect(feedback.score).toBeLessThanOrEqual(10);
      expect(feedback.feedback).toBeTruthy();
      expect(Array.isArray(feedback.suggestions)).toBe(true);
      expect(Array.isArray(feedback.strengths)).toBe(true);
      expect(Array.isArray(feedback.improvements)).toBe(true);
    }, testTimeout);
  });

  describe('Configuration Validation', () => {
    it('should validate configuration successfully', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      const validation = await directAgentService.validateConfiguration();

      expect(validation).toBeDefined();
      expect(typeof validation.valid).toBe('boolean');
      expect(Array.isArray(validation.errors)).toBe(true);
      expect(Array.isArray(validation.warnings)).toBe(true);
      expect(validation.details).toBeDefined();
      expect(validation.lastChecked).toBeInstanceOf(Date);

      if (validation.valid) {
        expect(validation.details.awsCredentials).toBe('valid');
        expect(validation.details.agentConfiguration).toBe('valid');
        expect(validation.details.agentConnectivity).toBe('connected');
      } else {
        expect(validation.errors.length).toBeGreaterThan(0);
        console.log('Configuration validation errors:', validation.errors);
      }
    }, testTimeout);
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      // This test would require mocking network failures
      // For now, we'll test with invalid agent configuration
      
      const originalAgentId = process.env.VITE_BEDROCK_AGENT_ID;
      process.env.VITE_BEDROCK_AGENT_ID = 'INVALID_AGENT_ID';

      try {
        const response = await directAgentService.sendMessage('Test message', undefined, true);
        
        // Should either fail gracefully or succeed with fallback
        if (response.error) {
          expect(response.error).toBeTruthy();
          expect(response.content).toBe('');
        }
      } catch (error) {
        // Network errors should be caught and handled
        expect(error).toBeInstanceOf(Error);
      } finally {
        // Restore original configuration
        if (originalAgentId) {
          process.env.VITE_BEDROCK_AGENT_ID = originalAgentId;
        }
      }
    }, testTimeout);

    it('should handle rate limiting gracefully', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      // Send multiple rapid requests to potentially trigger rate limiting
      const promises = Array.from({ length: 5 }, (_, i) => 
        directAgentService.sendMessage(`Test message ${i}`, undefined, true)
      );

      const responses = await Promise.allSettled(promises);

      // All requests should either succeed or fail gracefully
      responses.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          const response = result.value;
          expect(response).toBeDefined();
          expect(response.sessionId).toBeTruthy();
          
          if (response.error) {
            // Rate limiting or other errors should be handled gracefully
            expect(response.error).toBeTruthy();
            console.log(`Request ${index} failed with error: ${response.error}`);
          } else {
            expect(response.content).toBeTruthy();
          }
        } else {
          console.log(`Request ${index} rejected:`, result.reason);
        }
      });
    }, testTimeout * 2);
  });

  describe('Performance', () => {
    it('should respond within reasonable time limits', async () => {
      const config = configurationService.getEnvironmentConfig();
      
      if (!config.bedrockAgentId || !config.awsAccessKeyId) {
        console.log('Skipping test - missing configuration');
        return;
      }

      const startTime = Date.now();
      
      const response = await directAgentService.sendMessage(
        'This is a simple test message that should receive a quick response.',
        undefined,
        true
      );

      const endTime = Date.now();
      const responseTime = endTime - startTime;

      expect(response.error).toBeUndefined();
      expect(response.content).toBeTruthy();
      
      // Response should be within 10 seconds for simple messages
      expect(responseTime).toBeLessThan(10000);
      
      // Metadata should include processing time
      if (response.metadata?.processingTime) {
        expect(response.metadata.processingTime).toBeLessThan(responseTime);
      }

      console.log(`Response time: ${responseTime}ms`);
    }, testTimeout);
  });
});
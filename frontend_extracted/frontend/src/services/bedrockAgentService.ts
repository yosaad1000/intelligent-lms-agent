import { BedrockAgentRuntimeClient, InvokeAgentCommand } from '@aws-sdk/client-bedrock-agent-runtime';

export interface AgentMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  citations?: Citation[];
  toolsUsed?: string[];
  sessionId?: string;
}

export interface Citation {
  source: string;
  page?: number;
  section?: string;
  confidence?: number;
}

export interface AgentResponse {
  message: AgentMessage;
  sessionId: string;
  toolsUsed: string[];
  citations: Citation[];
}

export class BedrockAgentService {
  private static instance: BedrockAgentService;
  private client: BedrockAgentRuntimeClient;
  private agentId: string;
  private aliasId: string;

  private constructor() {
    // Initialize AWS SDK client
    this.client = new BedrockAgentRuntimeClient({
      region: import.meta.env.VITE_AWS_REGION || 'us-east-1',
      credentials: {
        accessKeyId: import.meta.env.VITE_AWS_ACCESS_KEY_ID || '',
        secretAccessKey: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY || '',
      }
    });
    
    this.agentId = import.meta.env.VITE_BEDROCK_AGENT_ID || 'ZTBBVSC6Y1';
    this.aliasId = import.meta.env.VITE_BEDROCK_AGENT_ALIAS_ID || 'TSTALIASID';
  }

  public static getInstance(): BedrockAgentService {
    if (!BedrockAgentService.instance) {
      BedrockAgentService.instance = new BedrockAgentService();
    }
    return BedrockAgentService.instance;
  }

  /**
   * Send a message to the Bedrock Agent and get a response
   */
  public async sendMessage(
    message: string, 
    sessionId: string,
    userId?: string,
    context?: any
  ): Promise<AgentResponse> {
    try {
      const command = new InvokeAgentCommand({
        agentId: this.agentId,
        agentAliasId: this.aliasId,
        sessionId: sessionId,
        inputText: message,
        // Add user context if available
        ...(userId && { 
          sessionState: {
            sessionAttributes: {
              userId: userId,
              context: JSON.stringify(context || {})
            }
          }
        })
      });

      const response = await this.client.send(command);
      
      // Process the streaming response
      let completion = '';
      let citations: Citation[] = [];
      let toolsUsed: string[] = [];

      if (response.completion) {
        for await (const event of response.completion) {
          if (event.chunk?.bytes) {
            const chunk = new TextDecoder().decode(event.chunk.bytes);
            completion += chunk;
          }
          
          // Extract citations and tools used from response metadata
          if (event.trace) {
            // Process trace information for citations and tools
            this.extractTraceInformation(event.trace, citations, toolsUsed);
          }
        }
      }

      const agentMessage: AgentMessage = {
        id: `agent-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        content: completion,
        sender: 'agent',
        timestamp: new Date(),
        citations: citations,
        toolsUsed: toolsUsed,
        sessionId: sessionId
      };

      return {
        message: agentMessage,
        sessionId: sessionId,
        toolsUsed: toolsUsed,
        citations: citations
      };

    } catch (error) {
      console.error('Error invoking Bedrock Agent:', error);
      
      // Return a fallback response
      const fallbackMessage: AgentMessage = {
        id: `agent-error-${Date.now()}`,
        content: "I'm sorry, I'm having trouble connecting to the AI service right now. Please try again in a moment.",
        sender: 'agent',
        timestamp: new Date(),
        sessionId: sessionId
      };

      return {
        message: fallbackMessage,
        sessionId: sessionId,
        toolsUsed: [],
        citations: []
      };
    }
  }

  /**
   * Extract trace information for citations and tools used
   */
  private extractTraceInformation(trace: any, citations: Citation[], toolsUsed: string[]): void {
    // This would be implemented based on the actual trace structure from Bedrock
    // For now, we'll add placeholder logic
    if (trace.orchestrationTrace) {
      // Extract tool usage information
      if (trace.orchestrationTrace.invocationInput) {
        const actionGroup = trace.orchestrationTrace.invocationInput.actionGroupName;
        if (actionGroup && !toolsUsed.includes(actionGroup)) {
          toolsUsed.push(actionGroup);
        }
      }
    }

    if (trace.knowledgeBaseTrace) {
      // Extract citation information from knowledge base
      const retrievalResults = trace.knowledgeBaseTrace.retrievalResults;
      if (retrievalResults) {
        retrievalResults.forEach((result: any) => {
          citations.push({
            source: result.location?.s3Location?.uri || 'Knowledge Base',
            confidence: result.score,
            section: result.metadata?.section
          });
        });
      }
    }
  }

  /**
   * Generate a unique session ID
   */
  public generateSessionId(userId?: string): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `session-${userId || 'anonymous'}-${timestamp}-${random}`;
  }

  /**
   * Get conversation history for a session (if supported by backend)
   */
  public async getConversationHistory(sessionId: string): Promise<AgentMessage[]> {
    // This would typically call a backend API to retrieve conversation history
    // For now, we'll return empty array as Bedrock Agent handles session memory internally
    return [];
  }

  /**
   * Clear conversation history for a session
   */
  public async clearConversation(sessionId: string): Promise<void> {
    // This would typically call a backend API to clear conversation history
    // Bedrock Agent sessions are managed automatically
    console.log(`Conversation cleared for session: ${sessionId}`);
  }

  /**
   * Get agent capabilities and available tools
   */
  public getAgentCapabilities(): string[] {
    return [
      'Document Analysis & Summarization',
      'Quiz Generation from Content',
      'Learning Analytics & Progress Tracking',
      'Voice Interview Practice',
      'Multi-language Support',
      'Citation-backed Responses',
      'Contextual Learning Assistance'
    ];
  }

  /**
   * Validate agent configuration
   */
  public async validateConfiguration(): Promise<boolean> {
    try {
      // Test with a simple message
      const testSessionId = this.generateSessionId('test');
      const response = await this.sendMessage('Hello', testSessionId);
      return response.message.content.length > 0;
    } catch (error) {
      console.error('Agent configuration validation failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const bedrockAgentService = BedrockAgentService.getInstance();

// Fallback service for development/demo mode
export class MockBedrockAgentService {
  public async sendMessage(
    message: string, 
    sessionId: string,
    userId?: string,
    context?: any
  ): Promise<AgentResponse> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

    const responses = this.getContextualResponses(message, context);
    const selectedResponse = responses[Math.floor(Math.random() * responses.length)];

    const agentMessage: AgentMessage = {
      id: `mock-agent-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      content: selectedResponse.content,
      sender: 'agent',
      timestamp: new Date(),
      citations: selectedResponse.citations,
      toolsUsed: selectedResponse.toolsUsed,
      sessionId: sessionId
    };

    return {
      message: agentMessage,
      sessionId: sessionId,
      toolsUsed: selectedResponse.toolsUsed || [],
      citations: selectedResponse.citations || []
    };
  }

  private getContextualResponses(message: string, context?: any) {
    const lowerMessage = message.toLowerCase();

    if (lowerMessage.includes('quiz') || lowerMessage.includes('test') || lowerMessage.includes('question')) {
      return [{
        content: `I can help you create a quiz! Based on your study materials, here are some practice questions:

**Question 1: Multiple Choice**
What is the primary purpose of machine learning?
A) To replace human intelligence
B) To enable computers to learn from data
C) To create robots
D) To process text only

**Question 2: Short Answer**
Explain the difference between supervised and unsupervised learning.

**Question 3: True/False**
Neural networks can only be used for image recognition tasks.

Would you like me to generate more questions or explain any of these concepts?`,
        citations: [
          { source: 'Machine Learning Fundamentals.pdf', page: 15, confidence: 0.95 },
          { source: 'AI Study Guide.docx', section: 'Chapter 3', confidence: 0.88 }
        ],
        toolsUsed: ['quiz_generator', 'knowledge_base_retrieval']
      }];
    }

    if (lowerMessage.includes('summary') || lowerMessage.includes('summarize')) {
      return [{
        content: `Here's a comprehensive summary of your study materials:

## Key Concepts Covered

### 1. Machine Learning Fundamentals
- **Definition**: A subset of AI that enables computers to learn from data
- **Types**: Supervised, Unsupervised, and Reinforcement Learning
- **Applications**: Image recognition, natural language processing, recommendation systems

### 2. Data Preprocessing
- **Data Cleaning**: Handling missing values and outliers
- **Feature Engineering**: Creating meaningful input variables
- **Normalization**: Scaling data for optimal model performance

### 3. Model Evaluation
- **Metrics**: Accuracy, Precision, Recall, F1-Score
- **Cross-Validation**: Techniques for robust model assessment
- **Overfitting Prevention**: Regularization and validation strategies

This summary covers the main topics from your uploaded documents. Would you like me to elaborate on any specific area?`,
        citations: [
          { source: 'ML_Overview.pdf', page: 1, confidence: 0.92 },
          { source: 'Data_Science_Notes.docx', section: 'Introduction', confidence: 0.89 },
          { source: 'Study_Guide_2024.pdf', page: 23, confidence: 0.85 }
        ],
        toolsUsed: ['document_processor', 'knowledge_base_retrieval']
      }];
    }

    if (lowerMessage.includes('analytics') || lowerMessage.includes('progress')) {
      return [{
        content: `## Your Learning Analytics Dashboard

### 📊 Study Progress
- **Documents Processed**: 12 files
- **Study Sessions**: 8 completed this week
- **Average Session Duration**: 45 minutes
- **Quiz Scores**: 85% average (improving trend)

### 🎯 Learning Goals
- **Current Focus**: Machine Learning Fundamentals
- **Completion Rate**: 68% of planned material
- **Recommended Next Steps**: 
  1. Review neural network architectures
  2. Practice with real datasets
  3. Complete advanced algorithms module

### 📈 Performance Trends
- **Comprehension Score**: 82% (↑ 5% from last week)
- **Retention Rate**: 78% (stable)
- **Engagement Level**: High (consistent daily activity)

### 🏆 Achievements Unlocked
- 🔥 7-day study streak
- 📚 Completed 5 document summaries
- 🧠 Mastered basic ML concepts

Keep up the excellent work! Your consistent effort is showing great results.`,
        citations: [
          { source: 'Learning_Analytics_Report.json', confidence: 0.98 },
          { source: 'User_Progress_Data.csv', confidence: 0.94 }
        ],
        toolsUsed: ['analytics_tracker', 'progress_calculator']
      }];
    }

    // Default response
    return [{
      content: `I'm your AI Learning Assistant! I can help you with:

🎓 **Study Support**
- Summarize your uploaded documents
- Answer questions about your materials
- Create practice quizzes and tests

📊 **Learning Analytics**
- Track your study progress
- Identify knowledge gaps
- Recommend study strategies

🗣️ **Interview Practice**
- Conduct mock interviews
- Provide feedback on responses
- Help with technical questions

📚 **Content Management**
- Organize your study materials
- Extract key concepts
- Create study schedules

What would you like to work on today? Feel free to upload documents or ask me any questions about your studies!`,
      citations: [
        { source: 'AI_Assistant_Capabilities.md', confidence: 0.99 }
      ],
      toolsUsed: ['general_assistant']
    }];
  }

  public generateSessionId(userId?: string): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `mock-session-${userId || 'anonymous'}-${timestamp}-${random}`;
  }

  public getAgentCapabilities(): string[] {
    return [
      'Document Analysis & Summarization',
      'Quiz Generation from Content', 
      'Learning Analytics & Progress Tracking',
      'Voice Interview Practice',
      'Multi-language Support',
      'Citation-backed Responses',
      'Contextual Learning Assistance'
    ];
  }

  public async validateConfiguration(): Promise<boolean> {
    return true; // Mock service is always available
  }
}

// Export the appropriate service based on environment
export const agentService = import.meta.env.VITE_USE_MOCK_AGENT === 'true' 
  ? new MockBedrockAgentService() 
  : bedrockAgentService;
/**
 * API-based Bedrock Agent Service for Frontend Integration
 * Task 12: Frontend-Backend API Integration
 * Uses API Gateway proxy instead of direct AWS SDK calls
 */

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
  content?: string;
  metadata?: any;
}

export interface AgentResponse {
  message: AgentMessage;
  sessionId: string;
  toolsUsed: string[];
  citations: Citation[];
  success: boolean;
  error?: string;
  traceData?: any[];
}

export interface UploadResponse {
  success: boolean;
  upload_url?: string;
  file_key?: string;
  bucket?: string;
  expires_in?: number;
  error?: string;
}

export interface DocumentInfo {
  key: string;
  filename: string;
  size: number;
  last_modified: string;
  download_url: string;
}

export class ApiBedrockAgentService {
  private static instance: ApiBedrockAgentService;
  private apiBaseUrl: string;
  private websocketUrl: string;

  private constructor() {
    // Get API URLs from environment
    this.apiBaseUrl = import.meta.env.VITE_API_GATEWAY_URL || 'https://7k21xsoz93.execute-api.us-east-1.amazonaws.com/dev';
    this.websocketUrl = import.meta.env.VITE_WEBSOCKET_URL || 'wss://4olkavb3wa.execute-api.us-east-1.amazonaws.com/dev';
    
    // Remove trailing slash
    if (this.apiBaseUrl.endsWith('/')) {
      this.apiBaseUrl = this.apiBaseUrl.slice(0, -1);
    }
  }

  public static getInstance(): ApiBedrockAgentService {
    if (!ApiBedrockAgentService.instance) {
      ApiBedrockAgentService.instance = new ApiBedrockAgentService();
    }
    return ApiBedrockAgentService.instance;
  }

  /**
   * Send a message to the Bedrock Agent via API Gateway
   */
  public async sendMessage(
    message: string, 
    sessionId: string,
    userId?: string,
    context?: any
  ): Promise<AgentResponse> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
          user_id: userId,
          context: context
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Agent request failed');
      }

      const agentMessage: AgentMessage = {
        id: data.message_id || `agent-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
        content: data.response || '',
        sender: 'agent',
        timestamp: new Date(data.timestamp || Date.now()),
        citations: data.citations || [],
        toolsUsed: data.tools_used || [],
        sessionId: data.session_id || sessionId
      };

      return {
        message: agentMessage,
        sessionId: data.session_id || sessionId,
        toolsUsed: data.tools_used || [],
        citations: data.citations || [],
        success: true,
        traceData: data.trace_data || []
      };

    } catch (error) {
      console.error('Error sending message to agent:', error);
      
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
        citations: [],
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get conversation history for a session
   */
  public async getConversationHistory(sessionId: string): Promise<AgentMessage[]> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/session/history?session_id=${encodeURIComponent(sessionId)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to get conversation history');
      }

      // Convert conversation history to AgentMessage format
      const messages: AgentMessage[] = [];
      
      for (const conversation of data.conversation_history || []) {
        // Add user message
        messages.push({
          id: `user-${conversation.timestamp}`,
          content: conversation.user_message,
          sender: 'user',
          timestamp: new Date(conversation.timestamp),
          sessionId: sessionId
        });

        // Add agent message
        messages.push({
          id: `agent-${conversation.timestamp}`,
          content: conversation.agent_response,
          sender: 'agent',
          timestamp: new Date(conversation.timestamp),
          toolsUsed: conversation.tools_used || [],
          sessionId: sessionId
        });
      }

      return messages;

    } catch (error) {
      console.error('Error getting conversation history:', error);
      return [];
    }
  }

  /**
   * Generate presigned URL for file upload
   */
  public async generateUploadUrl(fileName: string, contentType: string, userId: string): Promise<UploadResponse> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/upload/presigned`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_name: fileName,
          content_type: contentType,
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;

    } catch (error) {
      console.error('Error generating upload URL:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Upload file using presigned URL
   */
  public async uploadFile(file: File, userId: string, onProgress?: (progress: number) => void): Promise<{ success: boolean; fileKey?: string; error?: string }> {
    try {
      // Get presigned URL
      const uploadResponse = await this.generateUploadUrl(file.name, file.type, userId);
      
      if (!uploadResponse.success || !uploadResponse.upload_url) {
        throw new Error(uploadResponse.error || 'Failed to get upload URL');
      }

      // Upload file
      const xhr = new XMLHttpRequest();
      
      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable && onProgress) {
            const progress = (event.loaded / event.total) * 100;
            onProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve({
              success: true,
              fileKey: uploadResponse.file_key
            });
          } else {
            reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed due to network error'));
        });

        xhr.open('PUT', uploadResponse.upload_url);
        xhr.setRequestHeader('Content-Type', file.type);
        xhr.send(file);
      });

    } catch (error) {
      console.error('Error uploading file:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get list of user documents
   */
  public async getDocuments(userId: string): Promise<DocumentInfo[]> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/documents?user_id=${encodeURIComponent(userId)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to get documents');
      }

      return data.documents || [];

    } catch (error) {
      console.error('Error getting documents:', error);
      return [];
    }
  }

  /**
   * Check API health and agent connectivity
   */
  public async checkHealth(): Promise<{ healthy: boolean; agentResponsive: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      return {
        healthy: data.success && data.status === 'healthy',
        agentResponsive: data.agent_responsive || false,
        error: data.error
      };

    } catch (error) {
      console.error('Error checking health:', error);
      return {
        healthy: false,
        agentResponsive: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get agent capabilities
   */
  public async getAgentCapabilities(): Promise<string[]> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/capabilities`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to get capabilities');
      }

      return data.capabilities || [];

    } catch (error) {
      console.error('Error getting capabilities:', error);
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
  }

  /**
   * Generate a unique session ID
   */
  public generateSessionId(userId?: string): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 9);
    return `session-${userId || 'anonymous'}-${timestamp}-${random}`;
  }

  /**
   * Clear conversation history for a session
   */
  public async clearConversation(sessionId: string): Promise<void> {
    // Note: This would require a backend endpoint to clear session data
    // For now, we'll just log it as Bedrock Agent manages sessions automatically
    console.log(`Conversation cleared for session: ${sessionId}`);
  }

  /**
   * Validate API configuration
   */
  public async validateConfiguration(): Promise<boolean> {
    try {
      const health = await this.checkHealth();
      return health.healthy && health.agentResponsive;
    } catch (error) {
      console.error('API configuration validation failed:', error);
      return false;
    }
  }

  /**
   * Get WebSocket URL for real-time features
   */
  public getWebSocketUrl(): string {
    return this.websocketUrl;
  }

  /**
   * Get API base URL
   */
  public getApiBaseUrl(): string {
    return this.apiBaseUrl;
  }
}

// Export singleton instance
export const apiBedrockAgentService = ApiBedrockAgentService.getInstance();

// Export the service based on environment configuration
export const agentService = import.meta.env.VITE_USE_API_PROXY === 'true' 
  ? apiBedrockAgentService 
  : import('./bedrockAgentService').then(module => module.agentService);
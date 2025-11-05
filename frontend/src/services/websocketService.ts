/**
 * WebSocket Service for Real-time Chat
 * Task 12: Frontend-Backend API Integration
 */

export interface WebSocketMessage {
  type: 'connection_established' | 'typing' | 'partial_response' | 'final_response' | 'error' | 'pong';
  message?: string;
  content?: string;
  session_id?: string;
  citations?: any[];
  tools_used?: string[];
  timestamp?: string;
  connection_id?: string;
  error?: string;
}

export interface WebSocketConfig {
  url: string;
  userId?: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export class WebSocketService {
  private static instance: WebSocketService;
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private isConnected = false;

  private constructor(config: WebSocketConfig) {
    this.config = config;
    this.maxReconnectAttempts = config.reconnectAttempts || 5;
    this.reconnectDelay = config.reconnectDelay || 1000;
  }

  public static getInstance(config?: WebSocketConfig): WebSocketService {
    if (!WebSocketService.instance && config) {
      WebSocketService.instance = new WebSocketService(config);
    }
    return WebSocketService.instance;
  }

  /**
   * Connect to WebSocket server
   */
  public async connect(): Promise<boolean> {
    if (this.isConnecting || this.isConnected) {
      return this.isConnected;
    }

    this.isConnecting = true;

    try {
      const wsUrl = this.buildWebSocketUrl();
      console.log('Connecting to WebSocket:', wsUrl);

      this.ws = new WebSocket(wsUrl);

      return new Promise((resolve, reject) => {
        if (!this.ws) {
          reject(new Error('WebSocket not initialized'));
          return;
        }

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          this.isConnecting = false;
          
          // Attempt to reconnect if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

        // Timeout for connection
        setTimeout(() => {
          if (this.isConnecting) {
            this.isConnecting = false;
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);
      });

    } catch (error) {
      this.isConnecting = false;
      console.error('WebSocket connection failed:', error);
      return false;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
  }

  /**
   * Send a chat message
   */
  public sendMessage(message: string, sessionId: string, userId?: string): boolean {
    if (!this.isConnected || !this.ws) {
      console.error('WebSocket not connected');
      return false;
    }

    try {
      const payload = {
        action: 'sendMessage',
        message: message,
        session_id: sessionId,
        user_id: userId || this.config.userId || 'anonymous'
      };

      this.ws.send(JSON.stringify(payload));
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  /**
   * Send a ping message
   */
  public ping(): boolean {
    if (!this.isConnected || !this.ws) {
      return false;
    }

    try {
      const payload = {
        action: 'ping'
      };

      this.ws.send(JSON.stringify(payload));
      return true;
    } catch (error) {
      console.error('Failed to send ping:', error);
      return false;
    }
  }

  /**
   * Register a message handler
   */
  public onMessage(type: string, handler: (message: WebSocketMessage) => void): void {
    this.messageHandlers.set(type, handler);
  }

  /**
   * Remove a message handler
   */
  public offMessage(type: string): void {
    this.messageHandlers.delete(type);
  }

  /**
   * Check if WebSocket is connected
   */
  public isWebSocketConnected(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection status
   */
  public getConnectionStatus(): 'connecting' | 'connected' | 'disconnected' {
    if (this.isConnecting) return 'connecting';
    if (this.isConnected) return 'connected';
    return 'disconnected';
  }

  private buildWebSocketUrl(): string {
    const baseUrl = this.config.url;
    const params = new URLSearchParams();
    
    if (this.config.userId) {
      params.append('user_id', this.config.userId);
    }

    return params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
  }

  private handleMessage(message: WebSocketMessage): void {
    console.log('WebSocket message received:', message.type, message);

    // Call specific handler if registered
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    }

    // Call general message handler if registered
    const generalHandler = this.messageHandlers.get('*');
    if (generalHandler) {
      generalHandler(message);
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff

    console.log(`Scheduling WebSocket reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);

    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.connect().catch(error => {
          console.error('WebSocket reconnect failed:', error);
        });
      }
    }, delay);
  }
}

// Export a factory function for creating WebSocket service instances
export const createWebSocketService = (config: WebSocketConfig): WebSocketService => {
  return WebSocketService.getInstance(config);
};

// Export default instance getter
export const getWebSocketService = (): WebSocketService | null => {
  return WebSocketService.instance || null;
};
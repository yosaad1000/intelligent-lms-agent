# API Integration Guide

This document describes how the frontend integrates with various APIs and services in the LMS AI Agent system.

## Architecture Overview

The frontend uses a multi-layered API integration approach:

```
Frontend Components
        ↓
Service Layer (src/services/)
        ↓
API Clients & SDKs
        ↓
External Services (AWS, Supabase, Google)
```

## Core API Services

### 1. AWS Bedrock Agent Integration

#### Direct Agent Service (`directAgentService.ts`)

**Purpose**: Direct communication with AWS Bedrock Agent Runtime API.

```typescript
import { BedrockAgentRuntimeClient, InvokeAgentCommand } from '@aws-sdk/client-bedrock-agent-runtime'

class DirectAgentService {
  private client: BedrockAgentRuntimeClient
  
  constructor() {
    this.client = new BedrockAgentRuntimeClient({
      region: import.meta.env.VITE_AWS_REGION,
      credentials: {
        accessKeyId: import.meta.env.VITE_AWS_ACCESS_KEY_ID,
        secretAccessKey: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY,
      }
    })
  }

  async invokeAgent(message: string, sessionId: string): Promise<string> {
    const command = new InvokeAgentCommand({
      agentId: import.meta.env.VITE_BEDROCK_AGENT_ID,
      agentAliasId: import.meta.env.VITE_BEDROCK_AGENT_ALIAS_ID,
      sessionId,
      inputText: message,
    })

    const response = await this.client.send(command)
    return this.processStreamingResponse(response.completion)
  }
}
```

**Features**:
- Streaming response handling
- Session management
- Error handling and retry logic
- Response parsing and formatting

#### API Gateway Bedrock Service (`apiBedrockAgentService.ts`)

**Purpose**: Communication through API Gateway for production environments.

```typescript
class APIBedrockAgentService {
  private baseURL: string

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL
  }

  async invokeAgent(message: string, sessionId: string): Promise<AgentResponse> {
    const response = await fetch(`${this.baseURL}/agent/invoke`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await this.getAuthToken()}`,
      },
      body: JSON.stringify({
        message,
        sessionId,
        userId: await this.getCurrentUserId(),
      }),
    })

    if (!response.ok) {
      throw new APIError(`Agent invocation failed: ${response.statusText}`)
    }

    return response.json()
  }
}
```

### 2. Document Processing Service (`documentService.ts`)

**Purpose**: Handle document upload, processing, and management.

```typescript
class DocumentService {
  async uploadDocument(file: File, metadata: DocumentMetadata): Promise<Document> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('metadata', JSON.stringify(metadata))

    const response = await fetch(`${this.baseURL}/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${await this.getAuthToken()}`,
      },
      body: formData,
    })

    return response.json()
  }

  async processDocument(documentId: string): Promise<ProcessingResult> {
    const response = await fetch(`${this.baseURL}/documents/${documentId}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await this.getAuthToken()}`,
      },
    })

    return response.json()
  }

  async getDocuments(filters?: DocumentFilters): Promise<Document[]> {
    const queryParams = new URLSearchParams(filters as any)
    const response = await fetch(`${this.baseURL}/documents?${queryParams}`)
    
    return response.json()
  }
}
```

### 3. Analytics Service (`analyticsService.ts`)

**Purpose**: Learning analytics and progress tracking.

```typescript
class AnalyticsService {
  async getStudentAnalytics(studentId: string, timeRange: TimeRange): Promise<StudentAnalytics> {
    const response = await fetch(`${this.baseURL}/analytics/student/${studentId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${await this.getAuthToken()}`,
      },
    })

    return response.json()
  }

  async trackEvent(event: AnalyticsEvent): Promise<void> {
    await fetch(`${this.baseURL}/analytics/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await this.getAuthToken()}`,
      },
      body: JSON.stringify(event),
    })
  }

  async generateReport(reportConfig: ReportConfig): Promise<Report> {
    const response = await fetch(`${this.baseURL}/analytics/reports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await this.getAuthToken()}`,
      },
      body: JSON.stringify(reportConfig),
    })

    return response.json()
  }
}
```

## Authentication Integration

### Supabase Authentication

```typescript
import { createClient } from '@supabase/supabase-js'

class AuthService {
  private supabase = createClient(
    import.meta.env.VITE_SUPABASE_URL,
    import.meta.env.VITE_SUPABASE_ANON_KEY
  )

  async signIn(email: string, password: string): Promise<AuthResult> {
    const { data, error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) throw new AuthError(error.message)
    return data
  }

  async signUp(email: string, password: string, metadata: UserMetadata): Promise<AuthResult> {
    const { data, error } = await this.supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata,
      },
    })

    if (error) throw new AuthError(error.message)
    return data
  }

  async getSession(): Promise<Session | null> {
    const { data: { session } } = await this.supabase.auth.getSession()
    return session
  }

  async signOut(): Promise<void> {
    await this.supabase.auth.signOut()
  }
}
```

## Real-time Communication

### WebSocket Service (`websocketService.ts`)

**Purpose**: Real-time features like chat, notifications, and live updates.

```typescript
class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  connect(userId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${import.meta.env.VITE_WS_URL}?userId=${userId}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        resolve()
      }

      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        this.handleMessage(message)
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.handleReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(error)
      }
    })
  }

  sendMessage(message: WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        this.connect(this.currentUserId)
      }, 1000 * Math.pow(2, this.reconnectAttempts))
    }
  }
}
```

## Google Services Integration

### Google Drive Service (`googleDriveService.ts`)

```typescript
class GoogleDriveService {
  private gapi: any

  async initialize(): Promise<void> {
    await new Promise((resolve) => {
      gapi.load('client:auth2', resolve)
    })

    await gapi.client.init({
      apiKey: import.meta.env.VITE_GOOGLE_API_KEY,
      clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'],
      scope: 'https://www.googleapis.com/auth/drive.readonly',
    })
  }

  async listFiles(query?: string): Promise<GoogleDriveFile[]> {
    const response = await gapi.client.drive.files.list({
      q: query,
      fields: 'files(id,name,mimeType,modifiedTime)',
    })

    return response.result.files
  }

  async downloadFile(fileId: string): Promise<Blob> {
    const response = await gapi.client.drive.files.get({
      fileId,
      alt: 'media',
    })

    return new Blob([response.body])
  }
}
```

## Error Handling

### API Error Classes

```typescript
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export class AuthError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'AuthError'
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'NetworkError'
  }
}
```

### Error Handling Service (`errorHandlingService.ts`)

```typescript
class ErrorHandlingService {
  handleAPIError(error: unknown): APIError {
    if (error instanceof APIError) {
      return error
    }

    if (error instanceof Response) {
      return new APIError(
        `HTTP ${error.status}: ${error.statusText}`,
        error.status
      )
    }

    if (error instanceof Error) {
      return new APIError(error.message)
    }

    return new APIError('Unknown API error occurred')
  }

  async retryOperation<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: Error

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error as Error
        
        if (attempt === maxRetries) {
          throw lastError
        }

        await new Promise(resolve => setTimeout(resolve, delay * attempt))
      }
    }

    throw lastError!
  }
}
```

## Performance Optimization

### Caching Strategy

```typescript
class CacheService {
  private cache = new Map<string, CacheEntry>()
  private readonly TTL = 5 * 60 * 1000 // 5 minutes

  set<T>(key: string, value: T, ttl: number = this.TTL): void {
    this.cache.set(key, {
      value,
      expiry: Date.now() + ttl,
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    
    if (!entry) return null
    
    if (Date.now() > entry.expiry) {
      this.cache.delete(key)
      return null
    }

    return entry.value as T
  }

  clear(): void {
    this.cache.clear()
  }
}
```

### Request Deduplication

```typescript
class RequestDeduplicator {
  private pendingRequests = new Map<string, Promise<any>>()

  async deduplicate<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key)!
    }

    const promise = requestFn().finally(() => {
      this.pendingRequests.delete(key)
    })

    this.pendingRequests.set(key, promise)
    return promise
  }
}
```

## Development and Testing

### Mock Services

For development and testing, mock services are provided:

```typescript
class MockBedrockAgentService implements BedrockAgentService {
  async invokeAgent(message: string, sessionId: string): Promise<string> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Return mock response based on message content
    return this.generateMockResponse(message)
  }

  private generateMockResponse(message: string): string {
    const responses = {
      'hello': 'Hello! How can I help you with your studies today?',
      'quiz': 'I can help you create a quiz. What topic would you like to focus on?',
      'summary': 'Here\'s a summary of the document you uploaded...',
    }

    const key = Object.keys(responses).find(k => 
      message.toLowerCase().includes(k)
    )

    return key ? responses[key] : 'I understand. Let me help you with that.'
  }
}
```

### API Testing Utilities

```typescript
export const apiTestUtils = {
  mockFetch: (response: any, status: number = 200) => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: status >= 200 && status < 300,
        status,
        json: () => Promise.resolve(response),
      })
    ) as jest.Mock
  },

  expectAPICall: (url: string, options?: RequestInit) => {
    expect(fetch).toHaveBeenCalledWith(url, expect.objectContaining(options || {}))
  },

  createMockUser: (): User => ({
    id: 'test-user-id',
    email: 'test@example.com',
    role: 'student',
    name: 'Test User',
  }),
}
```

## Environment Configuration

### Environment Variables

```env
# AWS Configuration
VITE_AWS_REGION=us-east-1
VITE_BEDROCK_AGENT_ID=your-agent-id
VITE_BEDROCK_AGENT_ALIAS_ID=production
VITE_AWS_ACCESS_KEY_ID=your-access-key
VITE_AWS_SECRET_ACCESS_KEY=your-secret-key

# API Configuration
VITE_API_BASE_URL=https://api.example.com
VITE_WS_URL=wss://ws.example.com

# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# Google Integration
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_GOOGLE_API_KEY=your-google-api-key

# Development Settings
VITE_DEVELOPMENT_MODE=true
VITE_MOCK_DATA_ENABLED=true
VITE_API_TIMEOUT=30000
```

### Configuration Service

```typescript
class ConfigService {
  static get aws() {
    return {
      region: import.meta.env.VITE_AWS_REGION,
      agentId: import.meta.env.VITE_BEDROCK_AGENT_ID,
      agentAliasId: import.meta.env.VITE_BEDROCK_AGENT_ALIAS_ID,
    }
  }

  static get api() {
    return {
      baseURL: import.meta.env.VITE_API_BASE_URL,
      timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
    }
  }

  static get development() {
    return {
      isDevelopment: import.meta.env.VITE_DEVELOPMENT_MODE === 'true',
      mockDataEnabled: import.meta.env.VITE_MOCK_DATA_ENABLED === 'true',
    }
  }
}
```

This API integration architecture provides a robust, scalable, and maintainable foundation for frontend-backend communication in the LMS AI Agent system.
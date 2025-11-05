import { bedrockAgentService } from './bedrockAgentService';

export interface DocumentMetadata {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadDate: string;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress?: number;
  extractedText?: string;
  entities?: Array<{
    text: string;
    type: string;
    confidence: number;
  }>;
  keyPhrases?: Array<{
    text: string;
    confidence: number;
  }>;
  summary?: string;
  language?: string;
  sentiment?: {
    sentiment: string;
    confidence: any;
  };
  s3Key?: string;
  downloadUrl?: string;
  processingError?: string;
}

export interface UploadProgress {
  fileId: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  message?: string;
}

export class DocumentService {
  private static instance: DocumentService;
  private apiBaseUrl: string;
  private uploadProgressCallbacks: Map<string, (progress: UploadProgress) => void> = new Map();

  private constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_GATEWAY_URL || 'https://7k21xsoz93.execute-api.us-east-1.amazonaws.com/dev';
  }

  public static getInstance(): DocumentService {
    if (!DocumentService.instance) {
      DocumentService.instance = new DocumentService();
    }
    return DocumentService.instance;
  }

  /**
   * Upload a file with real-time progress tracking
   */
  public async uploadFile(
    file: File, 
    userId: string,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<DocumentMetadata> {
    const fileId = `file-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    
    try {
      // Register progress callback
      if (onProgress) {
        this.uploadProgressCallbacks.set(fileId, onProgress);
      }

      // Update progress: Starting upload
      this.updateProgress(fileId, 0, 'uploading', 'Preparing upload...');

      // Step 1: Get presigned upload URL
      const presignedResponse = await fetch(`${this.apiBaseUrl}/api/v1/upload/presigned`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_name: file.name,
          content_type: file.type,
          user_id: userId
        })
      });

      if (!presignedResponse.ok) {
        throw new Error(`Failed to get upload URL: ${presignedResponse.statusText}`);
      }

      const presignedData = await presignedResponse.json();
      if (!presignedData.success) {
        throw new Error(presignedData.error || 'Failed to get upload URL');
      }

      // Update progress: Got upload URL
      this.updateProgress(fileId, 10, 'uploading', 'Got upload URL...');

      // Step 2: Upload file to S3
      const uploadResponse = await this.uploadToS3(
        presignedData.upload_url,
        file,
        (progress) => {
          // Map S3 upload progress to 10-60%
          const mappedProgress = 10 + (progress * 0.5);
          this.updateProgress(fileId, mappedProgress, 'uploading', 'Uploading file...');
        }
      );

      if (!uploadResponse.ok) {
        throw new Error(`File upload failed: ${uploadResponse.statusText}`);
      }

      // Update progress: Upload complete, starting processing
      this.updateProgress(fileId, 60, 'processing', 'Processing document...');

      // Step 3: Trigger document processing
      const processResponse = await fetch(`${this.apiBaseUrl}/api/v1/documents/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_key: presignedData.file_key,
          user_id: userId
        })
      });

      if (!processResponse.ok) {
        throw new Error(`Document processing failed: ${processResponse.statusText}`);
      }

      const processData = await processResponse.json();
      if (!processData.success) {
        throw new Error(processData.error || 'Document processing failed');
      }

      // Update progress: Processing complete
      this.updateProgress(fileId, 100, 'completed', 'Document processed successfully!');

      // Create document metadata
      const metadata: DocumentMetadata = {
        id: processData.document_id || fileId,
        name: file.name,
        type: file.type.split('/')[1]?.toUpperCase() || 'UNKNOWN',
        size: file.size,
        uploadDate: new Date().toISOString(),
        status: 'completed',
        progress: 100,
        extractedText: processData.metadata?.extracted_text,
        entities: processData.metadata?.entities,
        keyPhrases: processData.metadata?.key_phrases,
        summary: processData.metadata?.summary,
        language: processData.metadata?.language,
        sentiment: processData.metadata?.sentiment,
        s3Key: presignedData.file_key
      };

      // Clean up progress callback
      this.uploadProgressCallbacks.delete(fileId);

      return metadata;

    } catch (error) {
      console.error('File upload error:', error);
      
      // Update progress: Failed
      this.updateProgress(fileId, 0, 'failed', `Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      // Clean up progress callback
      this.uploadProgressCallbacks.delete(fileId);

      // Return failed document metadata
      return {
        id: fileId,
        name: file.name,
        type: file.type.split('/')[1]?.toUpperCase() || 'UNKNOWN',
        size: file.size,
        uploadDate: new Date().toISOString(),
        status: 'failed',
        progress: 0,
        processingError: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Upload file to S3 with progress tracking
   */
  private async uploadToS3(
    presignedUrl: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<Response> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(new Response(xhr.response, { status: xhr.status }));
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed due to network error'));
      });

      xhr.open('PUT', presignedUrl);
      xhr.setRequestHeader('Content-Type', file.type);
      xhr.send(file);
    });
  }

  /**
   * Update upload progress
   */
  private updateProgress(fileId: string, progress: number, status: UploadProgress['status'], message?: string) {
    const callback = this.uploadProgressCallbacks.get(fileId);
    if (callback) {
      callback({
        fileId,
        progress,
        status,
        message
      });
    }
  }

  /**
   * Get list of user documents
   */
  public async getUserDocuments(userId: string): Promise<DocumentMetadata[]> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/documents?user_id=${encodeURIComponent(userId)}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to fetch documents');
      }

      // Convert API response to DocumentMetadata format
      return data.documents.map((doc: any) => ({
        id: doc.key?.split('/').slice(-2, -1)[0] || doc.filename,
        name: doc.filename || doc.original_filename || 'Unknown',
        type: doc.content_type?.split('/')[1]?.toUpperCase() || 'UNKNOWN',
        size: doc.size || doc.file_size || 0,
        uploadDate: doc.last_modified || doc.processed_at || new Date().toISOString(),
        status: doc.status || 'completed',
        extractedText: doc.extracted_text,
        entities: doc.entities,
        keyPhrases: doc.key_phrases,
        summary: doc.summary,
        language: doc.language,
        sentiment: doc.sentiment,
        s3Key: doc.key || doc.file_key,
        downloadUrl: doc.download_url
      }));

    } catch (error) {
      console.error('Failed to fetch user documents:', error);
      return [];
    }
  }

  /**
   * Delete a document
   */
  public async deleteDocument(documentId: string, userId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/v1/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId })
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to delete document:', error);
      return false;
    }
  }

  /**
   * Generate quiz from document
   */
  public async generateQuizFromDocument(
    documentId: string, 
    userId: string, 
    questionCount: number = 5
  ): Promise<any> {
    try {
      // Use the Bedrock Agent to generate quiz
      const sessionId = bedrockAgentService.generateSessionId(userId);
      const message = `Generate a ${questionCount}-question quiz from document ${documentId}. Include multiple choice, true/false, and short answer questions.`;
      
      const response = await bedrockAgentService.sendMessage(message, sessionId, userId, {
        action: 'generate_quiz',
        document_id: documentId,
        question_count: questionCount
      });

      return {
        success: true,
        quiz: response.message.content,
        citations: response.citations,
        sessionId: response.sessionId
      };

    } catch (error) {
      console.error('Failed to generate quiz:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Search documents by content
   */
  public async searchDocuments(
    query: string, 
    userId: string, 
    filters?: {
      type?: string;
      dateRange?: { start: string; end: string };
    }
  ): Promise<DocumentMetadata[]> {
    try {
      // Use Bedrock Agent for semantic search
      const sessionId = bedrockAgentService.generateSessionId(userId);
      const message = `Search my documents for: ${query}`;
      
      const response = await bedrockAgentService.sendMessage(message, sessionId, userId, {
        action: 'search_documents',
        query: query,
        filters: filters
      });

      // For now, return all documents and let frontend filter
      // In a real implementation, the agent would return filtered results
      const allDocuments = await this.getUserDocuments(userId);
      
      // Simple client-side filtering
      return allDocuments.filter(doc => 
        doc.name.toLowerCase().includes(query.toLowerCase()) ||
        doc.extractedText?.toLowerCase().includes(query.toLowerCase()) ||
        doc.summary?.toLowerCase().includes(query.toLowerCase())
      );

    } catch (error) {
      console.error('Document search failed:', error);
      return [];
    }
  }

  /**
   * Get document preview/details
   */
  public async getDocumentDetails(documentId: string, userId: string): Promise<DocumentMetadata | null> {
    try {
      const documents = await this.getUserDocuments(userId);
      return documents.find(doc => doc.id === documentId) || null;
    } catch (error) {
      console.error('Failed to get document details:', error);
      return null;
    }
  }

  /**
   * Validate file before upload
   */
  public validateFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'image/png',
      'image/jpeg',
      'image/jpg'
    ];

    if (file.size > maxSize) {
      return {
        valid: false,
        error: `File size must be less than ${maxSize / (1024 * 1024)}MB`
      };
    }

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `File type ${file.type} is not supported. Allowed types: PDF, DOC, DOCX, TXT, PNG, JPG`
      };
    }

    return { valid: true };
  }
}

// Export singleton instance
export const documentService = DocumentService.getInstance();

// Mock service for development
export class MockDocumentService {
  private documents: DocumentMetadata[] = [
    {
      id: '1',
      name: 'Machine Learning Fundamentals.pdf',
      type: 'PDF',
      size: 2048000,
      uploadDate: '2024-01-15T10:30:00Z',
      status: 'completed',
      extractedText: 'Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed...',
      entities: [
        { text: 'Machine Learning', type: 'TITLE', confidence: 0.95 },
        { text: 'Artificial Intelligence', type: 'TITLE', confidence: 0.92 }
      ],
      keyPhrases: [
        { text: 'machine learning algorithms', confidence: 0.89 },
        { text: 'supervised learning', confidence: 0.87 }
      ],
      summary: 'This document covers the fundamentals of machine learning, including supervised and unsupervised learning techniques.',
      language: 'en',
      sentiment: { sentiment: 'NEUTRAL', confidence: { Neutral: 0.85 } }
    },
    {
      id: '2',
      name: 'Data Structures and Algorithms.docx',
      type: 'DOCX',
      size: 1536000,
      uploadDate: '2024-01-14T14:20:00Z',
      status: 'completed',
      extractedText: 'Data structures are ways of organizing and storing data in a computer so that it can be accessed and modified efficiently...',
      entities: [
        { text: 'Data Structures', type: 'TITLE', confidence: 0.94 },
        { text: 'Algorithms', type: 'TITLE', confidence: 0.91 }
      ],
      keyPhrases: [
        { text: 'binary search trees', confidence: 0.88 },
        { text: 'time complexity', confidence: 0.86 }
      ],
      summary: 'Comprehensive guide to data structures and algorithms, covering arrays, linked lists, trees, and sorting algorithms.',
      language: 'en',
      sentiment: { sentiment: 'NEUTRAL', confidence: { Neutral: 0.82 } }
    }
  ];

  public async uploadFile(
    file: File, 
    userId: string,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<DocumentMetadata> {
    const fileId = `mock-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    
    // Simulate upload progress
    const progressSteps = [
      { progress: 0, status: 'uploading' as const, message: 'Starting upload...' },
      { progress: 25, status: 'uploading' as const, message: 'Uploading to cloud...' },
      { progress: 50, status: 'uploading' as const, message: 'Upload complete' },
      { progress: 60, status: 'processing' as const, message: 'Extracting text...' },
      { progress: 80, status: 'processing' as const, message: 'Analyzing content...' },
      { progress: 100, status: 'completed' as const, message: 'Processing complete!' }
    ];

    for (const step of progressSteps) {
      if (onProgress) {
        onProgress({ fileId, ...step });
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    const newDoc: DocumentMetadata = {
      id: fileId,
      name: file.name,
      type: file.type.split('/')[1]?.toUpperCase() || 'UNKNOWN',
      size: file.size,
      uploadDate: new Date().toISOString(),
      status: 'completed',
      extractedText: 'Mock extracted text content from the uploaded document...',
      entities: [
        { text: 'Sample Entity', type: 'PERSON', confidence: 0.85 }
      ],
      keyPhrases: [
        { text: 'key concept', confidence: 0.90 }
      ],
      summary: 'This is a mock summary of the uploaded document.',
      language: 'en',
      sentiment: { sentiment: 'NEUTRAL', confidence: { Neutral: 0.80 } }
    };

    this.documents.unshift(newDoc);
    return newDoc;
  }

  public async getUserDocuments(userId: string): Promise<DocumentMetadata[]> {
    await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
    return [...this.documents];
  }

  public async deleteDocument(documentId: string, userId: string): Promise<boolean> {
    const index = this.documents.findIndex(doc => doc.id === documentId);
    if (index !== -1) {
      this.documents.splice(index, 1);
      return true;
    }
    return false;
  }

  public async generateQuizFromDocument(
    documentId: string, 
    userId: string, 
    questionCount: number = 5
  ): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
      success: true,
      quiz: `Mock quiz with ${questionCount} questions generated from document ${documentId}`,
      citations: [{ source: 'Mock Document', confidence: 0.95 }]
    };
  }

  public async searchDocuments(query: string, userId: string): Promise<DocumentMetadata[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    return this.documents.filter(doc => 
      doc.name.toLowerCase().includes(query.toLowerCase()) ||
      doc.extractedText?.toLowerCase().includes(query.toLowerCase())
    );
  }

  public async getDocumentDetails(documentId: string, userId: string): Promise<DocumentMetadata | null> {
    return this.documents.find(doc => doc.id === documentId) || null;
  }

  public validateFile(file: File): { valid: boolean; error?: string } {
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      return { valid: false, error: 'File too large' };
    }
    return { valid: true };
  }
}

// Export the appropriate service based on environment
export const activeDocumentService = import.meta.env.VITE_USE_DUMMY_DATA === 'true' 
  ? new MockDocumentService() 
  : documentService;
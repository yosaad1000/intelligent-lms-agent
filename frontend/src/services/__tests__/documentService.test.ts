import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { DocumentService, MockDocumentService } from '../documentService';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    VITE_API_GATEWAY_URL: 'https://test-api.com',
    VITE_USE_DUMMY_DATA: 'false'
  }
}));

describe('DocumentService', () => {
  let documentService: DocumentService;

  beforeEach(() => {
    documentService = DocumentService.getInstance();
    mockFetch.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('validateFile', () => {
    it('should accept valid PDF file', () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const result = documentService.validateFile(file);
      
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should accept valid DOCX file', () => {
      const file = new File(['test'], 'test.docx', { 
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
      });
      const result = documentService.validateFile(file);
      
      expect(result.valid).toBe(true);
    });

    it('should reject file that is too large', () => {
      const largeContent = new Array(11 * 1024 * 1024).fill('a').join(''); // 11MB
      const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });
      const result = documentService.validateFile(file);
      
      expect(result.valid).toBe(false);
      expect(result.error).toContain('File size must be less than');
    });

    it('should reject unsupported file type', () => {
      const file = new File(['test'], 'test.exe', { type: 'application/octet-stream' });
      const result = documentService.validateFile(file);
      
      expect(result.valid).toBe(false);
      expect(result.error).toContain('File type');
      expect(result.error).toContain('is not supported');
    });
  });

  describe('uploadFile', () => {
    it('should successfully upload a file', async () => {
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const userId = 'test-user-123';

      // Mock presigned URL response
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            upload_url: 'https://s3.amazonaws.com/presigned-url',
            file_key: 'users/test-user-123/documents/file-id/test.pdf',
            file_id: 'file-id'
          })
        })
        // Mock S3 upload response
        .mockResolvedValueOnce({
          ok: true,
          status: 200
        })
        // Mock processing response
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            document_id: 'doc-123',
            metadata: {
              extracted_text: 'Test document content',
              entities: [{ text: 'Test', type: 'TITLE', confidence: 0.95 }],
              summary: 'This is a test document'
            }
          })
        });

      const progressCallback = vi.fn();
      const result = await documentService.uploadFile(file, userId, progressCallback);

      expect(result.status).toBe('completed');
      expect(result.name).toBe('test.pdf');
      expect(result.extractedText).toBe('Test document content');
      expect(progressCallback).toHaveBeenCalled();
    });

    it('should handle upload failure', async () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const userId = 'test-user-123';

      // Mock failed presigned URL response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request'
      });

      const result = await documentService.uploadFile(file, userId);

      expect(result.status).toBe('failed');
      expect(result.processingError).toContain('Failed to get upload URL');
    });
  });

  describe('getUserDocuments', () => {
    it('should fetch user documents successfully', async () => {
      const mockDocuments = [
        {
          key: 'users/test-user/documents/doc1/test.pdf',
          filename: 'test.pdf',
          size: 1024,
          last_modified: '2024-01-15T10:30:00Z'
        }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          documents: mockDocuments
        })
      });

      const result = await documentService.getUserDocuments('test-user-123');

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('test.pdf');
      expect(result[0].size).toBe(1024);
    });

    it('should handle fetch error gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await documentService.getUserDocuments('test-user-123');

      expect(result).toEqual([]);
    });
  });

  describe('searchDocuments', () => {
    it('should search documents by query', async () => {
      const mockDocuments = [
        {
          id: '1',
          name: 'machine-learning.pdf',
          extractedText: 'This document covers machine learning algorithms',
          type: 'PDF',
          size: 1024,
          uploadDate: '2024-01-15T10:30:00Z',
          status: 'completed' as const
        },
        {
          id: '2', 
          name: 'data-structures.pdf',
          extractedText: 'This document covers data structures and algorithms',
          type: 'PDF',
          size: 2048,
          uploadDate: '2024-01-14T10:30:00Z',
          status: 'completed' as const
        }
      ];

      // Mock getUserDocuments call
      vi.spyOn(documentService, 'getUserDocuments').mockResolvedValueOnce(mockDocuments);

      const result = await documentService.searchDocuments('machine learning', 'test-user-123');

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe('machine-learning.pdf');
    });
  });

  describe('generateQuizFromDocument', () => {
    it('should generate quiz from document', async () => {
      // Mock bedrockAgentService
      const mockBedrockService = {
        generateSessionId: vi.fn().mockReturnValue('session-123'),
        sendMessage: vi.fn().mockResolvedValue({
          message: { content: 'Generated quiz content' },
          citations: [{ source: 'test.pdf', confidence: 0.95 }],
          sessionId: 'session-123'
        })
      };

      // Mock the import
      vi.doMock('../bedrockAgentService', () => ({
        bedrockAgentService: mockBedrockService
      }));

      const result = await documentService.generateQuizFromDocument('doc-123', 'user-123', 5);

      expect(result.success).toBe(true);
      expect(result.quiz).toBe('Generated quiz content');
    });
  });
});

describe('MockDocumentService', () => {
  let mockService: MockDocumentService;

  beforeEach(() => {
    mockService = new MockDocumentService();
  });

  describe('uploadFile', () => {
    it('should simulate file upload with progress', async () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const progressCallback = vi.fn();

      const result = await mockService.uploadFile(file, 'test-user', progressCallback);

      expect(result.status).toBe('completed');
      expect(result.name).toBe('test.pdf');
      expect(progressCallback).toHaveBeenCalledWith(
        expect.objectContaining({
          progress: 100,
          status: 'completed'
        })
      );
    });
  });

  describe('getUserDocuments', () => {
    it('should return mock documents', async () => {
      const documents = await mockService.getUserDocuments('test-user');

      expect(documents.length).toBeGreaterThan(0);
      expect(documents[0]).toHaveProperty('name');
      expect(documents[0]).toHaveProperty('status');
    });
  });

  describe('deleteDocument', () => {
    it('should delete existing document', async () => {
      const documents = await mockService.getUserDocuments('test-user');
      const documentId = documents[0].id;

      const result = await mockService.deleteDocument(documentId, 'test-user');

      expect(result).toBe(true);

      const updatedDocuments = await mockService.getUserDocuments('test-user');
      expect(updatedDocuments.find(doc => doc.id === documentId)).toBeUndefined();
    });

    it('should return false for non-existent document', async () => {
      const result = await mockService.deleteDocument('non-existent', 'test-user');

      expect(result).toBe(false);
    });
  });

  describe('searchDocuments', () => {
    it('should filter documents by query', async () => {
      const result = await mockService.searchDocuments('Machine Learning', 'test-user');

      expect(result.length).toBeGreaterThan(0);
      expect(result[0].name.toLowerCase()).toContain('machine');
    });

    it('should return empty array for no matches', async () => {
      const result = await mockService.searchDocuments('nonexistent topic', 'test-user');

      expect(result).toEqual([]);
    });
  });

  describe('generateQuizFromDocument', () => {
    it('should generate mock quiz', async () => {
      const result = await mockService.generateQuizFromDocument('doc-123', 'user-123', 5);

      expect(result.success).toBe(true);
      expect(result.quiz).toContain('Mock quiz');
      expect(result.quiz).toContain('5 questions');
    });
  });

  describe('validateFile', () => {
    it('should validate file size', () => {
      const largeContent = new Array(11 * 1024 * 1024).fill('a').join('');
      const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });

      const result = mockService.validateFile(file);

      expect(result.valid).toBe(false);
      expect(result.error).toBe('File too large');
    });

    it('should accept valid file', () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      const result = mockService.validateFile(file);

      expect(result.valid).toBe(true);
    });
  });
});
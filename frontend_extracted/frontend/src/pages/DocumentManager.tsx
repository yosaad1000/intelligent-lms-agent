import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  DocumentArrowUpIcon,
  DocumentTextIcon,
  EyeIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FolderIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  XMarkIcon,
  ArrowDownTrayIcon,
  AcademicCapIcon,
  SparklesIcon,
  TagIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import { DocumentMetadata, UploadProgress, activeDocumentService } from '../services/documentService';

const DocumentManager: React.FC = () => {
  const { user, currentRole } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: UploadProgress }>({});
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentMetadata | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load user documents on component mount
  useEffect(() => {
    loadUserDocuments();
  }, [user]);

  const loadUserDocuments = async () => {
    if (!user?.user_id) return;
    
    setLoading(true);
    try {
      const userDocuments = await activeDocumentService.getUserDocuments(user.user_id);
      setDocuments(userDocuments);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (files: FileList) => {
    if (!files || !user?.user_id) return;

    setLoading(true);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      // Validate file
      const validation = activeDocumentService.validateFile(file);
      if (!validation.valid) {
        alert(`${file.name}: ${validation.error}`);
        continue;
      }

      try {
        // Upload file with progress tracking
        const document = await activeDocumentService.uploadFile(
          file,
          user.user_id,
          (progress) => {
            setUploadProgress(prev => ({
              ...prev,
              [progress.fileId]: progress
            }));
          }
        );

        // Add document to list
        setDocuments(prev => {
          const existing = prev.find(doc => doc.id === document.id);
          if (existing) {
            return prev.map(doc => doc.id === document.id ? document : doc);
          }
          return [document, ...prev];
        });

        // Clean up progress after completion
        setTimeout(() => {
          setUploadProgress(prev => {
            const newProgress = { ...prev };
            delete newProgress[document.id];
            return newProgress;
          });
        }, 2000);

      } catch (error) {
        console.error('Upload failed:', error);
        alert(`Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    setLoading(false);
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      handleFileUpload(files);
    }
    event.target.value = '';
  };

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  }, [user]);

  const handleDeleteDocument = async (id: string) => {
    if (!user?.user_id) return;
    
    const confirmed = window.confirm('Are you sure you want to delete this document?');
    if (!confirmed) return;

    try {
      const success = await activeDocumentService.deleteDocument(id, user.user_id);
      if (success) {
        setDocuments(prev => prev.filter(doc => doc.id !== id));
      } else {
        alert('Failed to delete document');
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete document');
    }
  };

  const handleViewDocument = (document: DocumentMetadata) => {
    setSelectedDocument(document);
    setShowPreview(true);
  };

  const handleGenerateQuiz = async (document: DocumentMetadata) => {
    if (!user?.user_id) return;

    try {
      setLoading(true);
      const result = await activeDocumentService.generateQuizFromDocument(
        document.id,
        user.user_id,
        5
      );

      if (result.success) {
        // Navigate to quiz page with generated quiz
        navigate('/quiz', { 
          state: { 
            quiz: result.quiz, 
            documentName: document.name,
            sessionId: result.sessionId
          } 
        });
      } else {
        alert('Failed to generate quiz: ' + result.error);
      }
    } catch (error) {
      console.error('Quiz generation failed:', error);
      alert('Failed to generate quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchDocuments = async (query: string) => {
    if (!user?.user_id) return;

    if (!query.trim()) {
      loadUserDocuments();
      return;
    }

    try {
      setLoading(true);
      const results = await activeDocumentService.searchDocuments(query, user.user_id);
      setDocuments(results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string, progress?: number) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'processing':
      case 'uploading':
        return <ClockIcon className="h-5 w-5 text-yellow-500 animate-spin" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getFileTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pdf':
        return <DocumentTextIcon className="h-8 w-8 text-red-500" />;
      case 'docx':
      case 'doc':
        return <DocumentTextIcon className="h-8 w-8 text-blue-500" />;
      case 'txt':
        return <DocumentTextIcon className="h-8 w-8 text-gray-500" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
        return <DocumentTextIcon className="h-8 w-8 text-green-500" />;
      default:
        return <DocumentTextIcon className="h-8 w-8 text-gray-500" />;
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.extractedText?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.summary?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesType = filterType === 'all' || doc.type.toLowerCase() === filterType.toLowerCase();
    
    return matchesSearch && matchesType;
  });

  // Get unique file types for filter
  const fileTypes = ['all', ...Array.from(new Set(documents.map(doc => doc.type)))];

  // Handle search with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchTerm) {
        handleSearchDocuments(searchTerm);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 safe-area-padding transition-colors">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container-responsive">
          <div className="py-4 sm:py-6">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
              Document Manager
            </h1>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mt-1">
              Upload and manage your study materials for AI processing
            </p>
          </div>
        </div>
      </div>

      <div className="container-responsive py-6 sm:py-8">
        {/* Upload Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Upload Documents
          </h2>
          
          <div 
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragOver 
                ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' 
                : 'border-gray-300 dark:border-gray-600'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <CloudArrowUpIcon className={`mx-auto h-12 w-12 mb-4 ${
              isDragOver ? 'text-blue-500' : 'text-gray-400'
            }`} />
            <div className="mb-4">
              <label htmlFor="file-upload" className="cursor-pointer">
                <span className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  {isDragOver ? 'Drop files here' : 'Drop files here or click to upload'}
                </span>
                <input
                  ref={fileInputRef}
                  id="file-upload"
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
              </label>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Supports PDF, DOC, DOCX, TXT, PNG, JPG files up to 10MB each
            </p>
            <div className="mt-4 flex justify-center">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Choose Files
              </button>
            </div>
          </div>

          {/* Upload Progress */}
          {Object.keys(uploadProgress).length > 0 && (
            <div className="mt-6 space-y-3">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Upload Progress
              </h3>
              {Object.entries(uploadProgress).map(([fileId, progress]) => (
                <div key={fileId} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-700 dark:text-gray-300">
                      {progress.message || 'Processing...'}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400">
                      {Math.round(progress.progress)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        progress.status === 'failed' 
                          ? 'bg-red-500' 
                          : progress.status === 'completed'
                          ? 'bg-green-500'
                          : 'bg-blue-500'
                      }`}
                      style={{ width: `${progress.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Search and Filter */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents by name, content, or summary..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600 dark:text-gray-400">Filter:</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
              >
                {fileTypes.map(type => (
                  <option key={type} value={type}>
                    {type === 'all' ? 'All Types' : type.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={loadUserDocuments}
              className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Documents List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Your Documents ({filteredDocuments.length})
            </h2>
          </div>

          {filteredDocuments.length === 0 ? (
            <div className="p-8 text-center">
              <FolderIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                No documents found
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                {searchTerm ? 'Try adjusting your search terms' : 'Upload your first document to get started'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredDocuments.map((doc) => (
                <div key={doc.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1 min-w-0">
                      {getFileTypeIcon(doc.type)}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {doc.name}
                        </h3>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {doc.type} • {formatFileSize(doc.size)}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(doc.uploadDate).toLocaleDateString()}
                          </span>
                        </div>
                        
                        {/* Document metadata */}
                        {doc.status === 'completed' && (
                          <div className="mt-2 space-y-1">
                            {doc.summary && (
                              <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                                {doc.summary}
                              </p>
                            )}
                            {doc.entities && doc.entities.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {doc.entities.slice(0, 3).map((entity, idx) => (
                                  <span 
                                    key={idx}
                                    className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                                  >
                                    <TagIcon className="h-3 w-3 mr-1" />
                                    {entity.text}
                                  </span>
                                ))}
                                {doc.entities.length > 3 && (
                                  <span className="text-xs text-gray-500">
                                    +{doc.entities.length - 3} more
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {(doc.status === 'processing' || doc.status === 'uploading') && (
                          <div className="mt-2">
                            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                              <span>
                                {uploadProgress[doc.id]?.message || 'Processing...'}
                              </span>
                              <span>{Math.round(uploadProgress[doc.id]?.progress || doc.progress || 0)}%</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                              <div 
                                className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                                style={{ width: `${uploadProgress[doc.id]?.progress || doc.progress || 0}%` }}
                              />
                            </div>
                          </div>
                        )}

                        {doc.status === 'failed' && (
                          <div className="mt-2">
                            <p className="text-xs text-red-600 dark:text-red-400">
                              {doc.processingError || 'Processing failed'}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 ml-4">
                      {getStatusIcon(doc.status, doc.progress)}
                      
                      {doc.status === 'completed' && (
                        <>
                          <button 
                            onClick={() => handleViewDocument(doc)}
                            className="p-2 text-gray-400 hover:text-blue-500 transition-colors"
                            title="View document details"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </button>
                          
                          <button 
                            onClick={() => handleGenerateQuiz(doc)}
                            className="p-2 text-gray-400 hover:text-green-500 transition-colors"
                            title="Generate quiz from document"
                          >
                            <AcademicCapIcon className="h-4 w-4" />
                          </button>

                          <button 
                            onClick={() => navigate('/chat', { state: { documentContext: doc } })}
                            className="p-2 text-gray-400 hover:text-purple-500 transition-colors"
                            title="Chat about this document"
                          >
                            <ChatBubbleLeftRightIcon className="h-4 w-4" />
                          </button>

                          {doc.downloadUrl && (
                            <a 
                              href={doc.downloadUrl}
                              download={doc.name}
                              className="p-2 text-gray-400 hover:text-indigo-500 transition-colors"
                              title="Download document"
                            >
                              <ArrowDownTrayIcon className="h-4 w-4" />
                            </a>
                          )}
                        </>
                      )}
                      
                      <button 
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                        title="Delete document"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Processing Status */}
        {documents.some(doc => doc.status === 'processing' || doc.status === 'uploading') && (
          <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <div className="flex items-center">
              <ClockIcon className="h-5 w-5 text-blue-500 mr-3 animate-spin" />
              <div>
                <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Processing Documents
                </h3>
                <p className="text-sm text-blue-700 dark:text-blue-200 mt-1">
                  Your documents are being processed with AWS Textract and Comprehend for AI analysis. This may take a few minutes.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* AI Features Info */}
        <div className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-700 rounded-lg p-4">
          <div className="flex items-start">
            <SparklesIcon className="h-5 w-5 text-purple-500 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-purple-900 dark:text-purple-100">
                AI-Powered Document Analysis
              </h3>
              <p className="text-sm text-purple-700 dark:text-purple-200 mt-1">
                Your documents are automatically processed with AWS Textract for text extraction, 
                Amazon Comprehend for entity recognition, and integrated with our AI assistant for 
                intelligent conversations, quiz generation, and learning analytics.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Document Preview Modal */}
      {showPreview && selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                {selectedDocument.name}
              </h2>
              <button
                onClick={() => setShowPreview(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Document Info */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                      Document Information
                    </h3>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Type:</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {selectedDocument.type}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Size:</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {formatFileSize(selectedDocument.size)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Uploaded:</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {new Date(selectedDocument.uploadDate).toLocaleDateString()}
                        </span>
                      </div>
                      {selectedDocument.language && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Language:</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {selectedDocument.language.toUpperCase()}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Summary */}
                  {selectedDocument.summary && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                        AI Summary
                      </h3>
                      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                          {selectedDocument.summary}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Entities */}
                  {selectedDocument.entities && selectedDocument.entities.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                        Extracted Entities
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedDocument.entities.map((entity, idx) => (
                          <span 
                            key={idx}
                            className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                          >
                            {entity.text} ({entity.type})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Key Phrases */}
                  {selectedDocument.keyPhrases && selectedDocument.keyPhrases.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                        Key Phrases
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedDocument.keyPhrases.map((phrase, idx) => (
                          <span 
                            key={idx}
                            className="inline-flex items-center px-3 py-1 rounded-full text-xs bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                          >
                            {phrase.text}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Extracted Text */}
                <div>
                  <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Extracted Text (Preview)
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 h-96 overflow-y-auto">
                    <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                      {selectedDocument.extractedText || 'No text extracted yet...'}
                    </pre>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  onClick={() => handleGenerateQuiz(selectedDocument)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center"
                >
                  <AcademicCapIcon className="h-4 w-4 mr-2" />
                  Generate Quiz
                </button>
                <button
                  onClick={() => {
                    setShowPreview(false);
                    navigate('/chat', { state: { documentContext: selectedDocument } });
                  }}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center"
                >
                  <ChatBubbleLeftRightIcon className="h-4 w-4 mr-2" />
                  Chat About Document
                </button>
                {selectedDocument.downloadUrl && (
                  <a
                    href={selectedDocument.downloadUrl}
                    download={selectedDocument.name}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                    Download
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManager;
import React, { useState, useRef } from 'react';
import { directAgentService, AgentError, DocumentAnalysis } from '../services/directAgentService';
import { 
  DocumentArrowUpIcon,
  DocumentTextIcon,
  TrashIcon,
  EyeIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadTime: Date;
  url?: string;
  analysis?: DocumentAnalysis;
  isAnalyzing?: boolean;
  error?: string;
}

const DocumentTester: React.FC = () => {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<UploadedDocument | null>(null);
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    
    try {
      for (const file of Array.from(files)) {
        // Validate file type
        if (!file.type.includes('pdf') && !file.type.includes('text') && !file.type.includes('document')) {
          throw new Error(`Unsupported file type: ${file.type}`);
        }

        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
          throw new Error(`File too large: ${file.name}. Maximum size is 10MB.`);
        }

        // Create document object
        const newDocument: UploadedDocument = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          name: file.name,
          size: file.size,
          type: file.type,
          uploadTime: new Date(),
          url: URL.createObjectURL(file) // For preview purposes
        };

        setDocuments(prev => [...prev, newDocument]);
      }
    } catch (error) {
      console.error('File upload error:', error);
      // You could add a toast notification here
    } finally {
      setIsUploading(false);
      // Clear the input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const analyzeDocument = async (document: UploadedDocument, query?: string) => {
    if (!document.url) return;

    // Update document state to show analyzing
    setDocuments(prev => prev.map(doc => 
      doc.id === document.id 
        ? { ...doc, isAnalyzing: true, error: undefined }
        : doc
    ));

    try {
      const analysisQuery = query || 'Analyze this document and provide a comprehensive summary including key points, main topics, and important insights.';
      
      const startTime = Date.now();
      const analysis = await directAgentService.analyzeDocument(document.name, analysisQuery);
      const processingTime = Date.now() - startTime;

      // Update document with analysis results
      setDocuments(prev => prev.map(doc => 
        doc.id === document.id 
          ? { 
              ...doc, 
              analysis: {
                ...analysis,
                processingTime
              },
              isAnalyzing: false 
            }
          : doc
      ));

      // Select this document to show results
      setSelectedDocument(prev => prev?.id === document.id ? {
        ...document,
        analysis: { ...analysis, processingTime },
        isAnalyzing: false
      } : prev);

    } catch (error) {
      const errorMessage = error instanceof AgentError 
        ? directAgentService.getErrorMessage(error)
        : 'Document analysis failed';

      // Update document with error
      setDocuments(prev => prev.map(doc => 
        doc.id === document.id 
          ? { ...doc, isAnalyzing: false, error: errorMessage }
          : doc
      ));
    }
  };

  const removeDocument = (documentId: string) => {
    setDocuments(prev => {
      const updated = prev.filter(doc => doc.id !== documentId);
      // If the removed document was selected, clear selection
      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null);
      }
      return updated;
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getDocumentIcon = (type: string) => {
    if (type.includes('pdf')) {
      return <DocumentTextIcon className="h-8 w-8 text-red-500" />;
    }
    return <DocumentTextIcon className="h-8 w-8 text-blue-500" />;
  };

  const predefinedQueries = [
    "Summarize the main points of this document",
    "What are the key findings or conclusions?",
    "Extract important data, statistics, or numbers",
    "Identify the main topics and themes",
    "What questions does this document answer?",
    "Generate study notes from this content"
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Document Tester
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Test document upload and AI-powered analysis functionality
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Document Upload and List */}
        <div className="space-y-6">
          {/* Upload Area */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 p-6">
            <div className="text-center">
              <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900 dark:text-gray-100">
                    Upload documents for analysis
                  </span>
                  <span className="mt-1 block text-xs text-gray-500 dark:text-gray-400">
                    PDF, TXT, DOC files up to 10MB
                  </span>
                </label>
                <input
                  ref={fileInputRef}
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  className="sr-only"
                  multiple
                  accept=".pdf,.txt,.doc,.docx"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                />
              </div>
              <div className="mt-4">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
                      Choose Files
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Document List */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                Uploaded Documents ({documents.length})
              </h3>
            </div>
            
            <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-96 overflow-y-auto">
              {documents.length === 0 ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                  No documents uploaded yet
                </div>
              ) : (
                documents.map((document) => (
                  <div key={document.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        {getDocumentIcon(document.type)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                            {document.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {formatFileSize(document.size)} • {document.uploadTime.toLocaleString()}
                          </p>
                          
                          {document.error && (
                            <div className="flex items-center mt-1 text-xs text-red-600 dark:text-red-400">
                              <XCircleIcon className="h-3 w-3 mr-1" />
                              {document.error}
                            </div>
                          )}
                          
                          {document.analysis && (
                            <div className="flex items-center mt-1 text-xs text-green-600 dark:text-green-400">
                              <CheckCircleIcon className="h-3 w-3 mr-1" />
                              Analysis complete ({document.analysis.processingTime}ms)
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {document.isAnalyzing ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        ) : (
                          <>
                            <button
                              onClick={() => setSelectedDocument(document)}
                              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                              title="View details"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => analyzeDocument(document)}
                              disabled={document.isAnalyzing}
                              className="p-1 text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 disabled:opacity-50"
                              title="Analyze document"
                            >
                              <MagnifyingGlassIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => removeDocument(document.id)}
                              className="p-1 text-red-400 hover:text-red-600 dark:hover:text-red-300"
                              title="Remove document"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Analysis Interface and Results */}
        <div className="space-y-6">
          {/* Analysis Query Input */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
              Custom Analysis Query
            </h3>
            
            <div className="space-y-3">
              <textarea
                value={analysisQuery}
                onChange={(e) => setAnalysisQuery(e.target.value)}
                placeholder="Enter your analysis question or leave blank for general analysis..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                rows={3}
              />
              
              {selectedDocument && (
                <button
                  onClick={() => analyzeDocument(selectedDocument, analysisQuery)}
                  disabled={selectedDocument.isAnalyzing}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {selectedDocument.isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <MagnifyingGlassIcon className="h-4 w-4" />
                      <span>Analyze Selected Document</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Predefined Queries */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
              Quick Analysis Options
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {predefinedQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => setAnalysisQuery(query)}
                  className="text-left px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-600"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>

          {/* Analysis Results */}
          {selectedDocument && (
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Analysis Results
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedDocument.name}
                </p>
              </div>
              
              <div className="p-4">
                {selectedDocument.isAnalyzing ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-3 text-gray-600 dark:text-gray-400">
                      Analyzing document...
                    </span>
                  </div>
                ) : selectedDocument.error ? (
                  <div className="flex items-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-3" />
                    <div>
                      <p className="text-red-800 dark:text-red-200 font-medium">Analysis Failed</p>
                      <p className="text-red-600 dark:text-red-400 text-sm">{selectedDocument.error}</p>
                    </div>
                  </div>
                ) : selectedDocument.analysis ? (
                  <div className="space-y-4">
                    {/* Processing Time */}
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <ClockIcon className="h-4 w-4 mr-2" />
                      Processing time: {selectedDocument.analysis.processingTime}ms
                    </div>

                    {/* Summary */}
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Summary</h4>
                      <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                        {selectedDocument.analysis.summary}
                      </p>
                    </div>

                    {/* Key Points */}
                    {selectedDocument.analysis.keyPoints && selectedDocument.analysis.keyPoints.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Key Points</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                          {selectedDocument.analysis.keyPoints.map((point, index) => (
                            <li key={index}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Insights */}
                    {selectedDocument.analysis.insights && selectedDocument.analysis.insights.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Insights</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                          {selectedDocument.analysis.insights.map((insight, index) => (
                            <li key={index}>{insight}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Suggested Questions */}
                    {selectedDocument.analysis.suggestedQuestions && selectedDocument.analysis.suggestedQuestions.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Suggested Questions</h4>
                        <div className="space-y-2">
                          {selectedDocument.analysis.suggestedQuestions.map((question, index) => (
                            <button
                              key={index}
                              onClick={() => setAnalysisQuery(question)}
                              className="block w-full text-left px-3 py-2 text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30 border border-blue-200 dark:border-blue-700"
                            >
                              {question}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Confidence Score */}
                    {selectedDocument.analysis.confidence && (
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Confidence Score</h4>
                        <div className="flex items-center">
                          <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${selectedDocument.analysis.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="ml-3 text-sm text-gray-600 dark:text-gray-400">
                            {Math.round(selectedDocument.analysis.confidence * 100)}%
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <DocumentTextIcon className="mx-auto h-12 w-12 mb-4" />
                    <p>Click "Analyze" to process this document</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentTester;
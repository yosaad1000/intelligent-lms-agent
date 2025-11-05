import React, { useState, useEffect, useRef } from 'react';
import { directAgentService, AgentError, AgentResponse } from '../services/directAgentService';
import { 
  PaperAirplaneIcon,
  TrashIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import CompactStatusIndicator from './CompactStatusIndicator';

interface ChatMessage {
  id: string;
  type: 'user' | 'agent' | 'error';
  content: string;
  timestamp: Date;
  metadata?: {
    sessionId?: string;
    processingTime?: number;
    tokensUsed?: number;
  };
}

const ChatTester: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'testing'>('disconnected');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize session and test connection
    initializeSession();
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initializeSession = async () => {
    setConnectionStatus('testing');
    try {
      const newSessionId = directAgentService.createSession();
      setSessionId(newSessionId);
      
      // Test connection
      await directAgentService.validateConfiguration();
      setConnectionStatus('connected');
      
      // Add welcome message
      addMessage({
        type: 'agent',
        content: 'Chat testing session initialized. You can now test the Bedrock Agent chat functionality.',
        timestamp: new Date(),
        metadata: { sessionId: newSessionId }
      });
    } catch (error) {
      setConnectionStatus('disconnected');
      addMessage({
        type: 'error',
        content: `Failed to initialize chat session: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      });
    }
  };

  const addMessage = (message: Omit<ChatMessage, 'id'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9)
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message
    addMessage({
      type: 'user',
      content: userMessage,
      timestamp: new Date(),
      metadata: { sessionId }
    });

    try {
      const startTime = Date.now();
      const response: AgentResponse = await directAgentService.sendMessage(userMessage, sessionId);
      const processingTime = Date.now() - startTime;

      // Add agent response
      addMessage({
        type: 'agent',
        content: response.content,
        timestamp: new Date(),
        metadata: {
          sessionId: response.sessionId,
          processingTime,
          tokensUsed: response.metadata?.tokensUsed
        }
      });

    } catch (error) {
      const errorMessage = error instanceof AgentError 
        ? directAgentService.getErrorMessage(error)
        : 'Failed to send message';

      addMessage({
        type: 'error',
        content: errorMessage,
        timestamp: new Date(),
        metadata: { sessionId }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([]);
    // Create new session
    const newSessionId = directAgentService.createSession();
    setSessionId(newSessionId);
    
    addMessage({
      type: 'agent',
      content: 'Conversation cleared. New session started.',
      timestamp: new Date(),
      metadata: { sessionId: newSessionId }
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'disconnected':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'testing':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>;
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const quickTestMessages = [
    "Hello, can you help me with machine learning concepts?",
    "Explain the difference between supervised and unsupervised learning",
    "What are the key components of a neural network?",
    "How does backpropagation work in deep learning?"
  ];

  return (
    <div className="max-w-4xl mx-auto p-6 h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Chat Tester
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Test real-time conversation with the Bedrock Agent
          </p>
        </div>
        
        {/* Status Indicator */}
        <div className="flex items-center space-x-3">
          <CompactStatusIndicator />
        </div>
        
        {/* Connection Status */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span className={`text-sm font-medium ${
              connectionStatus === 'connected' ? 'text-green-600 dark:text-green-400' :
              connectionStatus === 'disconnected' ? 'text-red-600 dark:text-red-400' :
              'text-blue-600 dark:text-blue-400'
            }`}>
              {connectionStatus === 'connected' ? 'Connected' :
               connectionStatus === 'disconnected' ? 'Disconnected' :
               'Testing...'}
            </span>
          </div>
          
          <button
            onClick={clearConversation}
            className="flex items-center space-x-2 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            <TrashIcon className="h-4 w-4" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Session Info */}
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 mb-4">
        <div className="flex items-center justify-between text-sm">
          <div>
            <span className="font-medium text-gray-700 dark:text-gray-300">Session ID:</span>
            <span className="ml-2 font-mono text-gray-600 dark:text-gray-400">{sessionId}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700 dark:text-gray-300">Messages:</span>
            <span className="ml-2 text-gray-600 dark:text-gray-400">{messages.length}</span>
          </div>
        </div>
      </div>

      {/* Quick Test Buttons */}
      <div className="mb-4">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Quick Test Messages:</h3>
        <div className="flex flex-wrap gap-2">
          {quickTestMessages.map((message, index) => (
            <button
              key={index}
              onClick={() => setInputMessage(message)}
              disabled={isLoading}
              className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full hover:bg-blue-200 dark:hover:bg-blue-800 disabled:opacity-50"
            >
              {message.length > 40 ? message.substring(0, 40) + '...' : message}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.type === 'error'
                    ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-700'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                }`}
              >
                <div className="whitespace-pre-wrap break-words">
                  {message.content}
                </div>
                
                {/* Message metadata */}
                <div className="flex items-center justify-between mt-2 text-xs opacity-75">
                  <div className="flex items-center space-x-2">
                    <ClockIcon className="h-3 w-3" />
                    <span>{formatTimestamp(message.timestamp)}</span>
                  </div>
                  
                  {message.metadata?.processingTime && (
                    <span>{message.metadata.processingTime}ms</span>
                  )}
                </div>
                
                {message.metadata?.tokensUsed && (
                  <div className="text-xs opacity-75 mt-1">
                    Tokens: {message.metadata.tokensUsed}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                  <span className="text-gray-600 dark:text-gray-400">Agent is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="flex space-x-3">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              disabled={isLoading || connectionStatus !== 'connected'}
              className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
              rows={2}
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading || connectionStatus !== 'connected'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <PaperAirplaneIcon className="h-4 w-4" />
              <span>Send</span>
            </button>
          </div>
          
          {connectionStatus !== 'connected' && (
            <div className="mt-2 flex items-center space-x-2 text-sm text-yellow-600 dark:text-yellow-400">
              <ExclamationTriangleIcon className="h-4 w-4" />
              <span>
                {connectionStatus === 'disconnected' 
                  ? 'Not connected to agent. Check configuration.' 
                  : 'Testing connection...'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatTester;
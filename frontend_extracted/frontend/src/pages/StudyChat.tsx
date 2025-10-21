import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useMockAuth } from '../contexts/MockAuthContext';
import { apiBedrockAgentService } from '../services/apiBedrockAgentService';
import { directAgentService, AgentResponse } from '../services/directAgentService';
import type { AgentMessage } from '../services/apiBedrockAgentService';
import { mockDataService } from '../services/mockDataService';
import { useHybridMode, useAgentService } from '../hooks/useHybridMode';
import HybridModeIndicator from '../components/HybridModeIndicator';
import { 
  PaperAirplaneIcon,
  DocumentTextIcon,
  UserIcon,
  ComputerDesktopIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  BookOpenIcon,
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

// Use AgentMessage from the service
type Message = AgentMessage;

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

// Hook to get the appropriate auth context
const useAuthContext = () => {
  const isDev = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
  if (isDev) {
    return useMockAuth();
  } else {
    return useAuth();
  }
};

const StudyChat: React.FC = () => {
  const { user } = useAuthContext();
  const { isHybridMode, isAgentConnected, statusIndicators } = useHybridMode();
  const { agentService, agentServiceType } = useAgentService();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [agentCapabilities, setAgentCapabilities] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize agent and load data
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Get agent capabilities based on service type
        let capabilities: string[] = [];
        if (agentServiceType === 'direct') {
          capabilities = ['Document Analysis', 'Quiz Generation', 'Interview Practice', 'Real-time Chat'];
        } else if (agentServiceType === 'api') {
          capabilities = await apiBedrockAgentService.getAgentCapabilities();
        } else {
          capabilities = ['Mock Chat', 'Sample Responses'];
        }
        setAgentCapabilities(capabilities);
        
        // Generate session ID based on service type
        let sessionId: string;
        if (agentServiceType === 'direct') {
          sessionId = directAgentService.createSession();
        } else {
          sessionId = apiBedrockAgentService.generateSessionId(user?.id);
        }
        setCurrentSessionId(sessionId);
        
        // Load mock conversations
        const mockConversations: Conversation[] = [
          {
            id: '1',
            title: 'Machine Learning Basics',
            lastMessage: 'Can you explain supervised learning?',
            timestamp: new Date('2024-01-15T10:30:00'),
            messageCount: 12
          },
          {
            id: '2',
            title: 'Data Structures Discussion',
            lastMessage: 'What are the advantages of binary trees?',
            timestamp: new Date('2024-01-14T15:45:00'),
            messageCount: 8
          },
          {
            id: '3',
            title: 'Algorithm Analysis',
            lastMessage: 'How do I calculate time complexity?',
            timestamp: new Date('2024-01-13T09:15:00'),
            messageCount: 15
          }
        ];
        setConversations(mockConversations);

        // Load first conversation
        if (mockConversations.length > 0) {
          setCurrentConversation(mockConversations[0].id);
          loadConversationMessages(mockConversations[0].id);
        }
      } catch (error) {
        console.error('Failed to initialize chat:', error);
      }
    };

    initializeChat();
  }, [user, agentServiceType]);

  const loadConversationMessages = (conversationId: string) => {
    // Mock messages for the conversation - in a real app, this would load from backend
    const mockMessages: Message[] = [
      {
        id: '1',
        content: 'Hello! I\'d like to learn about machine learning. Can you help me understand the basics?',
        sender: 'user',
        timestamp: new Date('2024-01-15T10:00:00')
      },
      {
        id: '2',
        content: 'I\'d be happy to help you learn about machine learning! Based on your uploaded documents, I can see you have materials on "Introduction to Machine Learning". \n\nMachine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task. There are three main types:\n\n1. **Supervised Learning** - Learning with labeled examples\n2. **Unsupervised Learning** - Finding patterns in unlabeled data\n3. **Reinforcement Learning** - Learning through trial and error\n\nWould you like me to elaborate on any of these types?',
        sender: 'agent',
        timestamp: new Date('2024-01-15T10:01:00'),
        citations: [
          { source: 'Introduction to Machine Learning.pdf', page: 12, confidence: 0.95 },
          { source: 'ML Fundamentals.docx', section: 'Section 2.1', confidence: 0.88 }
        ],
        toolsUsed: ['knowledge_base_retrieval', 'document_processor']
      },
      {
        id: '3',
        content: 'Can you explain supervised learning in more detail?',
        sender: 'user',
        timestamp: new Date('2024-01-15T10:30:00')
      }
    ];
    setMessages(mockMessages);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = inputMessage;
    setInputMessage('');
    setIsTyping(true);

    try {
      let agentResponse: Message;

      if (agentServiceType === 'direct') {
        console.log('🔄 Using Direct Agent Service (Hybrid Mode)');
        
        // Use Direct Agent Service for real Bedrock Agent
        const response: AgentResponse = await directAgentService.sendMessage(
          messageToSend,
          currentSessionId
        );

        if (response.error) {
          throw new Error(response.error);
        }

        agentResponse = {
          id: response.messageId,
          content: response.content,
          sender: 'agent',
          timestamp: response.timestamp,
          metadata: response.metadata
        };

        // Update session ID if it was created
        if (!currentSessionId && response.sessionId) {
          setCurrentSessionId(response.sessionId);
        }

      } else if (agentServiceType === 'api') {
        console.log('🔄 Using API Bedrock Agent Service (Standard Mode)');
        
        // Get user context for better responses
        const userContext = {
          role: 'student', // Default role for now
          userId: user?.id,
          documents: mockDataService.getDocuments(undefined, user?.id),
          classes: mockDataService.getStudentClasses(user?.id || '')
        };

        // Use existing API service
        const response = await apiBedrockAgentService.sendMessage(
          messageToSend,
          currentSessionId,
          user?.id,
          userContext
        );

        agentResponse = response.message;
      } else {
        // Mock mode - use fallback service
        console.log('🔄 Using Mock Agent Service');
        
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
        
        agentResponse = {
          id: `mock-${Date.now()}`,
          content: `This is a mock response to: "${messageToSend}". In production, this would be handled by the real AI agent.`,
          sender: 'agent',
          timestamp: new Date()
        };
      }

      setMessages(prev => [...prev, agentResponse]);
      
    } catch (error) {
      console.error('Failed to get agent response:', error);
      
      // Service-specific error messages
      let errorContent: string;
      if (agentServiceType === 'direct') {
        errorContent = "I'm having trouble connecting to the Bedrock Agent. Please check your AWS configuration and try again.";
      } else if (agentServiceType === 'api') {
        errorContent = "I'm having trouble connecting to the API service. Please try again in a moment.";
      } else {
        errorContent = "Mock service error. This would normally be handled by the real AI agent.";
      }
      
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        content: errorContent,
        sender: 'agent',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const createNewConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'New Conversation',
      lastMessage: '',
      timestamp: new Date(),
      messageCount: 0
    };
    
    setConversations(prev => [newConversation, ...prev]);
    setCurrentConversation(newConversation.id);
    setMessages([]);
    
    // Generate new session ID for new conversation based on service type
    let newSessionId: string;
    if (agentServiceType === 'direct') {
      newSessionId = directAgentService.createSession();
    } else {
      newSessionId = apiBedrockAgentService.generateSessionId(user?.id);
    }
    setCurrentSessionId(newSessionId);
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 safe-area-padding transition-colors">
      <div className="flex h-screen">
        {/* Sidebar - Conversations */}
        <div className="w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Study Chat
              </h2>
              <button
                onClick={createNewConversation}
                className="p-2 text-gray-500 hover:text-blue-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <PlusIcon className="h-5 w-5" />
              </button>
            </div>
            
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
              />
            </div>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto">
            {filteredConversations.length === 0 ? (
              <div className="p-4 text-center">
                <ChatBubbleLeftRightIcon className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No conversations found
                </p>
              </div>
            ) : (
              filteredConversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => {
                    setCurrentConversation(conversation.id);
                    loadConversationMessages(conversation.id);
                  }}
                  className={`p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                    currentConversation === conversation.id ? 'bg-blue-50 dark:bg-blue-900/20 border-r-2 border-r-blue-500' : ''
                  }`}
                >
                  <h3 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                    {conversation.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 truncate mt-1">
                    {conversation.lastMessage}
                  </p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-400">
                      {conversation.timestamp.toLocaleDateString()}
                    </span>
                    <span className="text-xs text-gray-400">
                      {conversation.messageCount} messages
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Chat Header */}
          <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {conversations.find(c => c.id === currentConversation)?.title || 'AI Study Assistant'}
                  </h1>
                  <HybridModeIndicator />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {isAgentConnected 
                    ? 'Powered by Amazon Bedrock Agent - Ask questions about your study materials'
                    : 'AI Assistant temporarily unavailable - Using fallback responses'
                  }
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <BookOpenIcon className="h-5 w-5 text-gray-400" />
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {mockDataService.getDocuments(undefined, user?.id).length} documents available
                  </span>
                </div>
                {agentCapabilities.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <SparklesIcon className="h-5 w-5 text-blue-500" />
                    <span className="text-sm text-blue-600 dark:text-blue-400">
                      {agentCapabilities.length} AI capabilities
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            {/* Agent Capabilities */}
            {agentCapabilities.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {agentCapabilities.slice(0, 4).map((capability, index) => (
                  <span 
                    key={index}
                    className="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-xs rounded-full"
                  >
                    {capability}
                  </span>
                ))}
                {agentCapabilities.length > 4 && (
                  <span className="px-2 py-1 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs rounded-full">
                    +{agentCapabilities.length - 4} more
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <ComputerDesktopIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  Start a conversation
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  Ask me anything about your uploaded study materials
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {[
                    'Explain the main concepts',
                    'Create a summary',
                    'Ask practice questions',
                    'Compare different topics'
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInputMessage(suggestion)}
                      className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-3xl ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex-shrink-0 ${message.sender === 'user' ? 'ml-3' : 'mr-3'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        message.sender === 'user' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                      }`}>
                        {message.sender === 'user' ? (
                          <UserIcon className="h-4 w-4" />
                        ) : (
                          <ComputerDesktopIcon className="h-4 w-4" />
                        )}
                      </div>
                    </div>
                    
                    <div className={`rounded-lg px-4 py-2 ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700'
                    }`}>
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      
                      {message.citations && message.citations.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Sources:</p>
                          {message.citations.map((citation, index) => (
                            <div key={index} className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                              <div className="flex items-center">
                                <DocumentTextIcon className="h-3 w-3 mr-1" />
                                <span>
                                  {citation.source}
                                  {citation.page && ` - Page ${citation.page}`}
                                  {citation.section && ` - ${citation.section}`}
                                </span>
                              </div>
                              {citation.confidence && (
                                <span className="text-xs text-gray-400">
                                  {Math.round(citation.confidence * 100)}%
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {message.toolsUsed && message.toolsUsed.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Tools used:</p>
                          <div className="flex flex-wrap gap-1">
                            {message.toolsUsed.map((tool, index) => (
                              <span 
                                key={index}
                                className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded"
                              >
                                {tool.replace(/_/g, ' ')}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div className="text-xs text-gray-400 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex max-w-3xl">
                  <div className="flex-shrink-0 mr-3">
                    <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                      <ComputerDesktopIcon className="h-4 w-4 text-gray-600 dark:text-gray-300" />
                    </div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about your study materials..."
                  rows={1}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100 resize-none"
                  style={{ minHeight: '40px', maxHeight: '120px' }}
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
                className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudyChat;
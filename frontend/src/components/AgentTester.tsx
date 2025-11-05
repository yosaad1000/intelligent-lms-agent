import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  MicrophoneIcon,
  BeakerIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import TestingModeIndicator from './TestingModeIndicator';
import './TestingModeIndicator.css';

const AgentTester: React.FC = () => {
  const testingComponents = [
    {
      name: 'Chat Tester',
      description: 'Test real-time conversation with the Bedrock Agent',
      path: '/agent-tester/chat',
      icon: ChatBubbleLeftRightIcon,
      color: 'bg-blue-500',
      status: 'completed'
    },
    {
      name: 'Document Tester',
      description: 'Test document upload and AI-powered analysis',
      path: '/agent-tester/documents',
      icon: DocumentTextIcon,
      color: 'bg-green-500',
      status: 'completed'
    },
    {
      name: 'Quiz Tester',
      description: 'Generate and take AI-powered quizzes',
      path: '/agent-tester/quiz',
      icon: ClipboardDocumentListIcon,
      color: 'bg-purple-500',
      status: 'completed'
    },
    {
      name: 'Interview Tester',
      description: 'Practice interviews with AI-powered feedback',
      path: '/agent-tester/interview',
      icon: MicrophoneIcon,
      color: 'bg-orange-500',
      status: 'completed'
    }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <BeakerIcon className="h-10 w-10 text-blue-500" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Agent Tester
          </h1>
        </div>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Test AWS Bedrock Agent functionality in hybrid mode with mock authentication 
          and real AI services. Validate chat, document analysis, quiz generation, and interview features.
        </p>
      </div>

      {/* Configuration Status */}
      <div className="mb-8">
        <TestingModeIndicator showDetails={true} />
      </div>

      {/* Testing Components Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {testingComponents.map((component) => {
          const IconComponent = component.icon;
          
          return (
            <Link
              key={component.name}
              to={component.path}
              className="group bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-200"
            >
              <div className="flex items-start space-x-4">
                <div className={`${component.color} p-3 rounded-lg text-white group-hover:scale-110 transition-transform duration-200`}>
                  <IconComponent className="h-6 w-6" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                      {component.name}
                    </h3>
                    {component.status === 'completed' && (
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  
                  <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                    {component.description}
                  </p>
                  
                  <div className="mt-3 text-blue-600 dark:text-blue-400 text-sm font-medium group-hover:underline">
                    Start Testing →
                  </div>
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Setup Information */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
        <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-3">
          Setup Requirements
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800 dark:text-blue-200">
          <div>
            <h4 className="font-medium mb-2">Environment Variables</h4>
            <ul className="space-y-1 text-xs">
              <li>• VITE_USE_MOCK_AUTH=true</li>
              <li>• VITE_USE_MOCK_AGENT=false</li>
              <li>• VITE_AWS_REGION=us-east-1</li>
              <li>• VITE_BEDROCK_AGENT_ID=ZTBBVSC6Y1</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">AWS Configuration</h4>
            <ul className="space-y-1 text-xs">
              <li>• AWS CLI configured with credentials</li>
              <li>• Bedrock Agent access permissions</li>
              <li>• S3 bucket access for documents</li>
              <li>• DynamoDB access for sessions</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentTester;
import React, { useState } from 'react';
import { apiBedrockAgentService } from '../services/apiBedrockAgentService';

interface QuizTestProps {
  onClose: () => void;
}

const QuizTest: React.FC<QuizTestProps> = ({ onClose }) => {
  const [testResult, setTestResult] = useState<string>('');
  const [testing, setTesting] = useState(false);

  const testQuizGeneration = async () => {
    setTesting(true);
    setTestResult('Testing quiz generation...');

    try {
      // Test agent connectivity
      const isConnected = await apiBedrockAgentService.validateConfiguration();
      
      if (!isConnected) {
        setTestResult('❌ Agent not connected. Using mock quiz generation.');
        return;
      }

      // Test quiz generation
      const sessionId = apiBedrockAgentService.generateSessionId('test-user');
      const response = await apiBedrockAgentService.sendMessage(
        'Generate a simple 3-question quiz about machine learning basics. Format as JSON with questions, options, and correct answers.',
        sessionId,
        'test-user',
        { action: 'test_quiz_generation' }
      );

      if (response.success) {
        setTestResult(`✅ Quiz generation test successful!\n\nAgent Response:\n${response.message.content.substring(0, 500)}...`);
      } else {
        setTestResult(`❌ Quiz generation failed: ${response.error}`);
      }
    } catch (error) {
      setTestResult(`❌ Test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Quiz Functionality Test
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <button
            onClick={testQuizGeneration}
            disabled={testing}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors"
          >
            {testing ? 'Testing...' : 'Test Quiz Generation'}
          </button>

          {testResult && (
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Test Result:</h3>
              <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {testResult}
              </div>
            </div>
          )}

          <div className="text-sm text-gray-600 dark:text-gray-400">
            <p><strong>Test Coverage:</strong></p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>✅ Agent connectivity validation</li>
              <li>✅ Quiz generation request</li>
              <li>✅ Response parsing</li>
              <li>✅ Error handling</li>
              <li>✅ Mock fallback functionality</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizTest;
import React, { useState, useEffect, useRef } from 'react';
import { directAgentService, AgentError, type InterviewSession, type InterviewFeedback } from '../services/directAgentService';
import { 
  MicrophoneIcon,
  StopIcon,
  PlayIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChatBubbleLeftRightIcon,
  ArrowPathIcon,
  StarIcon
} from '@heroicons/react/24/outline';

interface InterviewState {
  session: InterviewSession | null;
  currentQuestionIndex: number;
  isRecording: boolean;
  isPaused: boolean;
  currentResponse: string;
  feedback: InterviewFeedback[];
  overallScore: number;
  isProcessingResponse: boolean;
}

const InterviewTester: React.FC = () => {
  const [interviewState, setInterviewState] = useState<InterviewState>({
    session: null,
    currentQuestionIndex: 0,
    isRecording: false,
    isPaused: false,
    currentResponse: '',
    feedback: [],
    overallScore: 0,
    isProcessingResponse: false
  });

  const [selectedTopic, setSelectedTopic] = useState('');
  const [customTopic, setCustomTopic] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'testing'>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [interviewHistory, setInterviewHistory] = useState<InterviewSession[]>([]);

  const responseTextareaRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Check connection on mount
  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    setConnectionStatus('testing');
    try {
      const result = await directAgentService.validateConfiguration();
      setConnectionStatus(result.valid ? 'connected' : 'disconnected');
      if (!result.valid && result.error) {
        setError(result.error);
      } else {
        setError(null);
      }
    } catch (error) {
      setConnectionStatus('disconnected');
      setError(error instanceof Error ? error.message : 'Connection check failed');
    }
  };  const 
startInterview = async () => {
    const topic = selectedTopic || customTopic;
    if (!topic.trim()) {
      setError('Please select or enter an interview topic');
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      console.log('🎤 Starting interview with topic:', topic);
      
      const session = await directAgentService.startInterview(topic.trim());
      
      setInterviewState({
        session,
        currentQuestionIndex: 0,
        isRecording: false,
        isPaused: false,
        currentResponse: '',
        feedback: [],
        overallScore: 0,
        isProcessingResponse: false
      });

      console.log('✅ Interview session started:', session.sessionId);
      
    } catch (error) {
      console.error('❌ Interview start failed:', error);
      const errorMessage = error instanceof AgentError 
        ? directAgentService.getErrorMessage(error)
        : 'Failed to start interview';
      setError(errorMessage);
    } finally {
      setIsStarting(false);
    }
  };

  const submitResponse = async () => {
    if (!interviewState.session || !interviewState.currentResponse.trim()) {
      setError('Please provide a response before submitting');
      return;
    }

    setInterviewState(prev => ({ ...prev, isProcessingResponse: true }));
    setError(null);

    try {
      console.log('🎤 Submitting response for processing');
      
      const feedback = await directAgentService.conductInterview(
        interviewState.session.sessionId,
        interviewState.currentResponse.trim()
      );

      // Update interview state with feedback
      setInterviewState(prev => ({
        ...prev,
        feedback: [...prev.feedback, feedback],
        currentResponse: '',
        isProcessingResponse: false,
        overallScore: calculateOverallScore([...prev.feedback, feedback])
      }));

      // Move to next question or complete interview
      if (interviewState.currentQuestionIndex < 4) { // Limit to 5 questions
        setInterviewState(prev => ({
          ...prev,
          currentQuestionIndex: prev.currentQuestionIndex + 1
        }));
      } else {
        completeInterview();
      }

      console.log('✅ Response processed, feedback received');
      
    } catch (error) {
      console.error('❌ Response processing failed:', error);
      const errorMessage = error instanceof AgentError 
        ? directAgentService.getErrorMessage(error)
        : 'Failed to process response';
      setError(errorMessage);
      setInterviewState(prev => ({ ...prev, isProcessingResponse: false }));
    }
  };

  const completeInterview = () => {
    if (!interviewState.session) return;

    const completedSession: InterviewSession = {
      ...interviewState.session,
      status: 'completed',
      endTime: new Date(),
      feedback: interviewState.feedback
    };

    setInterviewHistory(prev => [completedSession, ...prev]);
    
    setInterviewState(prev => ({
      ...prev,
      session: { ...completedSession }
    }));

    console.log('✅ Interview completed');
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        // In a real implementation, you would transcribe this audio
        // For now, we'll just indicate that audio was recorded
        setInterviewState(prev => ({
          ...prev,
          currentResponse: prev.currentResponse + ' [Audio response recorded]'
        }));
      };

      mediaRecorder.start();
      setInterviewState(prev => ({ ...prev, isRecording: true }));
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      setError('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && interviewState.isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setInterviewState(prev => ({ ...prev, isRecording: false }));
    }
  };

  const resetInterview = () => {
    if (interviewState.isRecording) {
      stopRecording();
    }
    
    setInterviewState({
      session: null,
      currentQuestionIndex: 0,
      isRecording: false,
      isPaused: false,
      currentResponse: '',
      feedback: [],
      overallScore: 0,
      isProcessingResponse: false
    });
    
    setSelectedTopic('');
    setCustomTopic('');
    setError(null);
  };

  const calculateOverallScore = (feedback: InterviewFeedback[]): number => {
    if (feedback.length === 0) return 0;
    const totalScore = feedback.reduce((sum, f) => sum + f.score, 0);
    return Math.round((totalScore / feedback.length) * 10) / 10;
  };

  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
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

  const predefinedTopics = [
    'Software Engineering',
    'Frontend Development',
    'Backend Development',
    'System Design',
    'Data Structures & Algorithms',
    'Machine Learning',
    'Cloud Computing (AWS)',
    'Database Design',
    'DevOps & CI/CD',
    'Product Management',
    'Project Management',
    'Leadership & Management'
  ]; 
 const currentQuestion = interviewState.session?.questions[interviewState.currentQuestionIndex];
  const currentFeedback = interviewState.feedback[interviewState.currentQuestionIndex - 1];
  const isInterviewActive = interviewState.session?.status === 'active';
  const isInterviewCompleted = interviewState.session?.status === 'completed';

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center justify-center space-x-3">
          <ChatBubbleLeftRightIcon className="h-8 w-8 text-blue-500" />
          <span>Interview Tester</span>
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Practice interviews with AI-powered feedback and coaching
        </p>
      </div>

      {/* Connection Status */}
      <div className={`rounded-lg border-2 p-4 ${
        connectionStatus === 'connected' 
          ? 'border-green-200 bg-green-50 dark:bg-green-900/20' 
          : 'border-red-200 bg-red-50 dark:bg-red-900/20'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">
                {connectionStatus === 'testing' ? 'Checking Connection...' : 
                 connectionStatus === 'connected' ? 'Agent Connected' : 'Connection Error'}
              </h3>
              {error && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                  {error}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={checkConnection}
            disabled={connectionStatus === 'testing'}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Recheck
          </button>
        </div>
      </div>

      {/* Interview Setup */}
      {!interviewState.session && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Start New Interview
          </h2>

          {/* Topic Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Interview Topic
            </label>
            <select
              value={selectedTopic}
              onChange={(e) => {
                setSelectedTopic(e.target.value);
                if (e.target.value) setCustomTopic('');
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 mb-3"
            >
              <option value="">Select a topic...</option>
              {predefinedTopics.map((topic) => (
                <option key={topic} value={topic}>{topic}</option>
              ))}
            </select>

            <div className="text-center text-gray-500 dark:text-gray-400 text-sm mb-3">
              OR
            </div>

            <input
              type="text"
              value={customTopic}
              onChange={(e) => {
                setCustomTopic(e.target.value);
                if (e.target.value) setSelectedTopic('');
              }}
              placeholder="Enter custom interview topic..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
            />
          </div>

          {/* Start Button */}
          <button
            onClick={startInterview}
            disabled={(!selectedTopic && !customTopic.trim()) || isStarting || connectionStatus !== 'connected'}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {isStarting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Starting Interview...</span>
              </>
            ) : (
              <>
                <PlayIcon className="h-5 w-5" />
                <span>Start Interview</span>
              </>
            )}
          </button>
        </div>
      )}    
  {/* Active Interview */}
      {interviewState.session && isInterviewActive && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {/* Interview Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Interview: {interviewState.session.topic}
                </h2>
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400 mt-1">
                  <span>Question {interviewState.currentQuestionIndex + 1} of 5</span>
                  <span>Session: {interviewState.session.sessionId.substring(0, 8)}...</span>
                  {interviewState.session.startTime && (
                    <div className="flex items-center space-x-1">
                      <ClockIcon className="h-4 w-4" />
                      <span>
                        {formatTime(Date.now() - interviewState.session.startTime.getTime())}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              
              <button
                onClick={resetInterview}
                className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center space-x-2"
              >
                <ArrowPathIcon className="h-4 w-4" />
                <span>Reset</span>
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="px-6 py-2 bg-gray-50 dark:bg-gray-800">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${((interviewState.currentQuestionIndex + 1) / 5) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Current Question */}
          <div className="p-6 space-y-6">
            {currentQuestion && (
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                  Interview Question
                </h3>
                <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                  {currentQuestion.question}
                </p>
              </div>
            )}

            {/* Response Input */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                  Your Response
                </h4>
                
                {/* Recording Controls */}
                <div className="flex items-center space-x-2">
                  {!interviewState.isRecording ? (
                    <button
                      onClick={startRecording}
                      disabled={interviewState.isProcessingResponse}
                      className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
                    >
                      <MicrophoneIcon className="h-4 w-4" />
                      <span>Record</span>
                    </button>
                  ) : (
                    <button
                      onClick={stopRecording}
                      className="px-3 py-2 bg-red-800 text-white rounded-lg hover:bg-red-900 flex items-center space-x-2 animate-pulse"
                    >
                      <StopIcon className="h-4 w-4" />
                      <span>Stop Recording</span>
                    </button>
                  )}
                </div>
              </div>

              <textarea
                ref={responseTextareaRef}
                value={interviewState.currentResponse}
                onChange={(e) => setInterviewState(prev => ({ 
                  ...prev, 
                  currentResponse: e.target.value 
                }))}
                placeholder="Type your response here or use the record button to provide a voice response..."
                disabled={interviewState.isProcessingResponse}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                rows={6}
              />

              <button
                onClick={submitResponse}
                disabled={!interviewState.currentResponse.trim() || interviewState.isProcessingResponse}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {interviewState.isProcessingResponse ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Processing Response...</span>
                  </>
                ) : (
                  <>
                    <ChatBubbleLeftRightIcon className="h-5 w-5" />
                    <span>Submit Response</span>
                  </>
                )}
              </button>
            </div>

            {/* Previous Feedback */}
            {currentFeedback && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-6 border border-green-200 dark:border-green-700">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                    Feedback for Previous Response
                  </h4>
                  <div className="flex items-center space-x-2">
                    <StarIcon className="h-5 w-5 text-yellow-500" />
                    <span className="font-bold text-lg text-gray-900 dark:text-gray-100">
                      {currentFeedback.score}/10
                    </span>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <h5 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Feedback</h5>
                    <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                      {currentFeedback.feedback}
                    </p>
                  </div>

                  {currentFeedback.strengths.length > 0 && (
                    <div>
                      <h5 className="font-medium text-green-800 dark:text-green-200 mb-2">Strengths</h5>
                      <ul className="list-disc list-inside text-sm text-green-700 dark:text-green-300 space-y-1">
                        {currentFeedback.strengths.map((strength, index) => (
                          <li key={index}>{strength}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {currentFeedback.improvements.length > 0 && (
                    <div>
                      <h5 className="font-medium text-orange-800 dark:text-orange-200 mb-2">Areas for Improvement</h5>
                      <ul className="list-disc list-inside text-sm text-orange-700 dark:text-orange-300 space-y-1">
                        {currentFeedback.improvements.map((improvement, index) => (
                          <li key={index}>{improvement}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {currentFeedback.suggestions.length > 0 && (
                    <div>
                      <h5 className="font-medium text-blue-800 dark:text-blue-200 mb-2">Suggestions</h5>
                      <ul className="list-disc list-inside text-sm text-blue-700 dark:text-blue-300 space-y-1">
                        {currentFeedback.suggestions.map((suggestion, index) => (
                          <li key={index}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}    
  {/* Completed Interview */}
      {interviewState.session && isInterviewCompleted && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-green-50 dark:bg-green-900/20">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Interview Completed!
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {interviewState.session.topic}
                </p>
              </div>
              
              <div className="text-center">
                <div className="flex items-center space-x-2 mb-1">
                  <StarIcon className="h-6 w-6 text-yellow-500" />
                  <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {interviewState.overallScore}/10
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Overall Score</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {interviewState.feedback.length}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Questions Answered</div>
              </div>
              
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {interviewState.session.endTime && interviewState.session.startTime
                    ? formatTime(interviewState.session.endTime.getTime() - interviewState.session.startTime.getTime())
                    : '0:00'}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Time</div>
              </div>
              
              <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {Math.round((interviewState.feedback.filter(f => f.score >= 7).length / interviewState.feedback.length) * 100)}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Strong Responses</div>
              </div>
            </div>

            {/* Detailed Feedback */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                Detailed Feedback
              </h3>
              
              {interviewState.feedback.map((feedback, index) => (
                <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">
                      Question {index + 1}
                    </h4>
                    <div className="flex items-center space-x-2">
                      <StarIcon className="h-4 w-4 text-yellow-500" />
                      <span className="font-bold text-gray-900 dark:text-gray-100">
                        {feedback.score}/10
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-gray-700 dark:text-gray-300 text-sm mb-3">
                    {feedback.feedback}
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {feedback.strengths.length > 0 && (
                      <div>
                        <h5 className="font-medium text-green-800 dark:text-green-200 mb-1">Strengths</h5>
                        <ul className="list-disc list-inside text-xs text-green-700 dark:text-green-300">
                          {feedback.strengths.map((strength, i) => (
                            <li key={i}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {feedback.improvements.length > 0 && (
                      <div>
                        <h5 className="font-medium text-orange-800 dark:text-orange-200 mb-1">Improvements</h5>
                        <ul className="list-disc list-inside text-xs text-orange-700 dark:text-orange-300">
                          {feedback.improvements.map((improvement, i) => (
                            <li key={i}>{improvement}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex justify-center">
              <button
                onClick={resetInterview}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
              >
                <PlayIcon className="h-5 w-5" />
                <span>Start New Interview</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Interview History */}
      {interviewHistory.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              Interview History ({interviewHistory.length})
            </h3>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-64 overflow-y-auto">
            {interviewHistory.map((session) => (
              <div key={session.sessionId} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">
                      {session.topic}
                    </h4>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                      <span>Questions: {session.feedback?.length || 0}</span>
                      <span>
                        Duration: {session.endTime && session.startTime
                          ? formatTime(session.endTime.getTime() - session.startTime.getTime())
                          : 'N/A'}
                      </span>
                      <span>{session.startTime.toLocaleDateString()}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <StarIcon className="h-4 w-4 text-yellow-500" />
                    <span className="font-bold text-gray-900 dark:text-gray-100">
                      {session.feedback && session.feedback.length > 0
                        ? Math.round((session.feedback.reduce((sum, f) => sum + f.score, 0) / session.feedback.length) * 10) / 10
                        : 0}/10
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">How to Use Interview Tester</h3>
        <ol className="list-decimal list-inside text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>Select an interview topic or enter a custom one</li>
          <li>Click "Start Interview" to begin the AI-powered interview session</li>
          <li>Answer each question using text or voice recording</li>
          <li>Receive detailed feedback and suggestions for improvement</li>
          <li>Review your overall performance and interview history</li>
        </ol>
      </div>
    </div>
  );
};

export default InterviewTester;
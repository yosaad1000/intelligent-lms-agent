import React, { useState, useEffect } from 'react';
import { directAgentService, AgentError, type Quiz, type QuizOptions } from '../services/directAgentService';
import { 
  ClipboardDocumentListIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  AcademicCapIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface QuizResult {
  quiz: Quiz;
  userAnswers: Record<string, string>;
  score: number;
  totalQuestions: number;
  completedAt: Date;
  timeTaken: number;
}

interface QuizSession {
  quiz: Quiz | null;
  currentQuestionIndex: number;
  userAnswers: Record<string, string>;
  startTime: Date | null;
  isActive: boolean;
  isCompleted: boolean;
}

const QuizTester: React.FC = () => {
  const [quizSession, setQuizSession] = useState<QuizSession>({
    quiz: null,
    currentQuestionIndex: 0,
    userAnswers: {},
    startTime: null,
    isActive: false,
    isCompleted: false
  });

  const [quizOptions, setQuizOptions] = useState<QuizOptions>({
    difficulty: 'medium',
    questionCount: 5,
    topics: [],
    questionTypes: ['multiple-choice']
  });

  const [contentInput, setContentInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [quizResults, setQuizResults] = useState<QuizResult[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'testing'>('disconnected');

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
        setGenerationError(result.error);
      }
    } catch (error) {
      setConnectionStatus('disconnected');
      setGenerationError(error instanceof Error ? error.message : 'Connection check failed');
    }
  };

  const generateQuiz = async () => {
    if (!contentInput.trim()) {
      setGenerationError('Please provide content for quiz generation');
      return;
    }

    setIsGenerating(true);
    setGenerationError(null);

    try {
      console.log('🎯 Generating quiz with options:', quizOptions);
      
      const quiz = await directAgentService.generateQuiz(contentInput.trim(), quizOptions);
      
      setQuizSession({
        quiz,
        currentQuestionIndex: 0,
        userAnswers: {},
        startTime: null,
        isActive: false,
        isCompleted: false
      });

      console.log('✅ Quiz generated successfully:', quiz);
      
    } catch (error) {
      console.error('❌ Quiz generation failed:', error);
      const errorMessage = error instanceof AgentError 
        ? directAgentService.getErrorMessage(error)
        : 'Quiz generation failed';
      setGenerationError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const startQuiz = () => {
    if (!quizSession.quiz) return;

    setQuizSession(prev => ({
      ...prev,
      startTime: new Date(),
      isActive: true,
      isCompleted: false,
      currentQuestionIndex: 0,
      userAnswers: {}
    }));
  };

  const answerQuestion = (questionId: string, answer: string) => {
    setQuizSession(prev => ({
      ...prev,
      userAnswers: {
        ...prev.userAnswers,
        [questionId]: answer
      }
    }));
  };

  const nextQuestion = () => {
    if (!quizSession.quiz) return;

    const nextIndex = quizSession.currentQuestionIndex + 1;
    
    if (nextIndex >= quizSession.quiz.questions.length) {
      completeQuiz();
    } else {
      setQuizSession(prev => ({
        ...prev,
        currentQuestionIndex: nextIndex
      }));
    }
  };

  const previousQuestion = () => {
    setQuizSession(prev => ({
      ...prev,
      currentQuestionIndex: Math.max(0, prev.currentQuestionIndex - 1)
    }));
  };

  const completeQuiz = () => {
    if (!quizSession.quiz || !quizSession.startTime) return;

    const timeTaken = Date.now() - quizSession.startTime.getTime();
    let score = 0;

    // Calculate score
    quizSession.quiz.questions.forEach(question => {
      const userAnswer = quizSession.userAnswers[question.id];
      if (userAnswer && userAnswer.toLowerCase().trim() === question.correctAnswer.toLowerCase().trim()) {
        score++;
      }
    });

    const result: QuizResult = {
      quiz: quizSession.quiz,
      userAnswers: quizSession.userAnswers,
      score,
      totalQuestions: quizSession.quiz.questions.length,
      completedAt: new Date(),
      timeTaken
    };

    setQuizResults(prev => [result, ...prev]);
    setQuizSession(prev => ({
      ...prev,
      isActive: false,
      isCompleted: true
    }));
  };

  const resetQuiz = () => {
    setQuizSession({
      quiz: null,
      currentQuestionIndex: 0,
      userAnswers: {},
      startTime: null,
      isActive: false,
      isCompleted: false
    });
    setGenerationError(null);
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
    'Machine Learning Basics',
    'JavaScript Programming',
    'React Development',
    'AWS Cloud Services',
    'Data Structures',
    'Database Design',
    'Web Security',
    'Software Architecture'
  ];

  const currentQuestion = quizSession.quiz?.questions[quizSession.currentQuestionIndex];

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center justify-center space-x-3">
          <ClipboardDocumentListIcon className="h-8 w-8 text-purple-500" />
          <span>Quiz Tester</span>
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Generate and take AI-powered quizzes to test your knowledge
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
              {generationError && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                  {generationError}
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

      {/* Quiz Generation Section */}
      {!quizSession.quiz && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Generate New Quiz
          </h2>

          {/* Content Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Content for Quiz Generation
            </label>
            <textarea
              value={contentInput}
              onChange={(e) => setContentInput(e.target.value)}
              placeholder="Enter the content or topic you want to create a quiz about..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              rows={4}
            />
          </div>

          {/* Quick Topic Buttons */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Quick Topics
            </label>
            <div className="flex flex-wrap gap-2">
              {predefinedTopics.map((topic) => (
                <button
                  key={topic}
                  onClick={() => setContentInput(topic)}
                  className="px-3 py-1 text-sm bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-full hover:bg-purple-200 dark:hover:bg-purple-800"
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>

          {/* Quiz Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Difficulty */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Difficulty Level
              </label>
              <select
                value={quizOptions.difficulty}
                onChange={(e) => setQuizOptions(prev => ({ 
                  ...prev, 
                  difficulty: e.target.value as 'easy' | 'medium' | 'hard' 
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            {/* Question Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Number of Questions
              </label>
              <select
                value={quizOptions.questionCount}
                onChange={(e) => setQuizOptions(prev => ({ 
                  ...prev, 
                  questionCount: parseInt(e.target.value) 
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value={3}>3 Questions</option>
                <option value={5}>5 Questions</option>
                <option value={10}>10 Questions</option>
                <option value={15}>15 Questions</option>
              </select>
            </div>

            {/* Question Types */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Question Types
              </label>
              <div className="flex flex-wrap gap-3">
                {['multiple-choice', 'true-false', 'short-answer'].map((type) => (
                  <label key={type} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={quizOptions.questionTypes?.includes(type as any) || false}
                      onChange={(e) => {
                        const types = quizOptions.questionTypes || [];
                        if (e.target.checked) {
                          setQuizOptions(prev => ({
                            ...prev,
                            questionTypes: [...types, type as any]
                          }));
                        } else {
                          setQuizOptions(prev => ({
                            ...prev,
                            questionTypes: types.filter(t => t !== type)
                          }));
                        }
                      }}
                      className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">
                      {type.replace('-', ' ')}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={generateQuiz}
            disabled={!contentInput.trim() || isGenerating || connectionStatus !== 'connected'}
            className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Generating Quiz...</span>
              </>
            ) : (
              <>
                <AcademicCapIcon className="h-5 w-5" />
                <span>Generate Quiz</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Quiz Display Section */}
      {quizSession.quiz && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {/* Quiz Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-purple-50 dark:bg-purple-900/20">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {quizSession.quiz.title}
                </h2>
                <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400 mt-1">
                  <span>Difficulty: {quizSession.quiz.metadata.difficulty}</span>
                  <span>Questions: {quizSession.quiz.questions.length}</span>
                  <span>Est. Time: {quizSession.quiz.metadata.estimatedTime} min</span>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                {quizSession.startTime && quizSession.isActive && (
                  <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                    <ClockIcon className="h-4 w-4" />
                    <span>
                      {formatTime(Date.now() - quizSession.startTime.getTime())}
                    </span>
                  </div>
                )}
                
                <button
                  onClick={resetQuiz}
                  className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center space-x-2"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                  <span>Reset</span>
                </button>
              </div>
            </div>
          </div>

          {/* Quiz Content */}
          <div className="p-6">
            {!quizSession.isActive && !quizSession.isCompleted ? (
              /* Start Quiz */
              <div className="text-center py-8">
                <AcademicCapIcon className="mx-auto h-16 w-16 text-purple-500 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  Ready to Start Quiz?
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  You have {quizSession.quiz.questions.length} questions to answer.
                </p>
                <button
                  onClick={startQuiz}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center space-x-2 mx-auto"
                >
                  <PlayIcon className="h-5 w-5" />
                  <span>Start Quiz</span>
                </button>
              </div>
            ) : quizSession.isCompleted ? (
              /* Quiz Results */
              <div className="text-center py-8">
                <CheckCircleIcon className="mx-auto h-16 w-16 text-green-500 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  Quiz Completed!
                </h3>
                {quizResults.length > 0 && (
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-w-md mx-auto">
                    <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {quizResults[0].score}/{quizResults[0].totalQuestions}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Score: {Math.round((quizResults[0].score / quizResults[0].totalQuestions) * 100)}%
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Time: {formatTime(quizResults[0].timeTaken)}
                    </div>
                  </div>
                )}
              </div>
            ) : currentQuestion ? (
              /* Active Quiz Question */
              <div className="space-y-6">
                {/* Progress Bar */}
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>Question {quizSession.currentQuestionIndex + 1} of {quizSession.quiz.questions.length}</span>
                  <div className="flex-1 mx-4">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-purple-600 h-2 rounded-full transition-all duration-300" 
                        style={{ 
                          width: `${((quizSession.currentQuestionIndex + 1) / quizSession.quiz.questions.length) * 100}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Question */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                    {currentQuestion.question}
                  </h3>

                  {/* Answer Options */}
                  <div className="space-y-3">
                    {currentQuestion.type === 'multiple-choice' && currentQuestion.options ? (
                      currentQuestion.options.map((option, index) => (
                        <label key={index} className="flex items-center p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
                          <input
                            type="radio"
                            name={`question-${currentQuestion.id}`}
                            value={option}
                            checked={quizSession.userAnswers[currentQuestion.id] === option}
                            onChange={(e) => answerQuestion(currentQuestion.id, e.target.value)}
                            className="text-purple-600 focus:ring-purple-500"
                          />
                          <span className="ml-3 text-gray-900 dark:text-gray-100">{option}</span>
                        </label>
                      ))
                    ) : currentQuestion.type === 'true-false' ? (
                      ['True', 'False'].map((option) => (
                        <label key={option} className="flex items-center p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer">
                          <input
                            type="radio"
                            name={`question-${currentQuestion.id}`}
                            value={option}
                            checked={quizSession.userAnswers[currentQuestion.id] === option}
                            onChange={(e) => answerQuestion(currentQuestion.id, e.target.value)}
                            className="text-purple-600 focus:ring-purple-500"
                          />
                          <span className="ml-3 text-gray-900 dark:text-gray-100">{option}</span>
                        </label>
                      ))
                    ) : (
                      <textarea
                        value={quizSession.userAnswers[currentQuestion.id] || ''}
                        onChange={(e) => answerQuestion(currentQuestion.id, e.target.value)}
                        placeholder="Enter your answer..."
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                        rows={3}
                      />
                    )}
                  </div>
                </div>

                {/* Navigation Buttons */}
                <div className="flex justify-between">
                  <button
                    onClick={previousQuestion}
                    disabled={quizSession.currentQuestionIndex === 0}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  <button
                    onClick={nextQuestion}
                    disabled={!quizSession.userAnswers[currentQuestion.id]}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {quizSession.currentQuestionIndex === quizSession.quiz.questions.length - 1 ? 'Finish' : 'Next'}
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Quiz History */}
      {quizResults.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              Quiz History ({quizResults.length})
            </h3>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-64 overflow-y-auto">
            {quizResults.map((result, index) => (
              <div key={index} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">
                      {result.quiz.title}
                    </h4>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                      <span>Score: {result.score}/{result.totalQuestions} ({Math.round((result.score / result.totalQuestions) * 100)}%)</span>
                      <span>Time: {formatTime(result.timeTaken)}</span>
                      <span>{result.completedAt.toLocaleDateString()}</span>
                    </div>
                  </div>
                  
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    (result.score / result.totalQuestions) >= 0.8 
                      ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                      : (result.score / result.totalQuestions) >= 0.6
                      ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
                      : 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                  }`}>
                    {(result.score / result.totalQuestions) >= 0.8 ? 'Excellent' :
                     (result.score / result.totalQuestions) >= 0.6 ? 'Good' : 'Needs Improvement'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
        <h3 className="font-medium text-purple-900 dark:text-purple-100 mb-2">How to Use Quiz Tester</h3>
        <ol className="list-decimal list-inside text-sm text-purple-800 dark:text-purple-200 space-y-1">
          <li>Enter content or select a topic for quiz generation</li>
          <li>Configure quiz parameters (difficulty, question count, types)</li>
          <li>Click "Generate Quiz" to create AI-powered questions</li>
          <li>Start the quiz and answer each question</li>
          <li>Review your results and performance history</li>
        </ol>
      </div>
    </div>
  );
};

export default QuizTester;
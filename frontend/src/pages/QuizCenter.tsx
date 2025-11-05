import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useMockAuth } from '../contexts/MockAuthContext';
import { apiBedrockAgentService } from '../services/apiBedrockAgentService';
import { directAgentService } from '../services/directAgentService';
import { mockDataService } from '../services/mockDataService';
import QuizTest from '../components/QuizTest';
import { useHybridMode, useAgentService } from '../hooks/useHybridMode';
import HybridModeIndicator from '../components/HybridModeIndicator';
import { 
  PlayIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrophyIcon,
  DocumentTextIcon,
  AcademicCapIcon,
  ChartBarIcon,
  StarIcon,
  SparklesIcon,
  BookOpenIcon,
  ExclamationTriangleIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

interface Quiz {
  id: string;
  title: string;
  description: string;
  questionCount: number;
  duration: number; // in minutes
  difficulty: 'easy' | 'medium' | 'hard';
  subject: string;
  createdDate: string;
  attempts: number;
  bestScore?: number;
  status: 'available' | 'completed' | 'in-progress';
  sourceDocument?: string;
  generatedBy?: 'ai' | 'manual';
  questions?: QuizQuestion[];
}

interface QuizQuestion {
  id: string;
  type: 'multiple-choice' | 'true-false' | 'short-answer';
  question: string;
  options?: string[];
  correctAnswer: string | number;
  explanation?: string;
  points: number;
}

interface QuizAttempt {
  id: string;
  quizId: string;
  score: number;
  totalQuestions: number;
  completedAt: string;
  timeSpent: number; // in minutes
  answers: { [questionId: string]: string | number };
  feedback?: string;
}

interface QuizSession {
  id: string;
  quiz: Quiz;
  currentQuestionIndex: number;
  answers: { [questionId: string]: string | number };
  startTime: Date;
  timeRemaining: number; // in seconds
  isActive: boolean;
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

// Hook to detect hybrid testing mode (keeping for backward compatibility)
const useHybridModeCompat = () => {
  return import.meta.env.VITE_USE_MOCK_AUTH === 'true' && 
         import.meta.env.VITE_USE_MOCK_AGENT === 'false';
};

const QuizCenter: React.FC = () => {
  const { user } = useAuthContext();
  const { isHybridMode, isAgentConnected } = useHybridMode();
  const { agentService, agentServiceType } = useAgentService();
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [recentAttempts, setRecentAttempts] = useState<QuizAttempt[]>([]);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [currentQuizSession, setCurrentQuizSession] = useState<QuizSession | null>(null);
  const [showQuizInterface, setShowQuizInterface] = useState(false);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<string>('');
  const [showQuizTest, setShowQuizTest] = useState(false);

  // Initialize quiz data
  useEffect(() => {
    const initializeQuizCenter = async () => {
      try {

        // Load existing quizzes (mock data for now, would be from backend)
        const mockQuizzes: Quiz[] = [
          {
            id: '1',
            title: 'Machine Learning Fundamentals',
            description: 'Test your understanding of basic ML concepts, algorithms, and applications',
            questionCount: 15,
            duration: 30,
            difficulty: 'medium',
            subject: 'Machine Learning',
            createdDate: '2024-01-15',
            attempts: 2,
            bestScore: 85,
            status: 'completed',
            generatedBy: 'manual'
          },
          {
            id: '2',
            title: 'Data Structures Quiz',
            description: 'Arrays, linked lists, stacks, queues, and trees',
            questionCount: 20,
            duration: 45,
            difficulty: 'hard',
            subject: 'Computer Science',
            createdDate: '2024-01-14',
            attempts: 1,
            bestScore: 72,
            status: 'completed',
            generatedBy: 'manual'
          },
          {
            id: '3',
            title: 'Algorithm Complexity',
            description: 'Big O notation, time and space complexity analysis',
            questionCount: 12,
            duration: 25,
            difficulty: 'medium',
            subject: 'Algorithms',
            createdDate: '2024-01-13',
            attempts: 0,
            status: 'available',
            generatedBy: 'manual'
          }
        ];

        const mockAttempts: QuizAttempt[] = [
          {
            id: '1',
            quizId: '1',
            score: 13,
            totalQuestions: 15,
            completedAt: '2024-01-15T14:30:00',
            timeSpent: 28,
            answers: {}
          },
          {
            id: '2',
            quizId: '2',
            score: 14,
            totalQuestions: 20,
            completedAt: '2024-01-14T16:45:00',
            timeSpent: 42,
            answers: {}
          }
        ];

        setQuizzes(mockQuizzes);
        setRecentAttempts(mockAttempts);
      } catch (error) {
        console.error('Failed to initialize quiz center:', error);
      }
    };

    initializeQuizCenter();
  }, []);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'hard': return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'in-progress':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <PlayIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  const generateQuizFromDocument = async () => {
    if (!selectedDocument) {
      alert('Please select a document to generate quiz from');
      return;
    }

    setGeneratingQuiz(true);
    try {
      // Get user documents
      const documents = mockDataService.getDocuments(undefined, user?.id);
      const document = documents.find(d => d.id === selectedDocument);
      
      if (!document) {
        throw new Error('Selected document not found');
      }

      let quizData;

      if (agentServiceType === 'direct') {
        // Use DirectAgentService for hybrid mode
        console.log('🔄 Generating quiz using DirectAgentService...');
        
        const documentContent = `Document: ${document.name}\nContent: ${(document as any).content || document.name || 'Document content not available'}`;
        
        const quiz = await directAgentService.generateQuiz(documentContent, {
          difficulty: 'medium',
          questionCount: 10,
          topics: [document.name],
          questionTypes: ['multiple-choice', 'true-false', 'short-answer']
        });

        // Convert DirectAgentService quiz format to our format
        quizData = {
          title: quiz.title,
          description: `AI-generated quiz based on ${document.name}`,
          difficulty: quiz.metadata.difficulty,
          estimatedDuration: quiz.metadata.estimatedTime,
          questions: quiz.questions.map(q => ({
            id: q.id,
            type: q.type,
            question: q.question,
            options: q.options,
            correctAnswer: q.type === 'multiple-choice' ? 
              (q.options?.indexOf(q.correctAnswer) || 0) : q.correctAnswer,
            explanation: q.explanation,
            points: 1
          }))
        };
      } else if (agentServiceType === 'api') {
        // Use existing API service for normal mode
        const sessionId = apiBedrockAgentService.generateSessionId(user?.id);
        
        const quizPrompt = `Generate a comprehensive quiz based on the document "${document.name}". 
        
        Please create a quiz with the following specifications:
        - 10-15 multiple choice questions
        - 3-5 true/false questions  
        - 2-3 short answer questions
        - Mix of difficulty levels (easy, medium, hard)
        - Include explanations for correct answers
        - Focus on key concepts and important details
        
        Format the response as a JSON object with the following structure:
        {
          "title": "Quiz title based on document content",
          "description": "Brief description of what the quiz covers",
          "difficulty": "medium",
          "estimatedDuration": 25,
          "questions": [
            {
              "id": "q1",
              "type": "multiple-choice",
              "question": "Question text",
              "options": ["Option A", "Option B", "Option C", "Option D"],
              "correctAnswer": 0,
              "explanation": "Why this answer is correct",
              "points": 1
            }
          ]
        }`;

        const response = await apiBedrockAgentService.sendMessage(
          quizPrompt,
          sessionId,
          user?.id,
          {
            action: 'generate_quiz',
            document: document.name,
            userId: user?.id
          }
        );

        if (response.success) {
          quizData = parseQuizFromAgentResponse(response.message.content, document);
        } else {
          throw new Error(response.error || 'Failed to generate quiz');
        }
      } else {
        // Mock mode - generate fallback quiz
        console.log('🔄 Generating mock quiz...');
        
        quizData = {
          title: `Mock Quiz: ${document.name}`,
          description: `Mock quiz generated from ${document.name}`,
          difficulty: 'medium',
          estimatedDuration: 15,
          questions: generateFallbackQuestions(document.name)
        };
      }
      
      if (quizData) {
        const newQuiz: Quiz = {
          id: Date.now().toString(),
          title: quizData.title || `Quiz: ${document.name}`,
          description: quizData.description || `AI-generated quiz based on ${document.name}`,
          questionCount: quizData.questions?.length || 10,
          duration: quizData.estimatedDuration || 25,
          difficulty: quizData.difficulty || 'medium',
          subject: 'AI Generated',
          createdDate: new Date().toISOString().split('T')[0],
          attempts: 0,
          status: 'available',
          sourceDocument: document.name,
          generatedBy: 'ai',
          questions: quizData.questions
        };
        
        setQuizzes(prev => [newQuiz, ...prev]);
        setSelectedDocument('');
        
        // Show success message
        alert(`Quiz "${newQuiz.title}" generated successfully!`);
      } else {
        throw new Error('Failed to parse quiz from agent response');
      }
    } catch (error) {
      console.error('Quiz generation failed:', error);
      alert(`Failed to generate quiz: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setGeneratingQuiz(false);
    }
  };

  const parseQuizFromAgentResponse = (content: string, document: any) => {
    try {
      // Try to extract JSON from the response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const quizData = JSON.parse(jsonMatch[0]);
        return quizData;
      }
      
      // Fallback: create a simple quiz structure
      return {
        title: `Quiz: ${document.name}`,
        description: `AI-generated quiz based on ${document.name}`,
        difficulty: 'medium',
        estimatedDuration: 20,
        questions: generateFallbackQuestions(document.name)
      };
    } catch (error) {
      console.error('Failed to parse quiz JSON:', error);
      return null;
    }
  };

  const generateFallbackQuestions = (documentName: string): QuizQuestion[] => {
    return [
      {
        id: 'q1',
        type: 'multiple-choice',
        question: `What is the main topic covered in ${documentName}?`,
        options: ['Machine Learning', 'Data Structures', 'Web Development', 'Algorithms'],
        correctAnswer: 0,
        explanation: 'This question tests understanding of the document\'s main subject.',
        points: 1
      },
      {
        id: 'q2',
        type: 'true-false',
        question: 'The concepts in this document are fundamental to computer science.',
        correctAnswer: 'true',
        explanation: 'Most educational documents cover fundamental concepts.',
        points: 1
      },
      {
        id: 'q3',
        type: 'short-answer',
        question: 'Describe one key concept you learned from this document.',
        correctAnswer: 'Various answers accepted',
        explanation: 'This tests comprehension and ability to articulate learning.',
        points: 2
      }
    ];
  };

  const startQuiz = (quiz: Quiz) => {
    if (!quiz.questions || quiz.questions.length === 0) {
      alert('This quiz does not have questions available. Please generate a new quiz.');
      return;
    }

    const session: QuizSession = {
      id: `session-${Date.now()}`,
      quiz: quiz,
      currentQuestionIndex: 0,
      answers: {},
      startTime: new Date(),
      timeRemaining: quiz.duration * 60, // Convert minutes to seconds
      isActive: true
    };

    setCurrentQuizSession(session);
    setShowQuizInterface(true);
  };

  const submitAnswer = (questionId: string, answer: string | number) => {
    if (!currentQuizSession) return;

    const updatedSession = {
      ...currentQuizSession,
      answers: {
        ...currentQuizSession.answers,
        [questionId]: answer
      }
    };

    setCurrentQuizSession(updatedSession);
  };

  const nextQuestion = () => {
    if (!currentQuizSession?.quiz.questions) return;

    const nextIndex = currentQuizSession.currentQuestionIndex + 1;
    
    if (nextIndex >= currentQuizSession.quiz.questions.length) {
      // Quiz completed
      finishQuiz();
    } else {
      setCurrentQuizSession({
        ...currentQuizSession,
        currentQuestionIndex: nextIndex
      });
    }
  };

  const previousQuestion = () => {
    if (!currentQuizSession) return;

    const prevIndex = Math.max(0, currentQuizSession.currentQuestionIndex - 1);
    setCurrentQuizSession({
      ...currentQuizSession,
      currentQuestionIndex: prevIndex
    });
  };

  const finishQuiz = () => {
    if (!currentQuizSession) return;

    const { quiz, answers, startTime } = currentQuizSession;
    const endTime = new Date();
    const timeSpent = Math.round((endTime.getTime() - startTime.getTime()) / 60000); // minutes

    // Calculate score
    let correctAnswers = 0;
    let totalPoints = 0;

    if (quiz.questions) {
      quiz.questions.forEach(question => {
        const userAnswer = answers[question.id];
        totalPoints += question.points;
        
        if (question.type === 'multiple-choice' && userAnswer === question.correctAnswer) {
          correctAnswers += question.points;
        } else if (question.type === 'true-false' && userAnswer === question.correctAnswer) {
          correctAnswers += question.points;
        } else if (question.type === 'short-answer' && userAnswer) {
          // For short answer, give partial credit if answered
          correctAnswers += question.points * 0.8;
        }
      });
    }

    const finalScore = Math.round((correctAnswers / totalPoints) * 100);

    // Create quiz attempt record
    const attempt: QuizAttempt = {
      id: `attempt-${Date.now()}`,
      quizId: quiz.id,
      score: correctAnswers,
      totalQuestions: quiz.questions?.length || 0,
      completedAt: endTime.toISOString(),
      timeSpent: timeSpent,
      answers: answers,
      feedback: `You scored ${finalScore}% (${correctAnswers}/${totalPoints} points)`
    };

    // Update quiz attempts
    setRecentAttempts(prev => [attempt, ...prev]);

    // Update quiz status and best score
    setQuizzes(prev => prev.map(q => {
      if (q.id === quiz.id) {
        return {
          ...q,
          attempts: q.attempts + 1,
          bestScore: Math.max(q.bestScore || 0, finalScore),
          status: 'completed' as const
        };
      }
      return q;
    }));

    // Close quiz interface
    setCurrentQuizSession(null);
    setShowQuizInterface(false);

    // Show results
    alert(`Quiz completed! Your score: ${finalScore}% (${correctAnswers}/${totalPoints} points)`);
  };

  const subjects = Array.from(new Set(quizzes.map(q => q.subject)));
  
  const filteredQuizzes = quizzes.filter(quiz => {
    const matchesDifficulty = selectedDifficulty === 'all' || quiz.difficulty === selectedDifficulty;
    const matchesSubject = selectedSubject === 'all' || quiz.subject === selectedSubject;
    return matchesDifficulty && matchesSubject;
  });

  const averageScore = recentAttempts.length > 0 
    ? Math.round(recentAttempts.reduce((sum, attempt) => sum + (attempt.score / attempt.totalQuestions * 100), 0) / recentAttempts.length)
    : 0;

  // Get user documents for quiz generation
  const userDocuments = mockDataService.getDocuments(undefined, user?.id);

  // Quiz Interface Component
  const QuizInterface: React.FC = () => {
    if (!currentQuizSession || !currentQuizSession.quiz.questions) return null;

    const { quiz, currentQuestionIndex, answers } = currentQuizSession;
    const currentQuestion = quiz.questions?.[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / (quiz.questions?.length || 1)) * 100;
    
    if (!currentQuestion) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          {/* Quiz Header */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {quiz.title}
              </h2>
              <button
                onClick={() => {
                  if (confirm('Are you sure you want to exit the quiz? Your progress will be lost.')) {
                    setCurrentQuizSession(null);
                    setShowQuizInterface(false);
                  }
                }}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <XCircleIcon className="h-6 w-6" />
              </button>
            </div>
            
            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                <span>Question {currentQuestionIndex + 1} of {quiz.questions?.length || 0}</span>
                <span>{Math.round(progress)}% Complete</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Question Content */}
          <div className="p-6">
            <div className="mb-6">
              <div className="flex items-center mb-4">
                <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full text-sm font-medium">
                  {currentQuestion.type.replace('-', ' ').toUpperCase()}
                </span>
                <span className="ml-3 text-sm text-gray-500 dark:text-gray-400">
                  {currentQuestion.points} {currentQuestion.points === 1 ? 'point' : 'points'}
                </span>
              </div>
              
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                {currentQuestion.question}
              </h3>
            </div>

            {/* Answer Options */}
            <div className="space-y-3">
              {currentQuestion.type === 'multiple-choice' && currentQuestion.options && (
                currentQuestion.options.map((option, index) => (
                  <label
                    key={index}
                    className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
                      answers[currentQuestion.id] === index
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      value={index}
                      checked={answers[currentQuestion.id] === index}
                      onChange={() => submitAnswer(currentQuestion.id, index)}
                      className="mr-3 text-blue-500"
                    />
                    <span className="text-gray-900 dark:text-gray-100">{option}</span>
                  </label>
                ))
              )}

              {currentQuestion.type === 'true-false' && (
                <>
                  <label
                    className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
                      answers[currentQuestion.id] === 'true'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      value="true"
                      checked={answers[currentQuestion.id] === 'true'}
                      onChange={() => submitAnswer(currentQuestion.id, 'true')}
                      className="mr-3 text-blue-500"
                    />
                    <span className="text-gray-900 dark:text-gray-100">True</span>
                  </label>
                  <label
                    className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
                      answers[currentQuestion.id] === 'false'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      value="false"
                      checked={answers[currentQuestion.id] === 'false'}
                      onChange={() => submitAnswer(currentQuestion.id, 'false')}
                      className="mr-3 text-blue-500"
                    />
                    <span className="text-gray-900 dark:text-gray-100">False</span>
                  </label>
                </>
              )}

              {currentQuestion.type === 'short-answer' && (
                <textarea
                  value={answers[currentQuestion.id] as string || ''}
                  onChange={(e) => submitAnswer(currentQuestion.id, e.target.value)}
                  placeholder="Type your answer here..."
                  rows={4}
                  className="w-full p-4 border border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
                />
              )}
            </div>
          </div>

          {/* Navigation */}
          <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <button
              onClick={previousQuestion}
              disabled={currentQuestionIndex === 0}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 disabled:opacity-50 disabled:cursor-not-allowed hover:text-gray-800 dark:hover:text-gray-200"
            >
              Previous
            </button>
            
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {Object.keys(answers).length} of {quiz.questions?.length || 0} answered
            </div>
            
            {currentQuestionIndex === (quiz.questions?.length || 1) - 1 ? (
              <button
                onClick={finishQuiz}
                className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                Finish Quiz
              </button>
            ) : (
              <button
                onClick={nextQuestion}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 safe-area-padding transition-colors">
      {/* Quiz Interface Modal */}
      {showQuizInterface && <QuizInterface />}
      
      {/* Quiz Test Modal */}
      {showQuizTest && <QuizTest onClose={() => setShowQuizTest(false)} />}
      
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container-responsive">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-4 sm:py-6 space-y-3 sm:space-y-0">
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Quiz Center
                </h1>
                <HybridModeIndicator />
              </div>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mt-1">
                {isAgentConnected 
                  ? `Generate ${agentServiceType === 'mock' ? 'mock' : 'AI-powered'} quizzes from your study materials`
                  : 'AI quiz generation temporarily unavailable'
                }
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              {/* Test Button */}
              <button
                onClick={() => setShowQuizTest(true)}
                className="btn-mobile bg-gray-600 hover:bg-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 shadow-sm inline-flex items-center justify-center sm:justify-start"
              >
                <BeakerIcon className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                <span className="text-sm sm:text-base">Test Quiz</span>
              </button>
              
              {/* Document Selection for Quiz Generation */}
              {agentConnected && userDocuments.length > 0 && (
                <div className="flex items-center space-x-2">
                  <select
                    value={selectedDocument}
                    onChange={(e) => setSelectedDocument(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100 text-sm"
                  >
                    <option value="">Select document...</option>
                    {userDocuments.map(doc => (
                      <option key={doc.id} value={doc.id}>
                        {doc.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              
              <button
                onClick={generateQuizFromDocument}
                disabled={generatingQuiz || !selectedDocument || (agentServiceType !== 'mock' && !isAgentConnected)}
                className="btn-mobile bg-blue-600 hover:bg-blue-700 text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 shadow-sm inline-flex items-center justify-center sm:justify-start disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generatingQuiz ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <SparklesIcon className="h-4 w-4 sm:h-5 sm:w-5 mr-2" />
                )}
                <span className="text-sm sm:text-base">
                  {generatingQuiz ? 'Generating...' : 
                   agentServiceType === 'mock' ? 'Generate Mock Quiz' : 'Generate AI Quiz'}
                </span>
              </button>
            </div>
          </div>
          
          {/* Agent Status and Documents Info */}
          {agentConnected && (
            <div className="pb-4">
              <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex items-center space-x-1">
                  <BookOpenIcon className="h-4 w-4" />
                  <span>{userDocuments.length} documents available</span>
                </div>
                <div className="flex items-center space-x-1">
                  <SparklesIcon className="h-4 w-4 text-blue-500" />
                  <span className="text-blue-600 dark:text-blue-400">AI-powered quiz generation</span>
                </div>
              </div>
            </div>
          )}
          
          {/* No Documents Warning */}
          {agentConnected && userDocuments.length === 0 && (
            <div className="pb-4">
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2" />
                  <span className="text-sm text-yellow-800 dark:text-yellow-200">
                    No documents found. Upload study materials to generate AI quizzes.
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="container-responsive py-6 sm:py-8">
        {/* Stats Overview */}
        <div className="grid-responsive-4 mb-6 sm:mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center">
              <AcademicCapIcon className="h-6 w-6 sm:h-8 sm:w-8 text-blue-500 flex-shrink-0" />
              <div className="ml-3 sm:ml-4">
                <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {quizzes.length}
                </div>
                <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Available Quizzes</div>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center">
              <TrophyIcon className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-500 flex-shrink-0" />
              <div className="ml-3 sm:ml-4">
                <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {averageScore}%
                </div>
                <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Average Score</div>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center">
              <CheckCircleIcon className="h-6 w-6 sm:h-8 sm:w-8 text-green-500 flex-shrink-0" />
              <div className="ml-3 sm:ml-4">
                <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {quizzes.filter(q => q.status === 'completed').length}
                </div>
                <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Completed</div>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-6 w-6 sm:h-8 sm:w-8 text-purple-500 flex-shrink-0" />
              <div className="ml-3 sm:ml-4">
                <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {recentAttempts.length}
                </div>
                <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Total Attempts</div>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Difficulty
              </label>
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
              >
                <option value="all">All Difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Subject
              </label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
              >
                <option value="all">All Subjects</option>
                {subjects.map(subject => (
                  <option key={subject} value={subject}>{subject}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quizzes List */}
          <div className="lg:col-span-2">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Available Quizzes ({filteredQuizzes.length})
            </h2>
            
            <div className="space-y-4">
              {filteredQuizzes.map((quiz) => (
                <div key={quiz.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                          {quiz.title}
                        </h3>
                        {quiz.generatedBy === 'ai' && (
                          <div className="flex items-center space-x-1 px-2 py-1 bg-purple-100 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 rounded-full text-xs">
                            <SparklesIcon className="h-3 w-3" />
                            <span>AI Generated</span>
                          </div>
                        )}
                        {getStatusIcon(quiz.status)}
                      </div>
                      
                      <p className="text-gray-600 dark:text-gray-300 mb-3">
                        {quiz.description}
                      </p>
                      
                      {quiz.sourceDocument && (
                        <div className="flex items-center text-sm text-blue-600 dark:text-blue-400 mb-3">
                          <DocumentTextIcon className="h-4 w-4 mr-1" />
                          <span>Generated from: {quiz.sourceDocument}</span>
                        </div>
                      )}
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-4">
                        <div className="flex items-center">
                          <DocumentTextIcon className="h-4 w-4 mr-1" />
                          {quiz.questionCount} questions
                        </div>
                        <div className="flex items-center">
                          <ClockIcon className="h-4 w-4 mr-1" />
                          {quiz.duration} minutes
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(quiz.difficulty)}`}>
                          {quiz.difficulty}
                        </span>
                        <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                          {quiz.subject}
                        </span>
                      </div>
                      
                      {quiz.bestScore && (
                        <div className="flex items-center text-sm text-green-600 dark:text-green-400 mb-3">
                          <StarIcon className="h-4 w-4 mr-1" />
                          Best Score: {quiz.bestScore}% ({quiz.attempts} attempts)
                        </div>
                      )}
                    </div>
                    
                    <button 
                      onClick={() => startQuiz(quiz)}
                      className="ml-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center"
                    >
                      <PlayIcon className="h-4 w-4 mr-2" />
                      {quiz.status === 'completed' ? 'Retake' : 'Start'}
                    </button>
                  </div>
                </div>
              ))}
              
              {filteredQuizzes.length === 0 && (
                <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <AcademicCapIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    No quizzes found
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Try adjusting your filters or generate a new quiz
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Recent Attempts Sidebar */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Recent Attempts
            </h2>
            
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              {recentAttempts.length === 0 ? (
                <div className="p-6 text-center">
                  <ChartBarIcon className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No attempts yet
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {recentAttempts.map((attempt) => {
                    const quiz = quizzes.find(q => q.id === attempt.quizId);
                    const percentage = Math.round((attempt.score / attempt.totalQuestions) * 100);
                    
                    return (
                      <div key={attempt.id} className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900 dark:text-gray-100 text-sm truncate">
                            {quiz?.title}
                          </h4>
                          <span className={`text-sm font-semibold ${
                            percentage >= 80 ? 'text-green-600' : 
                            percentage >= 60 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {percentage}%
                          </span>
                        </div>
                        
                        <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
                          <div>{attempt.score}/{attempt.totalQuestions} correct</div>
                          <div>{attempt.timeSpent} minutes</div>
                          <div>{new Date(attempt.completedAt).toLocaleDateString()}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            
            {/* Quick Actions */}
            <div className="mt-6 space-y-3">
              <button className="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center">
                <ChartBarIcon className="h-4 w-4 mr-2" />
                View Analytics
              </button>
              
              <button className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-center">
                <DocumentTextIcon className="h-4 w-4 mr-2" />
                Study Materials
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuizCenter;
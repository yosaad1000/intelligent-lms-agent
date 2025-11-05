import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import {
  CogIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon,
  DocumentTextIcon,
  MicrophoneIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface AIConfig {
  general: {
    responseStyle: 'formal' | 'casual' | 'adaptive';
    verbosity: 'concise' | 'detailed' | 'comprehensive';
    language: string;
    personalityTraits: string[];
  };
  chat: {
    maxResponseLength: number;
    contextWindow: number;
    enableCitations: boolean;
    allowFollowUps: boolean;
    responseDelay: number;
  };
  quizGeneration: {
    defaultQuestionCount: number;
    difficultyDistribution: {
      easy: number;
      medium: number;
      hard: number;
    };
    questionTypes: string[];
    includeExplanations: boolean;
  };
  voiceInterviews: {
    speechRate: 'slow' | 'normal' | 'fast';
    pauseDuration: number;
    enableTranscription: boolean;
    feedbackDetail: 'basic' | 'detailed' | 'comprehensive';
  };
  contentAnalysis: {
    analysisDepth: 'surface' | 'moderate' | 'deep';
    enableSentiment: boolean;
    extractKeywords: boolean;
    generateSummaries: boolean;
  };
}

const TeacherAIConfig: React.FC = () => {
  const { user } = useAuth();
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeSection, setActiveSection] = useState<'general' | 'chat' | 'quiz' | 'voice' | 'content'>('general');
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchAIConfig();
  }, []);

  const fetchAIConfig = async () => {
    try {
      // Simulate API call with default config
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setConfig({
        general: {
          responseStyle: 'adaptive',
          verbosity: 'detailed',
          language: 'en',
          personalityTraits: ['helpful', 'encouraging', 'patient']
        },
        chat: {
          maxResponseLength: 500,
          contextWindow: 10,
          enableCitations: true,
          allowFollowUps: true,
          responseDelay: 1000
        },
        quizGeneration: {
          defaultQuestionCount: 10,
          difficultyDistribution: {
            easy: 30,
            medium: 50,
            hard: 20
          },
          questionTypes: ['multiple-choice', 'true-false', 'short-answer'],
          includeExplanations: true
        },
        voiceInterviews: {
          speechRate: 'normal',
          pauseDuration: 2000,
          enableTranscription: true,
          feedbackDetail: 'detailed'
        },
        contentAnalysis: {
          analysisDepth: 'moderate',
          enableSentiment: true,
          extractKeywords: true,
          generateSummaries: true
        }
      });
    } catch (error) {
      console.error('Error fetching AI config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (section: keyof AIConfig, field: string, value: any) => {
    if (!config) return;
    
    setConfig(prev => ({
      ...prev!,
      [section]: {
        ...prev![section],
        [field]: value
      }
    }));
    setHasChanges(true);
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving config:', error);
    } finally {
      setSaving(false);
    }
  };

  const resetToDefaults = () => {
    fetchAIConfig();
    setHasChanges(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-600 dark:text-gray-400">Loading AI configuration...</p>
        </div>
      </div>
    );
  }

  if (!config) return null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 safe-area-padding">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container-responsive">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-6 space-y-4 sm:space-y-0">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                <SparklesIcon className="h-7 w-7 mr-3 text-blue-500" />
                AI Configuration
              </h1>
              <p className="text-gray-600 dark:text-gray-300 mt-1">
                Customize AI behavior and responses for your teaching style
              </p>
            </div>
            
            <div className="flex space-x-3">
              {hasChanges && (
                <button
                  onClick={resetToDefaults}
                  className="btn-mobile bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300"
                >
                  Reset
                </button>
              )}
              <button
                onClick={handleSaveConfig}
                disabled={!hasChanges || saving}
                className={`btn-mobile ${
                  hasChanges && !saving
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                }`}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container-responsive py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Navigation Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">Configuration Sections</h3>
              <nav className="space-y-2">
                <button
                  onClick={() => setActiveSection('general')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeSection === 'general'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <CogIcon className="h-4 w-4 mr-3" />
                  General Settings
                </button>
                <button
                  onClick={() => setActiveSection('chat')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeSection === 'chat'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <ChatBubbleLeftRightIcon className="h-4 w-4 mr-3" />
                  AI Chat
                </button>
                <button
                  onClick={() => setActiveSection('quiz')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeSection === 'quiz'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <DocumentTextIcon className="h-4 w-4 mr-3" />
                  Quiz Generation
                </button>
                <button
                  onClick={() => setActiveSection('voice')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeSection === 'voice'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <MicrophoneIcon className="h-4 w-4 mr-3" />
                  Voice Interviews
                </button>
                <button
                  onClick={() => setActiveSection('content')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeSection === 'content'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <AdjustmentsHorizontalIcon className="h-4 w-4 mr-3" />
                  Content Analysis
                </button>
              </nav>
            </div>
          </div>

          {/* Configuration Content */}
          <div className="lg:col-span-3">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              {activeSection === 'general' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">General AI Settings</h3>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Response Style
                      </label>
                      <select
                        value={config.general.responseStyle}
                        onChange={(e) => handleConfigChange('general', 'responseStyle', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="formal">Formal - Professional and structured</option>
                        <option value="casual">Casual - Friendly and conversational</option>
                        <option value="adaptive">Adaptive - Matches student's communication style</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Response Verbosity
                      </label>
                      <select
                        value={config.general.verbosity}
                        onChange={(e) => handleConfigChange('general', 'verbosity', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="concise">Concise - Brief and to the point</option>
                        <option value="detailed">Detailed - Comprehensive explanations</option>
                        <option value="comprehensive">Comprehensive - Thorough with examples</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Primary Language
                      </label>
                      <select
                        value={config.general.language}
                        onChange={(e) => handleConfigChange('general', 'language', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="zh">Chinese</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        AI Personality Traits
                      </label>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {['helpful', 'encouraging', 'patient', 'analytical', 'creative', 'supportive'].map((trait) => (
                          <label key={trait} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={config.general.personalityTraits.includes(trait)}
                              onChange={(e) => {
                                const traits = e.target.checked
                                  ? [...config.general.personalityTraits, trait]
                                  : config.general.personalityTraits.filter(t => t !== trait);
                                handleConfigChange('general', 'personalityTraits', traits);
                              }}
                              className="rounded border-gray-300 dark:border-gray-600"
                            />
                            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">{trait}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'chat' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">AI Chat Configuration</h3>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Maximum Response Length (characters)
                      </label>
                      <input
                        type="number"
                        value={config.chat.maxResponseLength}
                        onChange={(e) => handleConfigChange('chat', 'maxResponseLength', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        min="100"
                        max="2000"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Context Window (previous messages)
                      </label>
                      <input
                        type="number"
                        value={config.chat.contextWindow}
                        onChange={(e) => handleConfigChange('chat', 'contextWindow', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        min="1"
                        max="50"
                      />
                    </div>

                    <div className="space-y-4">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={config.chat.enableCitations}
                          onChange={(e) => handleConfigChange('chat', 'enableCitations', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Enable source citations in responses
                        </span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={config.chat.allowFollowUps}
                          onChange={(e) => handleConfigChange('chat', 'allowFollowUps', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Allow follow-up questions
                        </span>
                      </label>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Response Delay (milliseconds)
                      </label>
                      <input
                        type="number"
                        value={config.chat.responseDelay}
                        onChange={(e) => handleConfigChange('chat', 'responseDelay', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        min="0"
                        max="5000"
                        step="100"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Simulates thinking time for more natural conversation
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'quiz' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Quiz Generation Settings</h3>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Default Number of Questions
                      </label>
                      <input
                        type="number"
                        value={config.quizGeneration.defaultQuestionCount}
                        onChange={(e) => handleConfigChange('quizGeneration', 'defaultQuestionCount', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        min="1"
                        max="50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                        Difficulty Distribution (%)
                      </label>
                      <div className="space-y-3">
                        <div className="flex items-center space-x-4">
                          <label className="w-16 text-sm text-gray-600 dark:text-gray-400">Easy:</label>
                          <input
                            type="number"
                            value={config.quizGeneration.difficultyDistribution.easy}
                            onChange={(e) => {
                              const newDist = { ...config.quizGeneration.difficultyDistribution, easy: parseInt(e.target.value) };
                              handleConfigChange('quizGeneration', 'difficultyDistribution', newDist);
                            }}
                            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            min="0"
                            max="100"
                          />
                          <span className="text-sm text-gray-500">%</span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <label className="w-16 text-sm text-gray-600 dark:text-gray-400">Medium:</label>
                          <input
                            type="number"
                            value={config.quizGeneration.difficultyDistribution.medium}
                            onChange={(e) => {
                              const newDist = { ...config.quizGeneration.difficultyDistribution, medium: parseInt(e.target.value) };
                              handleConfigChange('quizGeneration', 'difficultyDistribution', newDist);
                            }}
                            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            min="0"
                            max="100"
                          />
                          <span className="text-sm text-gray-500">%</span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <label className="w-16 text-sm text-gray-600 dark:text-gray-400">Hard:</label>
                          <input
                            type="number"
                            value={config.quizGeneration.difficultyDistribution.hard}
                            onChange={(e) => {
                              const newDist = { ...config.quizGeneration.difficultyDistribution, hard: parseInt(e.target.value) };
                              handleConfigChange('quizGeneration', 'difficultyDistribution', newDist);
                            }}
                            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                            min="0"
                            max="100"
                          />
                          <span className="text-sm text-gray-500">%</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Question Types
                      </label>
                      <div className="space-y-2">
                        {['multiple-choice', 'true-false', 'short-answer', 'essay', 'fill-in-blank'].map((type) => (
                          <label key={type} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={config.quizGeneration.questionTypes.includes(type)}
                              onChange={(e) => {
                                const types = e.target.checked
                                  ? [...config.quizGeneration.questionTypes, type]
                                  : config.quizGeneration.questionTypes.filter(t => t !== type);
                                handleConfigChange('quizGeneration', 'questionTypes', types);
                              }}
                              className="rounded border-gray-300 dark:border-gray-600"
                            />
                            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">
                              {type.replace('-', ' ')}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>

                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={config.quizGeneration.includeExplanations}
                          onChange={(e) => handleConfigChange('quizGeneration', 'includeExplanations', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Include explanations for correct answers
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'voice' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Voice Interview Settings</h3>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Speech Rate
                      </label>
                      <select
                        value={config.voiceInterviews.speechRate}
                        onChange={(e) => handleConfigChange('voiceInterviews', 'speechRate', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="slow">Slow - For language learners</option>
                        <option value="normal">Normal - Standard pace</option>
                        <option value="fast">Fast - For advanced students</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Pause Duration Between Questions (milliseconds)
                      </label>
                      <input
                        type="number"
                        value={config.voiceInterviews.pauseDuration}
                        onChange={(e) => handleConfigChange('voiceInterviews', 'pauseDuration', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        min="500"
                        max="10000"
                        step="500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Feedback Detail Level
                      </label>
                      <select
                        value={config.voiceInterviews.feedbackDetail}
                        onChange={(e) => handleConfigChange('voiceInterviews', 'feedbackDetail', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="basic">Basic - Simple pass/fail</option>
                        <option value="detailed">Detailed - Specific improvements</option>
                        <option value="comprehensive">Comprehensive - Full analysis</option>
                      </select>
                    </div>

                    <div>
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={config.voiceInterviews.enableTranscription}
                          onChange={(e) => handleConfigChange('voiceInterviews', 'enableTranscription', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Enable automatic transcription
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'content' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Content Analysis Configuration</h3>
                  
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Analysis Depth
                      </label>
                      <select
                        value={config.contentAnalysis.analysisDepth}
                        onChange={(e) => handleConfigChange('contentAnalysis', 'analysisDepth', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="surface">Surface - Basic content extraction</option>
                        <option value="moderate">Moderate - Structured analysis</option>
                        <option value="deep">Deep - Comprehensive understanding</option>
                      </select>
                    </div>

                    <div className="space-y-4">
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={config.contentAnalysis.enableSentiment}
                          onChange={(e) => handleConfigChange('contentAnalysis', 'enableSentiment', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Enable sentiment analysis
                        </span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={config.contentAnalysis.extractKeywords}
                          onChange={(e) => handleConfigChange('contentAnalysis', 'extractKeywords', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Extract keywords and key phrases
                        </span>
                      </label>

                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={config.contentAnalysis.generateSummaries}
                          onChange={(e) => handleConfigChange('contentAnalysis', 'generateSummaries', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                          Generate automatic summaries
                        </span>
                      </label>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Status Messages */}
            {hasChanges && (
              <div className="mt-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                  <span className="text-sm text-yellow-800 dark:text-yellow-200">
                    You have unsaved changes. Don't forget to save your configuration.
                  </span>
                </div>
              </div>
            )}

            {saving && (
              <div className="mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-center">
                  <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
                  <span className="text-sm text-blue-800 dark:text-blue-200">
                    Saving configuration changes...
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeacherAIConfig;
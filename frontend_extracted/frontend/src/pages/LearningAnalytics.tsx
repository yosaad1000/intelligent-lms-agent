import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { analyticsService, LearningMetrics, ConceptMastery, PersonalizedRecommendation, AnalyticsVisualizationData, LearningGoal } from '../services/analyticsService';
import { 
  ChartBarIcon,
  TrophyIcon,
  ClockIcon,
  BookOpenIcon,
  AcademicCapIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CalendarIcon,
  LightBulbIcon,
  PresentationChartLineIcon,
  DocumentArrowDownIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  FireIcon,
  EyeIcon,
  ChartPieIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface EnhancedAnalyticsData {
  metrics: LearningMetrics;
  conceptMastery: ConceptMastery;
  recommendations: PersonalizedRecommendation[];
  aiInsights: string;
  visualizationData: AnalyticsVisualizationData;
  goals: LearningGoal[];
  lastUpdated: string;
}

const LearningAnalytics: React.FC = () => {
  const { user, currentRole } = useAuth();
  const [analyticsData, setAnalyticsData] = useState<EnhancedAnalyticsData | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'year'>('week');
  const [selectedView, setSelectedView] = useState<'overview' | 'detailed' | 'goals' | 'recommendations'>('overview');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load analytics data with real Bedrock Agent integration
  const loadAnalyticsData = useCallback(async () => {
    if (!user?.id) return;

    try {
      setError(null);
      
      const timePeriodDays = selectedPeriod === 'week' ? 7 : selectedPeriod === 'month' ? 30 : 365;
      
      // Get comprehensive analytics from Bedrock Agent
      const analyticsResult = await analyticsService.getLearningAnalytics(user.id, timePeriodDays);
      
      // Get learning goals
      const goals = await analyticsService.getLearningGoals(user.id);
      
      if (analyticsResult.success) {
        setAnalyticsData({
          metrics: analyticsResult.metrics,
          conceptMastery: analyticsResult.conceptMastery,
          recommendations: analyticsResult.recommendations,
          aiInsights: analyticsResult.aiInsights,
          visualizationData: analyticsResult.visualizationData,
          goals,
          lastUpdated: new Date().toISOString()
        });
      } else {
        throw new Error('Failed to load analytics data');
      }
      
    } catch (error) {
      console.error('Error loading analytics:', error);
      setError('Failed to load analytics data. Please try again.');
      
      // Load fallback mock data
      const mockData = await analyticsService.getLearningAnalytics('demo_user', 30);
      const mockGoals = await analyticsService.getLearningGoals('demo_user');
      
      setAnalyticsData({
        metrics: mockData.metrics,
        conceptMastery: mockData.conceptMastery,
        recommendations: mockData.recommendations,
        aiInsights: mockData.aiInsights,
        visualizationData: mockData.visualizationData,
        goals: mockGoals,
        lastUpdated: new Date().toISOString()
      });
      
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id, selectedPeriod]);

  useEffect(() => {
    loadAnalyticsData();
  }, [loadAnalyticsData]);

  // Refresh analytics data
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalyticsData();
  };

  // Export analytics report
  const handleExportReport = async (format: 'pdf' | 'csv' | 'json' = 'pdf') => {
    if (!user?.id) return;
    
    try {
      const result = await analyticsService.exportAnalyticsReport(user.id, format);
      
      if (result.success && result.downloadUrl) {
        // Create download link
        const link = document.createElement('a');
        link.href = result.downloadUrl;
        link.download = `learning-analytics-${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        throw new Error(result.error || 'Export failed');
      }
      
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export report. Please try again.');
    }
  };

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const getMasteryColor = (level: number) => {
    if (level >= 0.8) return 'text-green-600 bg-green-100 dark:bg-green-900/20';
    if (level >= 0.6) return 'text-blue-600 bg-blue-100 dark:bg-blue-900/20';
    if (level >= 0.4) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
    return 'text-red-600 bg-red-100 dark:bg-red-900/20';
  };

  const getMasteryLabel = (level: number) => {
    if (level >= 0.8) return 'Expert';
    if (level >= 0.6) return 'Proficient';
    if (level >= 0.4) return 'Learning';
    return 'Beginner';
  };

  const getTrendIcon = (trend: 'improving' | 'stable' | 'declining') => {
    switch (trend) {
      case 'improving': return <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'declining': return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />;
      default: return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
    }
  };

  const getPriorityColor = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100 dark:bg-red-900/20';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
      case 'low': return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700';
    }
  };

  const formatPercentage = (value: number) => {
    return `${Math.round(value * 100)}%`;
  };

  const getEngagementLevel = (score: number) => {
    if (score >= 0.8) return { label: 'Excellent', color: 'text-green-600' };
    if (score >= 0.6) return { label: 'Good', color: 'text-blue-600' };
    if (score >= 0.4) return { label: 'Fair', color: 'text-yellow-600' };
    return { label: 'Needs Improvement', color: 'text-red-600' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-600 dark:text-gray-400">Loading comprehensive analytics...</p>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-500">Analyzing learning patterns with AI...</p>
        </div>
      </div>
    );
  }

  if (!analyticsData) return null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 safe-area-padding transition-colors">
      {/* Enhanced Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container-responsive">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-4 sm:py-6 space-y-3 sm:space-y-0">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                <ChartBarIcon className="h-6 w-6 sm:h-8 sm:w-8 mr-2 text-blue-500" />
                Learning Analytics Dashboard
              </h1>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mt-1">
                AI-powered insights into your learning journey • Last updated: {new Date(analyticsData.lastUpdated).toLocaleString()}
              </p>
              {error && (
                <div className="flex items-center mt-2 text-sm text-red-600 dark:text-red-400">
                  <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                  {error}
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              {/* View Selector */}
              <select
                value={selectedView}
                onChange={(e) => setSelectedView(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100 text-sm"
              >
                <option value="overview">Overview</option>
                <option value="detailed">Detailed Analysis</option>
                <option value="goals">Goals & Progress</option>
                <option value="recommendations">AI Recommendations</option>
              </select>
              
              {/* Time Period Selector */}
              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value as 'week' | 'month' | 'year')}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100 text-sm"
              >
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="year">This Year</option>
              </select>
              
              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 text-sm flex items-center"
              >
                <ArrowPathIcon className={`h-4 w-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </button>
              
              {/* Export Button */}
              <button
                onClick={() => handleExportReport('pdf')}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm flex items-center"
              >
                <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                Export
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container-responsive py-6 sm:py-8">
        {/* Enhanced Key Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <ClockIcon className="h-6 w-6 sm:h-8 sm:w-8 text-blue-500 flex-shrink-0" />
                <div className="ml-3 sm:ml-4">
                  <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {analyticsData.metrics.engagement.totalInteractions}
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Total Interactions</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {analyticsData.metrics.engagement.interactionFrequency.toFixed(1)}/day
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <TrophyIcon className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-500 flex-shrink-0" />
                <div className="ml-3 sm:ml-4">
                  <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {analyticsData.metrics.performance.averageQuizScore}%
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Quiz Average</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {analyticsData.metrics.performance.quizCount} quizzes
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AcademicCapIcon className="h-6 w-6 sm:h-8 sm:w-8 text-green-500 flex-shrink-0" />
                <div className="ml-3 sm:ml-4">
                  <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {formatPercentage(analyticsData.metrics.performance.averageMastery)}
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Avg Mastery</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                {analyticsData.metrics.progress.conceptsLearned} concepts
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <FireIcon className="h-6 w-6 sm:h-8 sm:w-8 text-purple-500 flex-shrink-0" />
                <div className="ml-3 sm:ml-4">
                  <div className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {formatPercentage(analyticsData.metrics.progress.learningVelocity)}
                  </div>
                  <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Learning Velocity</div>
                </div>
              </div>
              <div className="text-xs text-gray-500">
                +{analyticsData.metrics.progress.weeklyGrowth}% growth
              </div>
            </div>
          </div>
        </div>

        {/* Engagement & Sentiment Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6 sm:mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
              <EyeIcon className="h-5 w-5 mr-2" />
              Engagement Level
            </h3>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatPercentage(analyticsData.metrics.engagement.sentimentScore)}
                </div>
                <div className={`text-sm font-medium ${getEngagementLevel(analyticsData.metrics.engagement.sentimentScore).color}`}>
                  {getEngagementLevel(analyticsData.metrics.engagement.sentimentScore).label}
                </div>
              </div>
              <div className="w-16 h-16 relative">
                <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-gray-200 dark:text-gray-700"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeDasharray={`${analyticsData.metrics.engagement.sentimentScore * 100}, 100`}
                    className="text-blue-500"
                  />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
              <ChartPieIcon className="h-5 w-5 mr-2" />
              Mastery Distribution
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Advanced</span>
                <span className="text-sm font-medium text-green-600">{analyticsData.metrics.performance.masteryDistribution.advanced}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Intermediate</span>
                <span className="text-sm font-medium text-blue-600">{analyticsData.metrics.performance.masteryDistribution.intermediate}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Beginner</span>
                <span className="text-sm font-medium text-yellow-600">{analyticsData.metrics.performance.masteryDistribution.beginner}</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
              <BookOpenIcon className="h-5 w-5 mr-2" />
              Learning Progress
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Concepts Learned</span>
                <span className="text-sm font-medium text-green-600">{analyticsData.metrics.progress.conceptsLearned}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">In Progress</span>
                <span className="text-sm font-medium text-blue-600">{analyticsData.metrics.progress.conceptsInProgress}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">To Learn</span>
                <span className="text-sm font-medium text-yellow-600">{analyticsData.metrics.progress.conceptsToLearn}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Conditional View Rendering */}
        {selectedView === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Enhanced Study Time Chart */}
            <div className="lg:col-span-2">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  Study Time Analysis
                </h2>
                
                <div className="flex items-end space-x-2 h-48 mb-4">
                  {analyticsData.visualizationData.studyTimeChart.datasets[0].data.map((minutes, index) => {
                    const maxMinutes = Math.max(...analyticsData.visualizationData.studyTimeChart.datasets[0].data);
                    const height = (minutes / maxMinutes) * 100;
                    const labels = analyticsData.visualizationData.studyTimeChart.labels;
                    
                    return (
                      <div key={index} className="flex-1 flex flex-col items-center group">
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-t relative">
                          <div 
                            className="bg-gradient-to-t from-blue-500 to-blue-400 rounded-t transition-all duration-500 hover:from-blue-600 hover:to-blue-500"
                            style={{ height: `${height}%`, minHeight: '4px' }}
                          />
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                          {labels[index]}
                        </div>
                        <div className="text-xs font-medium text-gray-700 dark:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity">
                          {minutes}m
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Average Session</div>
                    <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {formatTime(analyticsData.metrics.engagement.averageSessionDuration)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Total This Period</div>
                    <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {formatTime(analyticsData.visualizationData.studyTimeChart.datasets[0].data.reduce((a, b) => a + b, 0))}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Daily Average</div>
                    <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {formatTime(Math.round(analyticsData.visualizationData.studyTimeChart.datasets[0].data.reduce((a, b) => a + b, 0) / analyticsData.visualizationData.studyTimeChart.datasets[0].data.length))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Concept Mastery Analysis */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                  <AcademicCapIcon className="h-5 w-5 mr-2" />
                  Concept Mastery Analysis
                </h2>
                
                <div className="space-y-4">
                  {Object.entries(analyticsData.conceptMastery).map(([concept, data], index) => (
                    <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <h3 className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                            {concept.replace(/_/g, ' ')}
                          </h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getMasteryColor(data.level)}`}>
                            {getMasteryLabel(data.level)}
                          </span>
                          {getTrendIcon(data.trend)}
                        </div>
                        <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                          {formatPercentage(data.level)}
                        </span>
                      </div>
                      
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-500 ${
                            data.level >= 0.8 ? 'bg-green-500' :
                            data.level >= 0.6 ? 'bg-blue-500' :
                            data.level >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${data.level * 100}%` }}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                        <span>{data.interactionCount} interactions</span>
                        <span>Difficulty: {data.difficulty}</span>
                        <span>Updated: {new Date(data.lastUpdated).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Enhanced Sidebar */}
            <div className="space-y-6">
              {/* Learning Goals */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                  <PresentationChartLineIcon className="h-5 w-5 mr-2" />
                  Learning Goals
                </h2>
                
                <div className="space-y-4">
                  {analyticsData.goals.map((goal) => {
                    const isCompleted = goal.isCompleted;
                    
                    return (
                      <div key={goal.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100">
                            {goal.title}
                          </h4>
                          <div className="flex items-center space-x-1">
                            {isCompleted && <CheckCircleIcon className="h-4 w-4 text-green-500" />}
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(goal.priority)}`}>
                              {goal.priority}
                            </span>
                          </div>
                        </div>
                        
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-500 ${
                              isCompleted ? 'bg-green-500' : 'bg-blue-500'
                            }`}
                            style={{ width: `${Math.min(goal.progress, 100)}%` }}
                          />
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-2">
                          <span>
                            {goal.currentValue} / {goal.targetValue} {goal.unit}
                          </span>
                          <span>{Math.round(goal.progress)}%</span>
                        </div>
                        
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Due: {new Date(goal.deadline).toLocaleDateString()}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* AI Insights */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                  <LightBulbIcon className="h-5 w-5 mr-2" />
                  AI Insights
                </h2>
                
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-4">
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {analyticsData.aiInsights}
                  </p>
                </div>
              </div>

              {/* Personalized Recommendations */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                  <LightBulbIcon className="h-5 w-5 mr-2" />
                  Personalized Recommendations
                </h2>
                
                <div className="space-y-3">
                  {analyticsData.recommendations.slice(0, 3).map((recommendation, index) => (
                    <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100">
                          {recommendation.title}
                        </h4>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(recommendation.priority)}`}>
                          {recommendation.priority}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                        {recommendation.description}
                      </p>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Impact: {Math.round(recommendation.estimatedImpact * 100)}%</span>
                        {recommendation.actionable && (
                          <span className="text-green-600 dark:text-green-400">Actionable</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                  <Cog6ToothIcon className="h-5 w-5 mr-2" />
                  Quick Actions
                </h2>
                
                <div className="space-y-2">
                  <button 
                    onClick={() => setSelectedView('goals')}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm flex items-center justify-center"
                  >
                    <PresentationChartLineIcon className="h-4 w-4 mr-2" />
                    Manage Goals
                  </button>
                  <button 
                    onClick={() => handleExportReport('pdf')}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm flex items-center justify-center"
                  >
                    <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                    Export Report
                  </button>
                  <button 
                    onClick={() => setSelectedView('recommendations')}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm flex items-center justify-center"
                  >
                    <LightBulbIcon className="h-4 w-4 mr-2" />
                    View All Recommendations
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Analysis View */}
        {selectedView === 'detailed' && (
          <div className="space-y-6">
            {/* Performance Trends Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                <ArrowTrendingUpIcon className="h-5 w-5 mr-2" />
                Performance Trends
              </h2>
              
              <div className="h-64 flex items-end space-x-2">
                {analyticsData.visualizationData.progressTrendChart.datasets[0].data.map((value, index) => {
                  const maxValue = Math.max(...analyticsData.visualizationData.progressTrendChart.datasets[0].data);
                  const height = (value / maxValue) * 100;
                  
                  return (
                    <div key={index} className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-t relative">
                        <div 
                          className="bg-gradient-to-t from-purple-500 to-purple-400 rounded-t transition-all duration-500"
                          style={{ height: `${height}%`, minHeight: '4px' }}
                        />
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        {analyticsData.visualizationData.progressTrendChart.labels[index]}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Detailed Concept Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Concept Mastery Breakdown
                </h3>
                <div className="space-y-4">
                  {Object.entries(analyticsData.conceptMastery).map(([concept, data]) => (
                    <div key={concept} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                        {concept.replace(/_/g, ' ')}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${data.level * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100 w-12">
                          {Math.round(data.level * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Learning Velocity Analysis
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Current Velocity</span>
                    <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {formatPercentage(analyticsData.metrics.progress.learningVelocity)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Weekly Growth</span>
                    <span className="text-lg font-semibold text-green-600">
                      +{analyticsData.metrics.progress.weeklyGrowth}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Engagement Score</span>
                    <span className="text-lg font-semibold text-blue-600">
                      {formatPercentage(analyticsData.metrics.engagement.sentimentScore)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Goals Management View */}
        {selectedView === 'goals' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center">
                <PresentationChartLineIcon className="h-5 w-5 mr-2" />
                Learning Goals Management
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {analyticsData.goals.map((goal) => (
                  <div key={goal.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                        {goal.title}
                      </h3>
                      {goal.isCompleted && <CheckCircleIcon className="h-5 w-5 text-green-500" />}
                    </div>
                    
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {goal.description}
                    </p>
                    
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Progress</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {Math.round(goal.progress)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-500 ${
                            goal.isCompleted ? 'bg-green-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${Math.min(goal.progress, 100)}%` }}
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2 text-xs text-gray-500 dark:text-gray-400">
                      <div className="flex justify-between">
                        <span>Current:</span>
                        <span>{goal.currentValue} {goal.unit}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Target:</span>
                        <span>{goal.targetValue} {goal.unit}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Deadline:</span>
                        <span>{new Date(goal.deadline).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    {goal.milestones && goal.milestones.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Milestones</h4>
                        <div className="space-y-1">
                          {goal.milestones.map((milestone, index) => (
                            <div key={index} className="flex items-center space-x-2 text-xs">
                              <div className={`w-2 h-2 rounded-full ${milestone.achieved ? 'bg-green-500' : 'bg-gray-300'}`} />
                              <span className={milestone.achieved ? 'text-green-600' : 'text-gray-500'}>
                                {milestone.description}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Recommendations View */}
        {selectedView === 'recommendations' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center">
                <LightBulbIcon className="h-5 w-5 mr-2" />
                AI-Powered Learning Recommendations
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {analyticsData.recommendations.map((recommendation, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                        {recommendation.title}
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(recommendation.priority)}`}>
                        {recommendation.priority}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {recommendation.description}
                    </p>
                    
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Estimated Impact</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full"
                            style={{ width: `${recommendation.estimatedImpact * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {Math.round(recommendation.estimatedImpact * 100)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                      <span>Type: {recommendation.type.replace(/_/g, ' ')}</span>
                      {recommendation.actionable && (
                        <span className="text-green-600 dark:text-green-400 font-medium">Actionable</span>
                      )}
                    </div>
                    
                    {recommendation.relatedConcepts && recommendation.relatedConcepts.length > 0 && (
                      <div className="mt-3">
                        <div className="flex flex-wrap gap-1">
                          {recommendation.relatedConcepts.map((concept, conceptIndex) => (
                            <span key={conceptIndex} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-xs rounded">
                              {concept}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningAnalytics;
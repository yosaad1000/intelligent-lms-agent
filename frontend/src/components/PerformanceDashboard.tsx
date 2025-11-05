import React, { useState, useEffect } from 'react';
import { performanceMonitor } from '../services/performanceMonitor';
import type { PerformanceMetrics, ConnectionPoolStats, CacheStats } from '../services/performanceMonitor';
import {
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ServerIcon,
  CpuChipIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface PerformanceDashboardProps {
  className?: string;
  refreshInterval?: number;
}

const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  className = '',
  refreshInterval = 5000 // 5 seconds
}) => {
  const [performanceData, setPerformanceData] = useState<{
    stats: ReturnType<typeof performanceMonitor.getPerformanceStats>;
    connectionPool: ConnectionPoolStats;
    cache: CacheStats;
    recommendations: string[];
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const refreshData = () => {
    try {
      const data = performanceMonitor.exportMetrics();
      setPerformanceData({
        stats: data.stats,
        connectionPool: data.connectionPool,
        cache: data.cache,
        recommendations: data.recommendations
      });
      setLastUpdated(new Date());
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to refresh performance data:', error);
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    
    const interval = setInterval(refreshData, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const getStatusColor = (value: number, thresholds: { good: number; warning: number }): string => {
    if (value <= thresholds.good) return 'text-green-600';
    if (value <= thresholds.warning) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <ArrowPathIcon className="h-6 w-6 animate-spin text-blue-500 mr-2" />
          <span className="text-gray-600 dark:text-gray-400">Loading performance data...</span>
        </div>
      </div>
    );
  }

  if (!performanceData) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
        <div className="text-center text-gray-500 dark:text-gray-400">
          No performance data available
        </div>
      </div>
    );
  }

  const { stats, connectionPool, cache, recommendations } = performanceData;

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="h-6 w-6 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Performance Dashboard
            </h3>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <ClockIcon className="h-4 w-4" />
            <span>Updated: {lastUpdated.toLocaleTimeString()}</span>
            <button
              onClick={refreshData}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              title="Refresh data"
            >
              <ArrowPathIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg Response Time</p>
                <p className={`text-2xl font-bold ${getStatusColor(stats.averageResponseTime, { good: 1000, warning: 3000 })}`}>
                  {formatTime(stats.averageResponseTime)}
                </p>
              </div>
              <ClockIcon className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
                <p className={`text-2xl font-bold ${getStatusColor(1 - stats.successRate, { good: 0.05, warning: 0.1 })}`}>
                  {formatPercentage(stats.successRate)}
                </p>
              </div>
              <CheckCircleIcon className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Requests</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {stats.totalRequests}
                </p>
              </div>
              <ServerIcon className="h-8 w-8 text-purple-500" />
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Cache Hit Rate</p>
                <p className={`text-2xl font-bold ${getStatusColor(1 - cache.hitRate, { good: 0.3, warning: 0.7 })}`}>
                  {formatPercentage(cache.hitRate)}
                </p>
              </div>
              <CpuChipIcon className="h-8 w-8 text-indigo-500" />
            </div>
          </div>
        </div>

        {/* Operation Breakdown */}
        {Object.keys(stats.operationStats).length > 0 && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Operation Performance
            </h4>
            <div className="space-y-2">
              {Object.entries(stats.operationStats).map(([operation, opStats]) => (
                <div key={operation} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {operation}
                      </span>
                      <div className="flex items-center space-x-4 text-sm">
                        <span className="text-gray-600 dark:text-gray-400">
                          {opStats.count} calls
                        </span>
                        <span className={getStatusColor(opStats.averageTime, { good: 1000, warning: 3000 })}>
                          {formatTime(opStats.averageTime)}
                        </span>
                        <span className={getStatusColor(1 - opStats.successRate, { good: 0.05, warning: 0.1 })}>
                          {formatPercentage(opStats.successRate)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Connection Pool Stats */}
        <div>
          <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Connection Pool
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">Active Connections</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {connectionPool.activeConnections}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">Avg Response Time</p>
              <p className={`text-lg font-bold ${getStatusColor(connectionPool.averageResponseTime, { good: 1000, warning: 3000 })}`}>
                {formatTime(connectionPool.averageResponseTime)}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">Error Rate</p>
              <p className={`text-lg font-bold ${getStatusColor(connectionPool.errorRate, { good: 0.05, warning: 0.1 })}`}>
                {formatPercentage(connectionPool.errorRate)}
              </p>
            </div>
          </div>
        </div>

        {/* Cache Stats */}
        <div>
          <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Cache Performance
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">Hit Rate</p>
              <p className={`text-lg font-bold ${getStatusColor(1 - cache.hitRate, { good: 0.3, warning: 0.7 })}`}>
                {formatPercentage(cache.hitRate)}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">Cache Size</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {cache.cacheSize}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Requests</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {cache.totalRequests}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">Evictions</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {cache.evictions}
              </p>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Performance Recommendations
            </h4>
            <div className="space-y-2">
              {recommendations.map((recommendation, index) => (
                <div
                  key={index}
                  className={`flex items-start space-x-2 p-3 rounded-lg ${
                    recommendation.includes('good') || recommendation.includes('No immediate')
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200'
                      : 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200'
                  }`}
                >
                  {recommendation.includes('good') || recommendation.includes('No immediate') ? (
                    <CheckCircleIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  ) : (
                    <ExclamationTriangleIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  )}
                  <span className="text-sm">{recommendation}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceDashboard;
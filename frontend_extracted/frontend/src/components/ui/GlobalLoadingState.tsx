import React from 'react';
import { SparklesIcon } from '@heroicons/react/24/outline';

interface GlobalLoadingStateProps {
  message?: string;
  submessage?: string;
  progress?: number;
  showProgress?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'minimal' | 'detailed';
}

const GlobalLoadingState: React.FC<GlobalLoadingStateProps> = ({
  message = 'Loading...',
  submessage,
  progress,
  showProgress = false,
  size = 'md',
  variant = 'default'
}) => {
  const sizeClasses = {
    sm: {
      container: 'p-4',
      spinner: 'h-6 w-6',
      text: 'text-sm',
      subtext: 'text-xs'
    },
    md: {
      container: 'p-6',
      spinner: 'h-8 w-8',
      text: 'text-base',
      subtext: 'text-sm'
    },
    lg: {
      container: 'p-8',
      spinner: 'h-12 w-12',
      text: 'text-lg',
      subtext: 'text-base'
    }
  };

  const classes = sizeClasses[size];

  if (variant === 'minimal') {
    return (
      <div className="flex items-center justify-center space-x-2">
        <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${classes.spinner}`}></div>
        <span className={`text-gray-600 dark:text-gray-400 ${classes.text}`}>{message}</span>
      </div>
    );
  }

  if (variant === 'detailed') {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center safe-area-padding">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          <div className="text-center">
            {/* Animated Logo/Icon */}
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 mb-6">
              <SparklesIcon className="h-8 w-8 text-white animate-pulse" />
            </div>

            {/* Main Loading Spinner */}
            <div className="relative mb-6">
              <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-gray-200 dark:border-gray-700 border-t-blue-600"></div>
              {showProgress && progress !== undefined && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                    {Math.round(progress)}%
                  </span>
                </div>
              )}
            </div>

            {/* Loading Message */}
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {message}
            </h2>

            {submessage && (
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {submessage}
              </p>
            )}

            {/* Progress Bar */}
            {showProgress && progress !== undefined && (
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-4">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
                ></div>
              </div>
            )}

            {/* Loading Steps/Dots */}
            <div className="flex justify-center space-x-2">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className={`h-2 w-2 rounded-full animate-pulse ${
                    i === 0 ? 'bg-blue-500' : i === 1 ? 'bg-purple-500' : 'bg-pink-500'
                  }`}
                  style={{
                    animationDelay: `${i * 0.2}s`,
                    animationDuration: '1s'
                  }}
                ></div>
              ))}
            </div>

            {/* Tips or Additional Info */}
            <div className="mt-6 text-xs text-gray-500 dark:text-gray-400">
              <p>This may take a few moments...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div className={`flex flex-col items-center justify-center text-center ${classes.container}`}>
      {/* Main Spinner */}
      <div className={`animate-spin rounded-full border-2 border-gray-300 dark:border-gray-600 border-t-blue-600 dark:border-t-blue-400 ${classes.spinner} mb-4`}></div>
      
      {/* Loading Text */}
      <div className="space-y-2">
        <p className={`font-medium text-gray-900 dark:text-gray-100 ${classes.text}`}>
          {message}
        </p>
        
        {submessage && (
          <p className={`text-gray-600 dark:text-gray-400 ${classes.subtext}`}>
            {submessage}
          </p>
        )}
      </div>

      {/* Progress Bar */}
      {showProgress && progress !== undefined && (
        <div className="w-full max-w-xs mt-4">
          <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

// Skeleton Loading Components
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
    <div className="flex items-center space-x-4 mb-4">
      <div className="h-10 w-10 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
      <div className="space-y-2 flex-1">
        <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
        <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
      </div>
    </div>
    <div className="space-y-3">
      <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded"></div>
      <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-5/6"></div>
      <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-4/6"></div>
    </div>
  </div>
);

export const SkeletonTable: React.FC<{ rows?: number; columns?: number }> = ({ 
  rows = 5, 
  columns = 4 
}) => (
  <div className="animate-pulse bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
    {/* Header */}
    <div className="bg-gray-50 dark:bg-gray-700 px-6 py-3 border-b border-gray-200 dark:border-gray-600">
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-300 dark:bg-gray-600 rounded"></div>
        ))}
      </div>
    </div>
    
    {/* Rows */}
    <div className="divide-y divide-gray-200 dark:divide-gray-600">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="px-6 py-4">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div key={colIndex} className="h-4 bg-gray-300 dark:bg-gray-600 rounded"></div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const SkeletonList: React.FC<{ items?: number }> = ({ items = 3 }) => (
  <div className="space-y-4">
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="animate-pulse flex items-center space-x-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="h-12 w-12 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
          <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
        </div>
        <div className="h-8 w-20 bg-gray-300 dark:bg-gray-600 rounded"></div>
      </div>
    ))}
  </div>
);

export default GlobalLoadingState;
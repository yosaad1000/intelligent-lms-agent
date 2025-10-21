import React from 'react';
import { AgentError, errorHandlingService } from '../services/errorHandlingService';
import { 
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface ErrorDisplayProps {
  error: AgentError;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  compact?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  className = '',
  compact = false
}) => {
  const errorInfo = errorHandlingService.getErrorDisplayInfo(error);

  const getIcon = () => {
    switch (errorInfo.severity) {
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
    }
  };

  const getBorderColor = () => {
    switch (errorInfo.severity) {
      case 'error':
        return 'border-red-200 dark:border-red-700';
      case 'warning':
        return 'border-yellow-200 dark:border-yellow-700';
      case 'info':
        return 'border-blue-200 dark:border-blue-700';
      default:
        return 'border-red-200 dark:border-red-700';
    }
  };

  const getBackgroundColor = () => {
    switch (errorInfo.severity) {
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'bg-red-50 dark:bg-red-900/20';
    }
  };

  const getTextColor = () => {
    switch (errorInfo.severity) {
      case 'error':
        return 'text-red-900 dark:text-red-100';
      case 'warning':
        return 'text-yellow-900 dark:text-yellow-100';
      case 'info':
        return 'text-blue-900 dark:text-blue-100';
      default:
        return 'text-red-900 dark:text-red-100';
    }
  };

  if (compact) {
    return (
      <div className={`${getBackgroundColor()} border ${getBorderColor()} rounded-md p-3 ${className}`}>
        <div className="flex items-center space-x-2">
          {getIcon()}
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium ${getTextColor()}`}>
              {errorInfo.title}
            </p>
            <p className={`text-xs ${getTextColor()} opacity-80 truncate`}>
              {errorInfo.message}
            </p>
          </div>
          <div className="flex items-center space-x-1">
            {errorInfo.canRetry && onRetry && (
              <button
                onClick={onRetry}
                className="text-xs bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Retry
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XCircleIcon className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${getBackgroundColor()} border ${getBorderColor()} rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-3">
        {getIcon()}
        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-medium ${getTextColor()}`}>
            {errorInfo.title}
          </h3>
          <p className={`mt-1 text-sm ${getTextColor()} opacity-90`}>
            {errorInfo.message}
          </p>
          
          {/* Error Details */}
          {error.details.context && (
            <div className="mt-3">
              <details className="group">
                <summary className={`cursor-pointer text-xs ${getTextColor()} opacity-70 hover:opacity-100`}>
                  Show technical details
                </summary>
                <div className="mt-2 p-2 bg-white dark:bg-gray-800 rounded border text-xs font-mono text-gray-600 dark:text-gray-400">
                  <div><strong>Code:</strong> {error.details.code}</div>
                  <div><strong>Category:</strong> {error.details.category}</div>
                  <div><strong>Timestamp:</strong> {error.details.timestamp.toLocaleString()}</div>
                  {error.details.context && (
                    <div className="mt-2">
                      <strong>Context:</strong>
                      <pre className="mt-1 whitespace-pre-wrap">
                        {JSON.stringify(error.details.context, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            </div>
          )}
          
          {/* Suggestions */}
          {errorInfo.suggestions.length > 0 && (
            <div className="mt-3">
              <h4 className={`text-xs font-medium ${getTextColor()} mb-2`}>
                Suggestions:
              </h4>
              <ul className={`text-xs ${getTextColor()} opacity-80 space-y-1`}>
                {errorInfo.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start space-x-1">
                    <span className="text-gray-400">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        {/* Actions */}
        <div className="flex items-center space-x-2">
          {errorInfo.canRetry && onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center space-x-1 text-xs bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <ArrowPathIcon className="h-3 w-3" />
              <span>Retry</span>
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XCircleIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Error Toast Component for temporary notifications
interface ErrorToastProps {
  error: AgentError;
  onDismiss: () => void;
  duration?: number;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({
  error,
  onDismiss,
  duration = 5000
}) => {
  React.useEffect(() => {
    const timer = setTimeout(onDismiss, duration);
    return () => clearTimeout(timer);
  }, [onDismiss, duration]);

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm">
      <ErrorDisplay
        error={error}
        onDismiss={onDismiss}
        compact={true}
        className="shadow-lg"
      />
    </div>
  );
};

// Error List Component for displaying multiple errors
interface ErrorListProps {
  errors: AgentError[];
  onRetry?: (error: AgentError) => void;
  onDismiss?: (error: AgentError) => void;
  onClearAll?: () => void;
  className?: string;
}

export const ErrorList: React.FC<ErrorListProps> = ({
  errors,
  onRetry,
  onDismiss,
  onClearAll,
  className = ''
}) => {
  if (errors.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
          Recent Errors ({errors.length})
        </h3>
        {onClearAll && (
          <button
            onClick={onClearAll}
            className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            Clear All
          </button>
        )}
      </div>
      
      {errors.map((error, index) => (
        <ErrorDisplay
          key={`${error.details.code}-${error.details.timestamp.getTime()}-${index}`}
          error={error}
          onRetry={onRetry ? () => onRetry(error) : undefined}
          onDismiss={onDismiss ? () => onDismiss(error) : undefined}
          compact={true}
        />
      ))}
    </div>
  );
};

export default ErrorDisplay;
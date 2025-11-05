import React from 'react';
import { useHybridMode } from '../hooks/useHybridMode';

interface HybridModeIndicatorProps {
  showDetails?: boolean;
  className?: string;
}

const HybridModeIndicator: React.FC<HybridModeIndicatorProps> = ({ 
  showDetails = false, 
  className = '' 
}) => {
  const { statusIndicators, isLoading } = useHybridMode();

  if (isLoading) {
    return (
      <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600 ${className}`}>
        <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse"></div>
        <span>Loading...</span>
      </div>
    );
  }

  const getColorClasses = (color: string) => {
    switch (color) {
      case 'blue':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'green':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'red':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'yellow':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  const getDotColor = (color: string) => {
    switch (color) {
      case 'blue': return 'bg-blue-500';
      case 'green': return 'bg-green-500';
      case 'red': return 'bg-red-500';
      case 'yellow': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  if (showDetails) {
    return (
      <div className={`space-y-2 ${className}`}>
        {statusIndicators.indicators.map((indicator, index) => (
          <div
            key={index}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm ${getColorClasses(indicator.color)}`}
            title={indicator.description}
          >
            <div className={`w-2 h-2 rounded-full ${getDotColor(indicator.color)}`}></div>
            <span className="font-medium">{indicator.label}</span>
            <span className="text-xs opacity-75">({indicator.description})</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {statusIndicators.indicators.map((indicator, index) => (
        <div
          key={index}
          className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getColorClasses(indicator.color)}`}
          title={indicator.description}
        >
          <div className={`w-2 h-2 rounded-full ${getDotColor(indicator.color)}`}></div>
          <span>{indicator.label}</span>
        </div>
      ))}
    </div>
  );
};

export default HybridModeIndicator;
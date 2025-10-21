import React, { useState, useEffect } from 'react';
import { configurationService, type ConfigurationStatus } from '../services/configurationService';
import './TestingModeIndicator.css';

interface CompactStatusIndicatorProps {
  className?: string;
  showRefresh?: boolean;
}

const CompactStatusIndicator: React.FC<CompactStatusIndicatorProps> = ({ 
  className = '', 
  showRefresh = true 
}) => {
  const [configStatus, setConfigStatus] = useState<ConfigurationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    checkConfiguration();
  }, []);

  const checkConfiguration = async () => {
    setIsLoading(true);
    try {
      const status = await configurationService.validateConfiguration();
      setConfigStatus(status);
    } catch (error) {
      console.error('Failed to check configuration:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshConfiguration = async () => {
    setIsLoading(true);
    try {
      const status = await configurationService.validateConfiguration(true);
      setConfigStatus(status);
    } catch (error) {
      console.error('Failed to refresh configuration:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: ConfigurationStatus | null) => {
    if (!status) return 'gray';
    if (status.valid) return status.warnings.length > 0 ? 'yellow' : 'green';
    return 'red';
  };

  const getStatusIcon = (status: ConfigurationStatus | null) => {
    if (isLoading) return '⏳';
    if (!status) return '❓';
    if (status.valid) return status.warnings.length > 0 ? '⚠️' : '✅';
    return '❌';
  };

  const getStatusText = (status: ConfigurationStatus | null) => {
    if (isLoading) return 'Checking...';
    if (!status) return 'Unknown';
    
    if (status.valid) {
      return status.warnings.length > 0 ? 'Ready (with warnings)' : 'Ready';
    }
    return 'Configuration Error';
  };

  const isHybridMode = configurationService.isHybridTestingMode();

  return (
    <div className={`compact-status-indicator ${className}`}>
      <div className={`compact-status-bar ${getStatusColor(configStatus)}`}>
        <span className="status-icon">{getStatusIcon(configStatus)}</span>
        <div className="compact-status-info">
          <span className="compact-status-mode">
            {isHybridMode ? 'Hybrid Mode' : 'Standard Mode'}
          </span>
          <span className="compact-status-text">
            {getStatusText(configStatus)}
          </span>
        </div>
        {showRefresh && (
          <button 
            onClick={refreshConfiguration}
            disabled={isLoading}
            className="compact-refresh-btn"
            title="Refresh status"
          >
            🔄
          </button>
        )}
      </div>
      
      {isHybridMode && (
        <div className="compact-hybrid-badge">
          Mock Auth + Real AI
        </div>
      )}
    </div>
  );
};

export default CompactStatusIndicator;
import React, { useState, useEffect } from 'react';
import { configurationService, type ConfigurationStatus } from '../services/configurationService';
import { errorHandlingService } from '../services/errorHandlingService';

interface TestingModeIndicatorProps {
  className?: string;
  showDetails?: boolean;
}

const TestingModeIndicator: React.FC<TestingModeIndicatorProps> = ({ 
  className = '', 
  showDetails = false 
}) => {
  const [configStatus, setConfigStatus] = useState<ConfigurationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

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
    
    const summary = configurationService.getStatusSummary(status);
    return summary.message;
  };

  const isHybridMode = configurationService.isHybridTestingMode();

  return (
    <div className={`testing-mode-indicator ${className}`}>
      {/* Main Status Bar */}
      <div className={`status-bar ${getStatusColor(configStatus)}`}>
        <div className="status-content">
          <span className="status-icon">{getStatusIcon(configStatus)}</span>
          <div className="status-info">
            <div className="status-title">
              {isHybridMode ? 'Hybrid Testing Mode' : 'Standard Mode'}
            </div>
            <div className="status-message">
              {getStatusText(configStatus)}
            </div>
          </div>
          <div className="status-actions">
            <button 
              onClick={refreshConfiguration}
              disabled={isLoading}
              className="refresh-btn"
              title="Refresh configuration status"
            >
              🔄
            </button>
            {showDetails && (
              <button 
                onClick={() => setShowDiagnostics(!showDiagnostics)}
                className="details-btn"
                title="Show diagnostic information"
              >
                🔍
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Hybrid Mode Warning */}
      {isHybridMode && (
        <div className="hybrid-warning">
          <span className="warning-icon">⚠️</span>
          <span className="warning-text">
            Using mock authentication with real AWS services
          </span>
        </div>
      )}

      {/* Configuration Details */}
      {showDetails && configStatus && (
        <div className="config-details">
          <div className="detail-section">
            <h4>Configuration Status</h4>
            <div className="detail-grid">
              <div className={`detail-item ${configStatus.details.awsCredentials}`}>
                <span className="detail-label">AWS Credentials:</span>
                <span className="detail-value">{configStatus.details.awsCredentials}</span>
              </div>
              <div className={`detail-item ${configStatus.details.agentConfiguration}`}>
                <span className="detail-label">Agent Config:</span>
                <span className="detail-value">{configStatus.details.agentConfiguration}</span>
              </div>
              <div className={`detail-item ${configStatus.details.agentConnectivity}`}>
                <span className="detail-label">Agent Connection:</span>
                <span className="detail-value">{configStatus.details.agentConnectivity}</span>
              </div>
            </div>
          </div>

          <div className="detail-section">
            <h4>Environment</h4>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Region:</span>
                <span className="detail-value">{configStatus.details.region}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Agent ID:</span>
                <span className="detail-value">{configStatus.details.agentId}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Alias ID:</span>
                <span className="detail-value">{configStatus.details.agentAliasId}</span>
              </div>
            </div>
          </div>

          {/* Errors */}
          {configStatus.errors.length > 0 && (
            <div className="detail-section errors">
              <h4>Errors</h4>
              <ul className="error-list">
                {configStatus.errors.map((error, index) => (
                  <li key={index} className="error-item">
                    <span className="error-icon">❌</span>
                    <span className="error-text">{error}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {configStatus.warnings.length > 0 && (
            <div className="detail-section warnings">
              <h4>Warnings</h4>
              <ul className="warning-list">
                {configStatus.warnings.map((warning, index) => (
                  <li key={index} className="warning-item">
                    <span className="warning-icon">⚠️</span>
                    <span className="warning-text">{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Setup Instructions */}
          {!configStatus.valid && (
            <div className="detail-section setup-instructions">
              <h4>Setup Instructions</h4>
              <ol className="instruction-list">
                {configurationService.getSetupInstructions(configStatus).map((instruction, index) => (
                  <li key={index} className="instruction-item">
                    {instruction}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {/* Diagnostic Information */}
      {showDiagnostics && (
        <DiagnosticPanel onClose={() => setShowDiagnostics(false)} />
      )}
    </div>
  );
};

// Diagnostic Panel Component
interface DiagnosticPanelProps {
  onClose: () => void;
}

const DiagnosticPanel: React.FC<DiagnosticPanelProps> = ({ onClose }) => {
  const [diagnosticInfo, setDiagnosticInfo] = useState<any>(null);
  const [errorStats, setErrorStats] = useState<any>(null);
  const [recentErrors, setRecentErrors] = useState<any[]>([]);

  useEffect(() => {
    // Get diagnostic information
    const info = configurationService.getDiagnosticInfo();
    setDiagnosticInfo(info);

    // Get error statistics
    const stats = errorHandlingService.getErrorStatistics();
    setErrorStats(stats);

    // Get recent errors
    const errors = errorHandlingService.getRecentErrors(5);
    setRecentErrors(errors);
  }, []);

  const copyToClipboard = () => {
    const diagnosticData = {
      diagnostic: diagnosticInfo,
      errorStats,
      recentErrors: recentErrors.map(error => ({
        ...error,
        timestamp: error.timestamp.toISOString()
      }))
    };

    navigator.clipboard.writeText(JSON.stringify(diagnosticData, null, 2));
    alert('Diagnostic information copied to clipboard');
  };

  return (
    <div className="diagnostic-panel">
      <div className="diagnostic-header">
        <h3>Diagnostic Information</h3>
        <div className="diagnostic-actions">
          <button onClick={copyToClipboard} className="copy-btn">
            📋 Copy
          </button>
          <button onClick={onClose} className="close-btn">
            ✕
          </button>
        </div>
      </div>

      <div className="diagnostic-content">
        {/* System Information */}
        <div className="diagnostic-section">
          <h4>System Information</h4>
          <pre className="diagnostic-data">
            {JSON.stringify(diagnosticInfo, null, 2)}
          </pre>
        </div>

        {/* Error Statistics */}
        <div className="diagnostic-section">
          <h4>Error Statistics</h4>
          <div className="error-stats">
            <div className="stat-item">
              <span className="stat-label">Total Errors:</span>
              <span className="stat-value">{errorStats?.total || 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Retryable Errors:</span>
              <span className="stat-value">{errorStats?.retryableCount || 0}</span>
            </div>
          </div>
          
          {errorStats?.byCategory && Object.keys(errorStats.byCategory).length > 0 && (
            <div className="category-stats">
              <h5>By Category:</h5>
              {Object.entries(errorStats.byCategory).map(([category, count]) => (
                <div key={category} className="category-item">
                  <span className="category-label">{category}:</span>
                  <span className="category-count">{count as number}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Errors */}
        {recentErrors.length > 0 && (
          <div className="diagnostic-section">
            <h4>Recent Errors</h4>
            <div className="recent-errors">
              {recentErrors.map((error, index) => (
                <div key={index} className="recent-error">
                  <div className="error-header">
                    <span className="error-code">{error.code}</span>
                    <span className="error-category">{error.category}</span>
                    <span className="error-time">
                      {error.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="error-message">{error.message}</div>
                  {error.context && (
                    <div className="error-context">
                      <pre>{JSON.stringify(error.context, null, 2)}</pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestingModeIndicator;
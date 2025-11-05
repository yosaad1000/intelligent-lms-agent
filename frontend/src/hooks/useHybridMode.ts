import { useState, useEffect, useCallback } from 'react';
import { hybridModeService, HybridModeConfig } from '../services/hybridModeService';

/**
 * Hook for managing hybrid mode state and configuration
 * Provides unified interface for components to detect and respond to hybrid mode changes
 */

export interface UseHybridModeReturn {
  // Configuration state
  config: HybridModeConfig | null;
  isLoading: boolean;
  error: string | null;
  
  // Mode detection
  isHybridMode: boolean;
  isAgentConnected: boolean;
  isConfigurationValid: boolean;
  
  // Service selection
  serviceSelection: {
    authService: 'mock' | 'real';
    agentService: 'mock' | 'direct' | 'api';
    dataService: 'mock' | 'real';
  };
  
  // Status indicators for UI
  statusIndicators: {
    mode: 'hybrid' | 'mock' | 'production';
    authStatus: 'mock' | 'real';
    agentStatus: 'connected' | 'disconnected';
    agentType: 'mock' | 'direct' | 'api';
    configurationStatus: 'valid' | 'invalid';
    indicators: Array<{
      type: 'hybrid' | 'agent' | 'auth';
      label: string;
      color: 'blue' | 'green' | 'red' | 'yellow';
      description: string;
    }>;
  };
  
  // Actions
  refreshConfiguration: () => Promise<void>;
  testConnectivity: () => Promise<{
    success: boolean;
    message: string;
    details?: any;
  }>;
  getSetupInstructions: () => string[];
  getDiagnosticInfo: () => Record<string, any>;
}

export const useHybridMode = (): UseHybridModeReturn => {
  const [config, setConfig] = useState<HybridModeConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize hybrid mode service
  useEffect(() => {
    let mounted = true;

    const initializeHybridMode = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const initialConfig = await hybridModeService.initialize();
        
        if (mounted) {
          setConfig(initialConfig);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to initialize hybrid mode');
          console.error('Failed to initialize hybrid mode:', err);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    initializeHybridMode();

    // Subscribe to configuration changes
    const unsubscribe = hybridModeService.onConfigurationChange((newConfig) => {
      if (mounted) {
        setConfig(newConfig);
      }
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, []);

  // Refresh configuration
  const refreshConfiguration = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const newConfig = await hybridModeService.refreshConfiguration();
      setConfig(newConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh configuration');
      console.error('Failed to refresh configuration:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Test connectivity
  const testConnectivity = useCallback(async () => {
    try {
      return await hybridModeService.testAgentConnectivity();
    } catch (err) {
      return {
        success: false,
        message: err instanceof Error ? err.message : 'Connectivity test failed',
        details: { error: err }
      };
    }
  }, []);

  // Get setup instructions
  const getSetupInstructions = useCallback(() => {
    try {
      return hybridModeService.getSetupInstructions();
    } catch (err) {
      return ['Error getting setup instructions. Please check configuration.'];
    }
  }, [config]);

  // Get diagnostic info
  const getDiagnosticInfo = useCallback(() => {
    try {
      return hybridModeService.getDiagnosticInfo();
    } catch (err) {
      return {
        error: err instanceof Error ? err.message : 'Failed to get diagnostic info',
        timestamp: new Date().toISOString()
      };
    }
  }, [config]);

  // Derived state
  const isHybridMode = config?.isHybridMode ?? false;
  const isAgentConnected = config?.agentConnected ?? false;
  const isConfigurationValid = config?.configurationValid ?? false;

  // Service selection
  const serviceSelection = config ? hybridModeService.getServiceSelection() : {
    authService: 'mock' as const,
    agentService: 'mock' as const,
    dataService: 'mock' as const
  };

  // Status indicators
  const statusIndicators = config ? hybridModeService.getStatusIndicators() : {
    mode: 'mock' as const,
    authStatus: 'mock' as const,
    agentStatus: 'disconnected' as const,
    agentType: 'mock' as const,
    configurationStatus: 'invalid' as const,
    indicators: []
  };

  return {
    // Configuration state
    config,
    isLoading,
    error,
    
    // Mode detection
    isHybridMode,
    isAgentConnected,
    isConfigurationValid,
    
    // Service selection
    serviceSelection,
    
    // Status indicators
    statusIndicators,
    
    // Actions
    refreshConfiguration,
    testConnectivity,
    getSetupInstructions,
    getDiagnosticInfo
  };
};

/**
 * Hook for getting the appropriate auth context based on hybrid mode
 */
export const useAuthContext = () => {
  const { serviceSelection } = useHybridMode();
  
  // This would be used in components to get the right auth context
  // The actual implementation would import and use the appropriate context
  return {
    shouldUseMockAuth: serviceSelection.authService === 'mock',
    authServiceType: serviceSelection.authService
  };
};

/**
 * Hook for getting the appropriate agent service based on hybrid mode
 */
export const useAgentService = () => {
  const { serviceSelection, isAgentConnected } = useHybridMode();
  
  return {
    agentService: hybridModeService.getAgentService(),
    agentServiceType: serviceSelection.agentService,
    isConnected: isAgentConnected
  };
};

/**
 * Hook for getting the appropriate data service based on hybrid mode
 */
export const useDataService = () => {
  const { serviceSelection } = useHybridMode();
  
  return {
    dataService: hybridModeService.getDataService(),
    dataServiceType: serviceSelection.dataService
  };
};
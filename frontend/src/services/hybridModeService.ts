import { configurationService } from './configurationService';
import { directAgentService } from './directAgentService';
import { apiBedrockAgentService } from './apiBedrockAgentService';
import { mockDataService } from './mockDataService';
import { bedrockAgentService } from './bedrockAgentService';

/**
 * Hybrid Mode Service - Central service for managing hybrid testing mode
 * Provides unified interface for switching between mock and real services
 */

export interface HybridModeConfig {
  useMockAuth: boolean;
  useMockAgent: boolean;
  useDummyData: boolean;
  isHybridMode: boolean;
  agentConnected: boolean;
  configurationValid: boolean;
}

export interface ServiceSelection {
  authService: 'mock' | 'real';
  agentService: 'mock' | 'direct' | 'api';
  dataService: 'mock' | 'real';
}

class HybridModeService {
  private config: HybridModeConfig | null = null;
  private configListeners: ((config: HybridModeConfig) => void)[] = [];

  /**
   * Initialize hybrid mode service and detect configuration
   */
  async initialize(): Promise<HybridModeConfig> {
    const config = await this.detectConfiguration();
    this.config = config;
    this.notifyListeners(config);
    return config;
  }

  /**
   * Detect current hybrid mode configuration
   */
  async detectConfiguration(): Promise<HybridModeConfig> {
    const useMockAuth = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
    const useMockAgent = import.meta.env.VITE_USE_MOCK_AGENT === 'true';
    const useDummyData = import.meta.env.VITE_USE_DUMMY_DATA === 'true';
    const isHybridMode = useMockAuth && !useMockAgent;

    let agentConnected = false;
    let configurationValid = false;

    if (isHybridMode) {
      try {
        // Validate direct agent service configuration
        const validation = await directAgentService.validateConfiguration();
        configurationValid = validation.valid;
        agentConnected = validation.valid;
      } catch (error) {
        console.warn('Failed to validate direct agent configuration:', error);
        configurationValid = false;
        agentConnected = false;
      }
    } else if (!useMockAgent) {
      try {
        // Validate API agent service configuration
        configurationValid = await apiBedrockAgentService.validateConfiguration();
        agentConnected = configurationValid;
      } catch (error) {
        console.warn('Failed to validate API agent configuration:', error);
        configurationValid = false;
        agentConnected = false;
      }
    } else {
      // Mock mode - always valid
      configurationValid = true;
      agentConnected = true;
    }

    return {
      useMockAuth,
      useMockAgent,
      useDummyData,
      isHybridMode,
      agentConnected,
      configurationValid
    };
  }

  /**
   * Get current configuration
   */
  getConfiguration(): HybridModeConfig {
    if (!this.config) {
      throw new Error('HybridModeService not initialized. Call initialize() first.');
    }
    return this.config;
  }

  /**
   * Determine which services to use based on configuration
   */
  getServiceSelection(): ServiceSelection {
    const config = this.getConfiguration();

    return {
      authService: config.useMockAuth ? 'mock' : 'real',
      agentService: config.useMockAgent ? 'mock' : 
                   config.isHybridMode ? 'direct' : 'api',
      dataService: config.useDummyData ? 'mock' : 'real'
    };
  }

  /**
   * Get appropriate agent service based on configuration
   */
  getAgentService() {
    const selection = this.getServiceSelection();
    
    switch (selection.agentService) {
      case 'direct':
        return directAgentService;
      case 'api':
        return apiBedrockAgentService;
      case 'mock':
      default:
        return bedrockAgentService; // Fallback to mock service
    }
  }

  /**
   * Get appropriate data service based on configuration
   */
  getDataService() {
    const selection = this.getServiceSelection();
    
    switch (selection.dataService) {
      case 'mock':
        return mockDataService;
      case 'real':
      default:
        // Return real data service when implemented
        return mockDataService; // Fallback to mock for now
    }
  }

  /**
   * Check if hybrid testing mode is active
   */
  isHybridTestingMode(): boolean {
    return this.getConfiguration().isHybridMode;
  }

  /**
   * Check if agent is connected and ready
   */
  isAgentConnected(): boolean {
    return this.getConfiguration().agentConnected;
  }

  /**
   * Check if configuration is valid
   */
  isConfigurationValid(): boolean {
    return this.getConfiguration().configurationValid;
  }

  /**
   * Refresh configuration and connectivity status
   */
  async refreshConfiguration(): Promise<HybridModeConfig> {
    const config = await this.detectConfiguration();
    this.config = config;
    this.notifyListeners(config);
    return config;
  }

  /**
   * Subscribe to configuration changes
   */
  onConfigurationChange(listener: (config: HybridModeConfig) => void): () => void {
    this.configListeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.configListeners.indexOf(listener);
      if (index > -1) {
        this.configListeners.splice(index, 1);
      }
    };
  }

  /**
   * Notify all listeners of configuration changes
   */
  private notifyListeners(config: HybridModeConfig): void {
    this.configListeners.forEach(listener => {
      try {
        listener(config);
      } catch (error) {
        console.error('Error in configuration change listener:', error);
      }
    });
  }

  /**
   * Get status indicators for UI display
   */
  getStatusIndicators() {
    const config = this.getConfiguration();
    const selection = this.getServiceSelection();

    return {
      mode: config.isHybridMode ? 'hybrid' : 
            config.useMockAgent ? 'mock' : 'production',
      authStatus: selection.authService === 'mock' ? 'mock' : 'real',
      agentStatus: config.agentConnected ? 'connected' : 'disconnected',
      agentType: selection.agentService,
      configurationStatus: config.configurationValid ? 'valid' : 'invalid',
      indicators: [
        ...(config.isHybridMode ? [{
          type: 'hybrid' as const,
          label: 'Hybrid Mode',
          color: 'blue' as const,
          description: 'Mock auth + Real agent'
        }] : []),
        {
          type: 'agent' as const,
          label: config.agentConnected ? 'AI Ready' : 'AI Offline',
          color: config.agentConnected ? 'green' as const : 'red' as const,
          description: `Agent service: ${selection.agentService}`
        },
        ...(config.useMockAuth ? [{
          type: 'auth' as const,
          label: 'Mock Auth',
          color: 'yellow' as const,
          description: 'Development authentication'
        }] : [])
      ]
    };
  }

  /**
   * Get setup instructions based on current configuration issues
   */
  getSetupInstructions(): string[] {
    const config = this.getConfiguration();
    
    if (config.configurationValid && config.agentConnected) {
      return ['✅ Configuration is complete and ready for testing!'];
    }

    const instructions: string[] = [];

    if (config.isHybridMode && !config.agentConnected) {
      instructions.push(
        '1. Configure AWS credentials:',
        '   - Run "aws configure" in your terminal',
        '   - Or set VITE_AWS_ACCESS_KEY_ID and VITE_AWS_SECRET_ACCESS_KEY',
        '',
        '2. Configure Bedrock Agent:',
        '   - Set VITE_BEDROCK_AGENT_ID to your agent ID',
        '   - Set VITE_BEDROCK_AGENT_ALIAS_ID to your agent alias',
        '   - Set VITE_AWS_REGION to your AWS region',
        '',
        '3. Verify agent deployment:',
        '   - Check that the agent exists in AWS Bedrock console',
        '   - Ensure the agent alias is deployed and active',
        '   - Verify IAM permissions for bedrock:InvokeAgent'
      );
    } else if (!config.useMockAgent && !config.agentConnected) {
      instructions.push(
        '1. Check API Gateway configuration:',
        '   - Verify API endpoint is accessible',
        '   - Check authentication configuration',
        '',
        '2. Verify backend services:',
        '   - Ensure Lambda functions are deployed',
        '   - Check CloudWatch logs for errors'
      );
    }

    return instructions;
  }

  /**
   * Get diagnostic information for troubleshooting
   */
  getDiagnosticInfo(): Record<string, any> {
    const config = this.getConfiguration();
    const selection = this.getServiceSelection();

    return {
      timestamp: new Date().toISOString(),
      configuration: config,
      serviceSelection: selection,
      environment: {
        nodeEnv: import.meta.env.MODE,
        viteEnv: import.meta.env.DEV ? 'development' : 'production',
        envVars: {
          VITE_USE_MOCK_AUTH: import.meta.env.VITE_USE_MOCK_AUTH,
          VITE_USE_MOCK_AGENT: import.meta.env.VITE_USE_MOCK_AGENT,
          VITE_USE_DUMMY_DATA: import.meta.env.VITE_USE_DUMMY_DATA,
          VITE_AWS_REGION: import.meta.env.VITE_AWS_REGION,
          VITE_BEDROCK_AGENT_ID: import.meta.env.VITE_BEDROCK_AGENT_ID,
          VITE_BEDROCK_AGENT_ALIAS_ID: import.meta.env.VITE_BEDROCK_AGENT_ALIAS_ID,
          hasAwsCredentials: !!(import.meta.env.VITE_AWS_ACCESS_KEY_ID && import.meta.env.VITE_AWS_SECRET_ACCESS_KEY)
        }
      },
      browser: {
        userAgent: navigator.userAgent,
        language: navigator.language,
        onLine: navigator.onLine
      }
    };
  }

  /**
   * Test agent connectivity
   */
  async testAgentConnectivity(): Promise<{
    success: boolean;
    message: string;
    details?: any;
  }> {
    const config = this.getConfiguration();
    const selection = this.getServiceSelection();

    try {
      if (selection.agentService === 'direct') {
        const response = await directAgentService.sendMessage(
          'Hello, this is a connectivity test.',
          undefined,
          true // isTest flag
        );

        if (response.error) {
          return {
            success: false,
            message: `Direct agent test failed: ${response.error}`,
            details: response
          };
        }

        return {
          success: true,
          message: 'Direct agent connectivity test successful',
          details: {
            sessionId: response.sessionId,
            responseLength: response.content.length,
            processingTime: response.metadata?.processingTime
          }
        };
      } else if (selection.agentService === 'api') {
        const response = await apiBedrockAgentService.sendMessage(
          'Hello, this is a connectivity test.',
          'test-session',
          'test-user'
        );

        return {
          success: response.success,
          message: response.success ? 
            'API agent connectivity test successful' : 
            `API agent test failed: ${response.error}`,
          details: response
        };
      } else {
        return {
          success: true,
          message: 'Mock agent service - no connectivity test needed',
          details: { mode: 'mock' }
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `Agent connectivity test failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        details: { error: error instanceof Error ? error.message : error }
      };
    }
  }

  /**
   * Switch to different mode (for testing purposes)
   */
  async switchMode(newMode: 'hybrid' | 'mock' | 'production'): Promise<void> {
    // This would typically update environment variables or configuration
    // For now, we'll just log the request
    console.log(`Mode switch requested: ${newMode}`);
    console.warn('Mode switching requires environment variable changes and application restart');
    
    // In a real implementation, this might:
    // 1. Update local storage configuration
    // 2. Trigger a configuration refresh
    // 3. Notify the user about required restart
  }
}

// Export singleton instance
export const hybridModeService = new HybridModeService();

// Export types and class for testing
export { HybridModeService };
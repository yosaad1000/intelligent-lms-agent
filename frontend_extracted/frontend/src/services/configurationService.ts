import { BedrockAgentRuntimeClient, InvokeAgentCommand } from '@aws-sdk/client-bedrock-agent-runtime';

export interface ConfigurationStatus {
  valid: boolean;
  errors: string[];
  warnings: string[];
  details: {
    awsCredentials: 'valid' | 'invalid' | 'missing';
    agentConfiguration: 'valid' | 'invalid' | 'missing';
    agentConnectivity: 'connected' | 'failed' | 'untested';
    region: string;
    agentId: string;
    agentAliasId: string;
  };
  lastChecked: Date;
}

export interface EnvironmentConfig {
  awsRegion: string;
  awsAccessKeyId: string;
  awsSecretAccessKey: string;
  bedrockAgentId: string;
  bedrockAgentAliasId: string;
  useMockAuth: boolean;
  useMockAgent: boolean;
  useDummyData: boolean;
}

class ConfigurationService {
  private cachedStatus: ConfigurationStatus | null = null;
  private cacheExpiry: number = 5 * 60 * 1000; // 5 minutes

  /**
   * Get current environment configuration
   */
  getEnvironmentConfig(): EnvironmentConfig {
    return {
      awsRegion: import.meta.env.VITE_AWS_REGION || 'us-east-1',
      awsAccessKeyId: import.meta.env.VITE_AWS_ACCESS_KEY_ID || '',
      awsSecretAccessKey: import.meta.env.VITE_AWS_SECRET_ACCESS_KEY || '',
      bedrockAgentId: import.meta.env.VITE_BEDROCK_AGENT_ID || '',
      bedrockAgentAliasId: import.meta.env.VITE_BEDROCK_AGENT_ALIAS_ID || '',
      useMockAuth: import.meta.env.VITE_USE_MOCK_AUTH === 'true',
      useMockAgent: import.meta.env.VITE_USE_MOCK_AGENT === 'true',
      useDummyData: import.meta.env.VITE_USE_DUMMY_DATA === 'true'
    };
  }

  /**
   * Check if we're in hybrid testing mode
   */
  isHybridTestingMode(): boolean {
    const config = this.getEnvironmentConfig();
    return config.useMockAuth && !config.useMockAgent;
  }

  /**
   * Validate complete configuration
   */
  async validateConfiguration(forceRefresh: boolean = false): Promise<ConfigurationStatus> {
    // Return cached result if still valid
    if (!forceRefresh && this.cachedStatus && 
        Date.now() - this.cachedStatus.lastChecked.getTime() < this.cacheExpiry) {
      return this.cachedStatus;
    }

    const config = this.getEnvironmentConfig();
    const status: ConfigurationStatus = {
      valid: true,
      errors: [],
      warnings: [],
      details: {
        awsCredentials: 'missing',
        agentConfiguration: 'missing',
        agentConnectivity: 'untested',
        region: config.awsRegion,
        agentId: config.bedrockAgentId,
        agentAliasId: config.bedrockAgentAliasId
      },
      lastChecked: new Date()
    };

    // Validate AWS credentials
    try {
      await this.validateAwsCredentials(config);
      status.details.awsCredentials = 'valid';
    } catch (error) {
      status.details.awsCredentials = 'invalid';
      status.errors.push(`AWS Credentials: ${error instanceof Error ? error.message : 'Invalid credentials'}`);
      status.valid = false;
    }

    // Validate agent configuration
    try {
      this.validateAgentConfiguration(config);
      status.details.agentConfiguration = 'valid';
    } catch (error) {
      status.details.agentConfiguration = 'invalid';
      status.errors.push(`Agent Configuration: ${error instanceof Error ? error.message : 'Invalid configuration'}`);
      status.valid = false;
    }

    // Test agent connectivity (only if credentials and config are valid)
    if (status.details.awsCredentials === 'valid' && status.details.agentConfiguration === 'valid') {
      try {
        await this.testAgentConnectivity(config);
        status.details.agentConnectivity = 'connected';
      } catch (error) {
        status.details.agentConnectivity = 'failed';
        status.errors.push(`Agent Connectivity: ${error instanceof Error ? error.message : 'Connection failed'}`);
        status.valid = false;
      }
    }

    // Add warnings for hybrid testing mode
    if (this.isHybridTestingMode()) {
      status.warnings.push('Running in hybrid testing mode - using mock authentication with real AWS services');
    }

    // Cache the result
    this.cachedStatus = status;
    return status;
  }

  /**
   * Validate AWS credentials
   */
  private async validateAwsCredentials(config: EnvironmentConfig): Promise<void> {
    if (!config.awsAccessKeyId || !config.awsSecretAccessKey) {
      throw new Error('AWS Access Key ID and Secret Access Key are required');
    }

    if (config.awsAccessKeyId.length < 16 || config.awsAccessKeyId.length > 32) {
      throw new Error('AWS Access Key ID format appears invalid');
    }

    if (config.awsSecretAccessKey.length < 40) {
      throw new Error('AWS Secret Access Key format appears invalid');
    }

    // For now, we'll skip STS validation to avoid additional dependencies
    // In production, you might want to add STS validation
    console.log('✅ AWS credentials format validated successfully');
  }

  /**
   * Validate agent configuration
   */
  private validateAgentConfiguration(config: EnvironmentConfig): void {
    if (!config.bedrockAgentId) {
      throw new Error('Bedrock Agent ID is required (VITE_BEDROCK_AGENT_ID)');
    }

    if (!config.bedrockAgentAliasId) {
      throw new Error('Bedrock Agent Alias ID is required (VITE_BEDROCK_AGENT_ALIAS_ID)');
    }

    // Validate agent ID format (should be alphanumeric, 10 characters)
    if (!/^[A-Z0-9]{10}$/.test(config.bedrockAgentId)) {
      throw new Error('Bedrock Agent ID format appears invalid (should be 10 alphanumeric characters)');
    }

    // Validate alias ID format
    if (config.bedrockAgentAliasId !== 'TSTALIASID' && 
        !/^[A-Z0-9]{10}$/.test(config.bedrockAgentAliasId)) {
      throw new Error('Bedrock Agent Alias ID format appears invalid');
    }

    // Validate region
    const validRegions = [
      'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 
      'ap-southeast-1', 'ap-northeast-1'
    ];
    
    if (!validRegions.includes(config.awsRegion)) {
      throw new Error(`AWS region '${config.awsRegion}' may not support Bedrock services`);
    }

    console.log('✅ Agent configuration validated successfully');
  }

  /**
   * Test agent connectivity
   */
  private async testAgentConnectivity(config: EnvironmentConfig): Promise<void> {
    const bedrockClient = new BedrockAgentRuntimeClient({
      region: config.awsRegion,
      credentials: {
        accessKeyId: config.awsAccessKeyId,
        secretAccessKey: config.awsSecretAccessKey
      }
    });

    try {
      const command = new InvokeAgentCommand({
        agentId: config.bedrockAgentId,
        agentAliasId: config.bedrockAgentAliasId,
        sessionId: `config-test-${Date.now()}`,
        inputText: 'Hello, this is a configuration test.'
      });

      const response = await bedrockClient.send(command);
      
      if (!response.completion) {
        throw new Error('Agent responded but completion stream is empty');
      }

      // Try to read at least one chunk from the stream
      let hasResponse = false;
      for await (const chunk of response.completion) {
        if (chunk.chunk?.bytes) {
          hasResponse = true;
          break;
        }
      }

      if (!hasResponse) {
        throw new Error('Agent responded but no content was received');
      }

      console.log('✅ Agent connectivity test successful');
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'ResourceNotFoundException') {
          throw new Error(`Agent not found: ${config.bedrockAgentId} with alias ${config.bedrockAgentAliasId}`);
        } else if (error.name === 'AccessDeniedException') {
          throw new Error('Access denied - check IAM permissions for Bedrock Agent access');
        } else if (error.name === 'ValidationException') {
          throw new Error('Invalid agent ID or alias ID format');
        } else if (error.name === 'ThrottlingException') {
          throw new Error('Request throttled - too many requests to Bedrock service');
        } else if (error.name === 'ServiceUnavailableException') {
          throw new Error('Bedrock service is temporarily unavailable');
        }
      }
      throw new Error(`Agent connectivity test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get configuration status summary for UI display
   */
  getStatusSummary(status: ConfigurationStatus): {
    overall: 'ready' | 'warning' | 'error';
    message: string;
    actionRequired: boolean;
  } {
    if (!status.valid) {
      return {
        overall: 'error',
        message: `Configuration errors: ${status.errors.join(', ')}`,
        actionRequired: true
      };
    }

    if (status.warnings.length > 0) {
      return {
        overall: 'warning',
        message: `Configuration warnings: ${status.warnings.join(', ')}`,
        actionRequired: false
      };
    }

    return {
      overall: 'ready',
      message: 'Configuration is valid and agent is ready for testing',
      actionRequired: false
    };
  }

  /**
   * Get setup instructions based on current configuration issues
   */
  getSetupInstructions(status: ConfigurationStatus): string[] {
    const instructions: string[] = [];

    if (status.details.awsCredentials === 'invalid' || status.details.awsCredentials === 'missing') {
      instructions.push(
        '1. Configure AWS credentials:',
        '   - Run "aws configure" in your terminal',
        '   - Or set VITE_AWS_ACCESS_KEY_ID and VITE_AWS_SECRET_ACCESS_KEY environment variables'
      );
    }

    if (status.details.agentConfiguration === 'invalid' || status.details.agentConfiguration === 'missing') {
      instructions.push(
        '2. Configure Bedrock Agent:',
        '   - Set VITE_BEDROCK_AGENT_ID to your agent ID (e.g., ZTBBVSC6Y1)',
        '   - Set VITE_BEDROCK_AGENT_ALIAS_ID to your agent alias (e.g., TSTALIASID)',
        '   - Set VITE_AWS_REGION to your AWS region (e.g., us-east-1)'
      );
    }

    if (status.details.agentConnectivity === 'failed') {
      instructions.push(
        '3. Check agent deployment:',
        '   - Verify the agent exists in AWS Bedrock console',
        '   - Ensure the agent alias is deployed and active',
        '   - Check IAM permissions for bedrock:InvokeAgent'
      );
    }

    if (instructions.length === 0) {
      instructions.push('✅ Configuration is complete and ready for testing!');
    }

    return instructions;
  }

  /**
   * Clear cached configuration status
   */
  clearCache(): void {
    this.cachedStatus = null;
  }

  /**
   * Get diagnostic information for troubleshooting
   */
  getDiagnosticInfo(): Record<string, any> {
    const config = this.getEnvironmentConfig();
    
    return {
      timestamp: new Date().toISOString(),
      environment: {
        nodeEnv: import.meta.env.MODE,
        viteEnv: import.meta.env.DEV ? 'development' : 'production'
      },
      configuration: {
        awsRegion: config.awsRegion,
        hasAwsAccessKeyId: !!config.awsAccessKeyId,
        hasAwsSecretAccessKey: !!config.awsSecretAccessKey,
        bedrockAgentId: config.bedrockAgentId,
        bedrockAgentAliasId: config.bedrockAgentAliasId,
        useMockAuth: config.useMockAuth,
        useMockAgent: config.useMockAgent,
        useDummyData: config.useDummyData,
        isHybridMode: this.isHybridTestingMode()
      },
      browser: {
        userAgent: navigator.userAgent,
        language: navigator.language,
        onLine: navigator.onLine
      },
      lastValidation: this.cachedStatus?.lastChecked?.toISOString() || 'never'
    };
  }
}

// Export singleton instance
export const configurationService = new ConfigurationService();

// Export types and class for testing
export { ConfigurationService };
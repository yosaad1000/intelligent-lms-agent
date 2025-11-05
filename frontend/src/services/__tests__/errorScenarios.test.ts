import { hybridModeService } from '../hybridModeService';
import { directAgentService } from '../directAgentService';
import { errorHandlingService } from '../errorHandlingService';

// Mock the services
jest.mock('../directAgentService');
jest.mock('../errorHandlingService');

const mockDirectAgentService = directAgentService as jest.Mocked<typeof directAgentService>;
const mockErrorHandlingService = errorHandlingService as jest.Mocked<typeof errorHandlingService>;

describe('Error Scenario Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock environment variables for hybrid mode
    Object.defineProperty(import.meta, 'env', {
      value: {
        VITE_USE_MOCK_AUTH: 'true',
        VITE_USE_MOCK_AGENT: 'false',
        VITE_USE_DUMMY_DATA: 'true',
        VITE_AWS_REGION: 'us-east-1',
        VITE_BEDROCK_AGENT_ID: 'ZTBBVSC6Y1',
        VITE_BEDROCK_AGENT_ALIAS_ID: 'TSTALIASID',
        VITE_AWS_ACCESS_KEY_ID: 'test-key',
        VITE_AWS_SECRET_ACCESS_KEY: 'test-secret'
      },
      writable: true
    });
  });

  describe('Network Connectivity Issues', () => {
    it('should handle network timeout errors', async () => {
      const timeoutError = new Error('Network timeout');
      timeoutError.name = 'TimeoutError';
      
      mockDirectAgentService.validateConfiguration.mockRejectedValue(timeoutError);
      
      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });

    it('should handle DNS resolution failures', async () => {
      const dnsError = new Error('DNS resolution failed');
      dnsError.name = 'DNSError';
      
      mockDirectAgentService.sendMessage.mockRejectedValue(dnsError);
      
      const testResult = await hybridModeService.testAgentConnectivity();
      
      expect(testResult.success).toBe(false);
      expect(testResult.message).toContain('failed');
    });

    it('should handle intermittent connectivity issues', async () => {
      // Simulate intermittent failures
      let callCount = 0;
      mockDirectAgentService.validateConfiguration.mockImplementation(() => {
        callCount++;
        if (callCount % 2 === 0) {
          return Promise.resolve({
            valid: true,
            errors: [],
            warnings: [],
            details: {
              awsCredentials: 'valid',
              agentConfiguration: 'valid',
              agentConnectivity: 'connected',
              region: 'us-east-1',
              agentId: 'ZTBBVSC6Y1',
              agentAliasId: 'TSTALIASID'
            },
            lastChecked: new Date()
          });
        } else {
          return Promise.reject(new Error('Intermittent failure'));
        }
      });

      // First call should fail
      const config1 = await hybridModeService.detectConfiguration();
      expect(config1.agentConnected).toBe(false);

      // Second call should succeed
      const config2 = await hybridModeService.detectConfiguration();
      expect(config2.agentConnected).toBe(true);
    });
  });

  describe('AWS Service Errors', () => {
    it('should handle invalid credentials error', async () => {
      const credentialsError = new Error('Invalid AWS credentials');
      credentialsError.name = 'CredentialsError';
      
      mockDirectAgentService.validateConfiguration.mockRejectedValue(credentialsError);
      
      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });

    it('should handle resource not found error', async () => {
      const notFoundError = new Error('Agent not found');
      notFoundError.name = 'ResourceNotFoundException';
      
      mockDirectAgentService.sendMessage.mockResolvedValue({
        sessionId: 'test-session',
        messageId: 'test-message',
        content: '',
        timestamp: new Date(),
        error: 'Agent not found: ZTBBVSC6Y1 with alias TSTALIASID'
      });
      
      const testResult = await hybridModeService.testAgentConnectivity();
      
      expect(testResult.success).toBe(false);
      expect(testResult.message).toContain('failed');
    });

    it('should handle access denied error', async () => {
      const accessDeniedError = new Error('Access denied');
      accessDeniedError.name = 'AccessDeniedException';
      
      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: false,
        errors: ['Access denied - check IAM permissions for Bedrock Agent access'],
        warnings: [],
        details: {
          awsCredentials: 'valid',
          agentConfiguration: 'valid',
          agentConnectivity: 'failed',
          region: 'us-east-1',
          agentId: 'ZTBBVSC6Y1',
          agentAliasId: 'TSTALIASID'
        },
        lastChecked: new Date()
      });
      
      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });

    it('should handle throttling errors', async () => {
      const throttlingError = new Error('Request throttled');
      throttlingError.name = 'ThrottlingException';
      
      mockDirectAgentService.sendMessage.mockResolvedValue({
        sessionId: 'test-session',
        messageId: 'test-message',
        content: '',
        timestamp: new Date(),
        error: 'Request throttled - too many requests to Bedrock service'
      });
      
      const testResult = await hybridModeService.testAgentConnectivity();
      
      expect(testResult.success).toBe(false);
      expect(testResult.message).toContain('throttled');
    });

    it('should handle service unavailable error', async () => {
      const serviceUnavailableError = new Error('Service unavailable');
      serviceUnavailableError.name = 'ServiceUnavailableException';
      
      mockDirectAgentService.validateConfiguration.mockRejectedValue(serviceUnavailableError);
      
      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });
  });

  describe('Configuration Errors', () => {
    it('should handle missing environment variables', async () => {
      // Remove required environment variables
      Object.defineProperty(import.meta, 'env', {
        value: {
          VITE_USE_MOCK_AUTH: 'true',
          VITE_USE_MOCK_AGENT: 'false',
          // Missing AWS configuration
        },
        writable: true
      });

      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: false,
        errors: ['AWS Access Key ID and Secret Access Key are required'],
        warnings: [],
        details: {
          awsCredentials: 'missing',
          agentConfiguration: 'missing',
          agentConnectivity: 'untested',
          region: '',
          agentId: '',
          agentAliasId: ''
        },
        lastChecked: new Date()
      });

      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });

    it('should handle invalid agent ID format', async () => {
      Object.defineProperty(import.meta, 'env', {
        value: {
          VITE_USE_MOCK_AUTH: 'true',
          VITE_USE_MOCK_AGENT: 'false',
          VITE_AWS_REGION: 'us-east-1',
          VITE_BEDROCK_AGENT_ID: 'invalid-format',
          VITE_BEDROCK_AGENT_ALIAS_ID: 'TSTALIASID',
          VITE_AWS_ACCESS_KEY_ID: 'test-key',
          VITE_AWS_SECRET_ACCESS_KEY: 'test-secret'
        },
        writable: true
      });

      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: false,
        errors: ['Bedrock Agent ID format appears invalid (should be 10 alphanumeric characters)'],
        warnings: [],
        details: {
          awsCredentials: 'valid',
          agentConfiguration: 'invalid',
          agentConnectivity: 'untested',
          region: 'us-east-1',
          agentId: 'invalid-format',
          agentAliasId: 'TSTALIASID'
        },
        lastChecked: new Date()
      });

      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });

    it('should handle unsupported AWS region', async () => {
      Object.defineProperty(import.meta, 'env', {
        value: {
          VITE_USE_MOCK_AUTH: 'true',
          VITE_USE_MOCK_AGENT: 'false',
          VITE_AWS_REGION: 'unsupported-region',
          VITE_BEDROCK_AGENT_ID: 'ZTBBVSC6Y1',
          VITE_BEDROCK_AGENT_ALIAS_ID: 'TSTALIASID',
          VITE_AWS_ACCESS_KEY_ID: 'test-key',
          VITE_AWS_SECRET_ACCESS_KEY: 'test-secret'
        },
        writable: true
      });

      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: false,
        errors: ["AWS region 'unsupported-region' may not support Bedrock services"],
        warnings: [],
        details: {
          awsCredentials: 'valid',
          agentConfiguration: 'invalid',
          agentConnectivity: 'untested',
          region: 'unsupported-region',
          agentId: 'ZTBBVSC6Y1',
          agentAliasId: 'TSTALIASID'
        },
        lastChecked: new Date()
      });

      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });
  });

  describe('Agent Response Errors', () => {
    it('should handle empty agent responses', async () => {
      mockDirectAgentService.sendMessage.mockResolvedValue({
        sessionId: 'test-session',
        messageId: 'test-message',
        content: '',
        timestamp: new Date()
      });

      const testResult = await hybridModeService.testAgentConnectivity();
      
      // Empty response should still be considered successful if no error
      expect(testResult.success).toBe(true);
    });

    it('should handle malformed agent responses', async () => {
      mockDirectAgentService.sendMessage.mockResolvedValue({
        sessionId: 'test-session',
        messageId: 'test-message',
        content: 'Malformed response without proper structure',
        timestamp: new Date()
      });

      const testResult = await hybridModeService.testAgentConnectivity();
      
      expect(testResult.success).toBe(true);
      expect(testResult.details).toBeDefined();
    });

    it('should handle agent timeout responses', async () => {
      mockDirectAgentService.sendMessage.mockResolvedValue({
        sessionId: 'test-session',
        messageId: 'test-message',
        content: '',
        timestamp: new Date(),
        error: 'Request timeout - agent took too long to respond'
      });

      const testResult = await hybridModeService.testAgentConnectivity();
      
      expect(testResult.success).toBe(false);
      expect(testResult.message).toContain('timeout');
    });
  });

  describe('Fallback and Recovery', () => {
    it('should provide fallback when direct agent fails', async () => {
      // Simulate direct agent failure
      mockDirectAgentService.validateConfiguration.mockRejectedValue(
        new Error('Direct agent unavailable')
      );

      const config = await hybridModeService.detectConfiguration();
      
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
      
      // Service should still provide setup instructions
      const instructions = hybridModeService.getSetupInstructions();
      expect(instructions.length).toBeGreaterThan(0);
    });

    it('should recover after configuration fix', async () => {
      // First call fails
      mockDirectAgentService.validateConfiguration
        .mockRejectedValueOnce(new Error('Configuration error'))
        .mockResolvedValueOnce({
          valid: true,
          errors: [],
          warnings: [],
          details: {
            awsCredentials: 'valid',
            agentConfiguration: 'valid',
            agentConnectivity: 'connected',
            region: 'us-east-1',
            agentId: 'ZTBBVSC6Y1',
            agentAliasId: 'TSTALIASID'
          },
          lastChecked: new Date()
        });

      // Initial configuration should fail
      const config1 = await hybridModeService.detectConfiguration();
      expect(config1.agentConnected).toBe(false);

      // After refresh, should succeed
      const config2 = await hybridModeService.refreshConfiguration();
      expect(config2.agentConnected).toBe(true);
    });

    it('should handle partial service failures gracefully', async () => {
      // Agent validation succeeds but connectivity test fails
      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: true,
        errors: [],
        warnings: [],
        details: {
          awsCredentials: 'valid',
          agentConfiguration: 'valid',
          agentConnectivity: 'connected',
          region: 'us-east-1',
          agentId: 'ZTBBVSC6Y1',
          agentAliasId: 'TSTALIASID'
        },
        lastChecked: new Date()
      });

      mockDirectAgentService.sendMessage.mockRejectedValue(
        new Error('Connectivity test failed')
      );

      await hybridModeService.initialize();
      
      const testResult = await hybridModeService.testAgentConnectivity();
      
      expect(testResult.success).toBe(false);
      expect(testResult.message).toContain('failed');
      
      // But configuration should still be considered valid
      const config = hybridModeService.getConfiguration();
      expect(config.configurationValid).toBe(true);
    });
  });

  describe('Error Reporting and Diagnostics', () => {
    it('should provide detailed diagnostic information on errors', async () => {
      mockDirectAgentService.validateConfiguration.mockRejectedValue(
        new Error('Test error for diagnostics')
      );

      await hybridModeService.initialize();
      
      const diagnostics = hybridModeService.getDiagnosticInfo();
      
      expect(diagnostics).toBeDefined();
      expect(diagnostics.timestamp).toBeDefined();
      expect(diagnostics.configuration).toBeDefined();
      expect(diagnostics.environment).toBeDefined();
      expect(diagnostics.browser).toBeDefined();
    });

    it('should track error patterns for debugging', async () => {
      // Simulate multiple errors
      const errors = [
        new Error('Network error 1'),
        new Error('Network error 2'),
        new Error('Configuration error')
      ];

      for (const error of errors) {
        mockDirectAgentService.validateConfiguration.mockRejectedValueOnce(error);
        await hybridModeService.detectConfiguration();
      }

      // Service should maintain error history for debugging
      const diagnostics = hybridModeService.getDiagnosticInfo();
      expect(diagnostics).toBeDefined();
    });

    it('should provide actionable error messages', async () => {
      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: false,
        errors: ['Invalid AWS credentials', 'Agent not found'],
        warnings: ['Using test environment'],
        details: {
          awsCredentials: 'invalid',
          agentConfiguration: 'invalid',
          agentConnectivity: 'failed',
          region: 'us-east-1',
          agentId: 'ZTBBVSC6Y1',
          agentAliasId: 'TSTALIASID'
        },
        lastChecked: new Date()
      });

      await hybridModeService.initialize();
      
      const instructions = hybridModeService.getSetupInstructions();
      
      expect(instructions.length).toBeGreaterThan(1);
      expect(instructions.join(' ')).toContain('Configure AWS credentials');
      expect(instructions.join(' ')).toContain('Configure Bedrock Agent');
    });
  });
});
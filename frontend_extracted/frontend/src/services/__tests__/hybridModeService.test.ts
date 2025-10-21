import { describe, it, expect, beforeEach, vi } from 'vitest';
import { HybridModeService } from '../hybridModeService';
import { directAgentService } from '../directAgentService';
import { apiBedrockAgentService } from '../apiBedrockAgentService';

// Mock the services
vi.mock('../directAgentService');
vi.mock('../apiBedrockAgentService');
vi.mock('../configurationService');

const mockDirectAgentService = vi.mocked(directAgentService);
const mockApiBedrockAgentService = vi.mocked(apiBedrockAgentService);

// Mock environment variables
const mockEnv = {
  VITE_USE_MOCK_AUTH: 'true',
  VITE_USE_MOCK_AGENT: 'false',
  VITE_USE_DUMMY_DATA: 'true',
  VITE_AWS_REGION: 'us-east-1',
  VITE_BEDROCK_AGENT_ID: 'ZTBBVSC6Y1',
  VITE_BEDROCK_AGENT_ALIAS_ID: 'TSTALIASID',
  VITE_AWS_ACCESS_KEY_ID: 'test-key',
  VITE_AWS_SECRET_ACCESS_KEY: 'test-secret'
};

describe('HybridModeService', () => {
  let service: HybridModeService;

  beforeEach(() => {
    service = new HybridModeService();
    
    // Reset mocks
    vi.clearAllMocks();
    
    // Mock import.meta.env
    Object.defineProperty(import.meta, 'env', {
      value: mockEnv,
      writable: true
    });
  });

  describe('detectConfiguration', () => {
    it('should detect hybrid mode correctly', async () => {
      // Mock successful validation
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

      const config = await service.detectConfiguration();

      expect(config.isHybridMode).toBe(true);
      expect(config.useMockAuth).toBe(true);
      expect(config.useMockAgent).toBe(false);
      expect(config.agentConnected).toBe(true);
      expect(config.configurationValid).toBe(true);
    });

    it('should detect non-hybrid mode correctly', async () => {
      // Change environment to non-hybrid
      Object.defineProperty(import.meta, 'env', {
        value: { ...mockEnv, VITE_USE_MOCK_AGENT: 'true' },
        writable: true
      });

      const config = await service.detectConfiguration();

      expect(config.isHybridMode).toBe(false);
      expect(config.useMockAuth).toBe(true);
      expect(config.useMockAgent).toBe(true);
      expect(config.agentConnected).toBe(true); // Mock mode is always connected
      expect(config.configurationValid).toBe(true);
    });

    it('should handle validation failures', async () => {
      // Mock failed validation
      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: false,
        errors: ['Invalid credentials'],
        warnings: [],
        details: {
          awsCredentials: 'invalid',
          agentConfiguration: 'valid',
          agentConnectivity: 'failed',
          region: 'us-east-1',
          agentId: 'ZTBBVSC6Y1',
          agentAliasId: 'TSTALIASID'
        },
        lastChecked: new Date()
      });

      const config = await service.detectConfiguration();

      expect(config.isHybridMode).toBe(true);
      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });
  });

  describe('getServiceSelection', () => {
    it('should return correct service selection for hybrid mode', async () => {
      await service.initialize();
      
      const selection = service.getServiceSelection();

      expect(selection.authService).toBe('mock');
      expect(selection.agentService).toBe('direct');
      expect(selection.dataService).toBe('mock');
    });

    it('should return correct service selection for mock mode', async () => {
      // Change to mock mode
      Object.defineProperty(import.meta, 'env', {
        value: { ...mockEnv, VITE_USE_MOCK_AGENT: 'true' },
        writable: true
      });

      await service.initialize();
      
      const selection = service.getServiceSelection();

      expect(selection.authService).toBe('mock');
      expect(selection.agentService).toBe('mock');
      expect(selection.dataService).toBe('mock');
    });

    it('should return correct service selection for production mode', async () => {
      // Change to production mode
      Object.defineProperty(import.meta, 'env', {
        value: { 
          ...mockEnv, 
          VITE_USE_MOCK_AUTH: 'false',
          VITE_USE_MOCK_AGENT: 'false',
          VITE_USE_DUMMY_DATA: 'false'
        },
        writable: true
      });

      mockApiBedrockAgentService.validateConfiguration.mockResolvedValue(true);

      await service.initialize();
      
      const selection = service.getServiceSelection();

      expect(selection.authService).toBe('real');
      expect(selection.agentService).toBe('api');
      expect(selection.dataService).toBe('real');
    });
  });

  describe('testAgentConnectivity', () => {
    it('should test direct agent connectivity successfully', async () => {
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

      mockDirectAgentService.sendMessage.mockResolvedValue({
        sessionId: 'test-session',
        messageId: 'test-message',
        content: 'Test response',
        timestamp: new Date(),
        metadata: { processingTime: 1000 }
      });

      await service.initialize();
      
      const result = await service.testAgentConnectivity();

      expect(result.success).toBe(true);
      expect(result.message).toContain('successful');
      expect(mockDirectAgentService.sendMessage).toHaveBeenCalledWith(
        'Hello, this is a connectivity test.',
        undefined,
        true
      );
    });

    it('should handle direct agent connectivity failures', async () => {
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

      mockDirectAgentService.sendMessage.mockResolvedValue({
        sessionId: 'test-session',
        messageId: 'test-message',
        content: '',
        timestamp: new Date(),
        error: 'Connection failed'
      });

      await service.initialize();
      
      const result = await service.testAgentConnectivity();

      expect(result.success).toBe(false);
      expect(result.message).toContain('failed');
    });

    it('should test API agent connectivity', async () => {
      // Change to API mode
      Object.defineProperty(import.meta, 'env', {
        value: { 
          ...mockEnv, 
          VITE_USE_MOCK_AUTH: 'false',
          VITE_USE_MOCK_AGENT: 'false'
        },
        writable: true
      });

      mockApiBedrockAgentService.validateConfiguration.mockResolvedValue(true);
      mockApiBedrockAgentService.sendMessage.mockResolvedValue({
        success: true,
        message: {
          id: 'test-id',
          content: 'Test response',
          sender: 'agent',
          timestamp: new Date()
        }
      });

      await service.initialize();
      
      const result = await service.testAgentConnectivity();

      expect(result.success).toBe(true);
      expect(mockApiBedrockAgentService.sendMessage).toHaveBeenCalled();
    });

    it('should handle mock mode connectivity test', async () => {
      // Change to mock mode
      Object.defineProperty(import.meta, 'env', {
        value: { ...mockEnv, VITE_USE_MOCK_AGENT: 'true' },
        writable: true
      });

      await service.initialize();
      
      const result = await service.testAgentConnectivity();

      expect(result.success).toBe(true);
      expect(result.message).toContain('Mock agent service');
    });
  });

  describe('configuration change listeners', () => {
    it('should notify listeners of configuration changes', async () => {
      const listener = vi.fn();
      
      const unsubscribe = service.onConfigurationChange(listener);
      
      await service.initialize();
      
      expect(listener).toHaveBeenCalledWith(expect.objectContaining({
        isHybridMode: true,
        useMockAuth: true,
        useMockAgent: false
      }));
      
      unsubscribe();
    });

    it('should handle listener errors gracefully', async () => {
      const errorListener = vi.fn(() => {
        throw new Error('Listener error');
      });
      
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      service.onConfigurationChange(errorListener);
      
      await service.initialize();
      
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error in configuration change listener:',
        expect.any(Error)
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('getStatusIndicators', () => {
    it('should return correct status indicators for hybrid mode', async () => {
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

      await service.initialize();
      
      const indicators = service.getStatusIndicators();

      expect(indicators.mode).toBe('hybrid');
      expect(indicators.agentStatus).toBe('connected');
      expect(indicators.indicators).toContainEqual(
        expect.objectContaining({
          type: 'hybrid',
          label: 'Hybrid Mode',
          color: 'blue'
        })
      );
      expect(indicators.indicators).toContainEqual(
        expect.objectContaining({
          type: 'agent',
          label: 'AI Ready',
          color: 'green'
        })
      );
    });
  });

  describe('getSetupInstructions', () => {
    it('should return setup complete message when configuration is valid', async () => {
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

      await service.initialize();
      
      const instructions = service.getSetupInstructions();

      expect(instructions).toContain('✅ Configuration is complete and ready for testing!');
    });

    it('should return setup instructions when configuration is invalid', async () => {
      mockDirectAgentService.validateConfiguration.mockResolvedValue({
        valid: false,
        errors: ['Invalid credentials'],
        warnings: [],
        details: {
          awsCredentials: 'invalid',
          agentConfiguration: 'valid',
          agentConnectivity: 'failed',
          region: 'us-east-1',
          agentId: 'ZTBBVSC6Y1',
          agentAliasId: 'TSTALIASID'
        },
        lastChecked: new Date()
      });

      await service.initialize();
      
      const instructions = service.getSetupInstructions();

      expect(instructions.length).toBeGreaterThan(1);
      expect(instructions.join(' ')).toContain('Configure AWS credentials');
      expect(instructions.join(' ')).toContain('Configure Bedrock Agent');
    });
  });

  describe('error handling', () => {
    it('should handle service initialization errors', async () => {
      mockDirectAgentService.validateConfiguration.mockRejectedValue(
        new Error('Service unavailable')
      );

      const config = await service.detectConfiguration();

      expect(config.agentConnected).toBe(false);
      expect(config.configurationValid).toBe(false);
    });

    it('should throw error when accessing configuration before initialization', () => {
      expect(() => service.getConfiguration()).toThrow(
        'HybridModeService not initialized'
      );
    });
  });
});
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useHybridMode } from '../useHybridMode';
import { hybridModeService } from '../../services/hybridModeService';

// Mock the hybrid mode service
vi.mock('../../services/hybridModeService');

const mockHybridModeService = vi.mocked(hybridModeService);

describe('useHybridMode', () => {
  const mockConfig = {
    useMockAuth: true,
    useMockAgent: false,
    useDummyData: true,
    isHybridMode: true,
    agentConnected: true,
    configurationValid: true
  };

  const mockServiceSelection = {
    authService: 'mock' as const,
    agentService: 'direct' as const,
    dataService: 'mock' as const
  };

  const mockStatusIndicators = {
    mode: 'hybrid' as const,
    authStatus: 'mock' as const,
    agentStatus: 'connected' as const,
    agentType: 'direct' as const,
    configurationStatus: 'valid' as const,
    indicators: [
      {
        type: 'hybrid' as const,
        label: 'Hybrid Mode',
        color: 'blue' as const,
        description: 'Mock auth + Real agent'
      },
      {
        type: 'agent' as const,
        label: 'AI Ready',
        color: 'green' as const,
        description: 'Agent service: direct'
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    mockHybridModeService.initialize.mockResolvedValue(mockConfig);
    mockHybridModeService.onConfigurationChange.mockReturnValue(() => {});
    mockHybridModeService.getServiceSelection.mockReturnValue(mockServiceSelection);
    mockHybridModeService.getStatusIndicators.mockReturnValue(mockStatusIndicators);
    mockHybridModeService.getSetupInstructions.mockReturnValue(['Setup complete']);
    mockHybridModeService.getDiagnosticInfo.mockReturnValue({ test: 'data' });
    mockHybridModeService.testAgentConnectivity.mockResolvedValue({
      success: true,
      message: 'Test successful'
    });
    mockHybridModeService.refreshConfiguration.mockResolvedValue(mockConfig);
  });

  it('should initialize hybrid mode service on mount', async () => {
    const { result } = renderHook(() => useHybridMode());

    expect(result.current.isLoading).toBe(true);
    expect(mockHybridModeService.initialize).toHaveBeenCalled();

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.config).toEqual(mockConfig);
    expect(result.current.isHybridMode).toBe(true);
    expect(result.current.isAgentConnected).toBe(true);
    expect(result.current.isConfigurationValid).toBe(true);
  });

  it('should handle initialization errors', async () => {
    const error = new Error('Initialization failed');
    mockHybridModeService.initialize.mockRejectedValue(error);

    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Initialization failed');
    expect(result.current.config).toBeNull();
  });

  it('should subscribe to configuration changes', async () => {
    let configChangeCallback: (config: any) => void = () => {};
    
    mockHybridModeService.onConfigurationChange.mockImplementation((callback) => {
      configChangeCallback = callback;
      return () => {};
    });

    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Simulate configuration change
    const newConfig = { ...mockConfig, agentConnected: false };
    
    act(() => {
      configChangeCallback(newConfig);
    });

    expect(result.current.config).toEqual(newConfig);
    expect(result.current.isAgentConnected).toBe(false);
  });

  it('should provide correct service selection', async () => {
    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.serviceSelection).toEqual(mockServiceSelection);
  });

  it('should provide correct status indicators', async () => {
    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.statusIndicators).toEqual(mockStatusIndicators);
  });

  it('should refresh configuration', async () => {
    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.refreshConfiguration();
    });

    expect(mockHybridModeService.refreshConfiguration).toHaveBeenCalled();
  });

  it('should handle refresh configuration errors', async () => {
    const error = new Error('Refresh failed');
    mockHybridModeService.refreshConfiguration.mockRejectedValue(error);

    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.refreshConfiguration();
    });

    expect(result.current.error).toBe('Refresh failed');
  });

  it('should test connectivity', async () => {
    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const connectivityResult = await act(async () => {
      return await result.current.testConnectivity();
    });

    expect(connectivityResult.success).toBe(true);
    expect(connectivityResult.message).toBe('Test successful');
    expect(mockHybridModeService.testAgentConnectivity).toHaveBeenCalled();
  });

  it('should handle connectivity test errors', async () => {
    const error = new Error('Connectivity test failed');
    mockHybridModeService.testAgentConnectivity.mockRejectedValue(error);

    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const connectivityResult = await act(async () => {
      return await result.current.testConnectivity();
    });

    expect(connectivityResult.success).toBe(false);
    expect(connectivityResult.message).toBe('Connectivity test failed');
  });

  it('should get setup instructions', async () => {
    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const instructions = result.current.getSetupInstructions();

    expect(instructions).toEqual(['Setup complete']);
    expect(mockHybridModeService.getSetupInstructions).toHaveBeenCalled();
  });

  it('should get diagnostic info', async () => {
    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const diagnosticInfo = result.current.getDiagnosticInfo();

    expect(diagnosticInfo).toEqual({ test: 'data' });
    expect(mockHybridModeService.getDiagnosticInfo).toHaveBeenCalled();
  });

  it('should handle service method errors gracefully', async () => {
    mockHybridModeService.getSetupInstructions.mockImplementation(() => {
      throw new Error('Service error');
    });

    const { result } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const instructions = result.current.getSetupInstructions();

    expect(instructions).toEqual(['Error getting setup instructions. Please check configuration.']);
  });

  it('should provide default values when config is null', () => {
    mockHybridModeService.initialize.mockResolvedValue(mockConfig);
    mockHybridModeService.onConfigurationChange.mockReturnValue(() => {});

    const { result } = renderHook(() => useHybridMode());

    // Before initialization completes
    expect(result.current.isHybridMode).toBe(false);
    expect(result.current.isAgentConnected).toBe(false);
    expect(result.current.isConfigurationValid).toBe(false);
    expect(result.current.serviceSelection.authService).toBe('mock');
    expect(result.current.serviceSelection.agentService).toBe('mock');
    expect(result.current.serviceSelection.dataService).toBe('mock');
  });

  it('should cleanup subscription on unmount', async () => {
    const unsubscribe = jest.fn();
    mockHybridModeService.onConfigurationChange.mockReturnValue(unsubscribe);

    const { unmount } = renderHook(() => useHybridMode());

    await waitFor(() => {
      expect(mockHybridModeService.onConfigurationChange).toHaveBeenCalled();
    });

    unmount();

    expect(unsubscribe).toHaveBeenCalled();
  });
});
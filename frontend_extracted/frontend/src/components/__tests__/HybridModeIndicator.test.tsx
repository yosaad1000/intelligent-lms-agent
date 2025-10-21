import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import HybridModeIndicator from '../HybridModeIndicator';
import { useHybridMode } from '../../hooks/useHybridMode';

// Mock the useHybridMode hook
vi.mock('../../hooks/useHybridMode');

const mockUseHybridMode = vi.mocked(useHybridMode);

describe('HybridModeIndicator', () => {
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
      },
      {
        type: 'auth' as const,
        label: 'Mock Auth',
        color: 'yellow' as const,
        description: 'Development authentication'
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state', () => {
    mockUseHybridMode.mockReturnValue({
      statusIndicators: mockStatusIndicators,
      isLoading: true,
      config: null,
      error: null,
      isHybridMode: false,
      isAgentConnected: false,
      isConfigurationValid: false,
      serviceSelection: {
        authService: 'mock',
        agentService: 'mock',
        dataService: 'mock'
      },
      refreshConfiguration: vi.fn(),
      testConnectivity: vi.fn(),
      getSetupInstructions: vi.fn(),
      getDiagnosticInfo: vi.fn()
    });

    render(<HybridModeIndicator />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should render compact indicators by default', () => {
    mockUseHybridMode.mockReturnValue({
      statusIndicators: mockStatusIndicators,
      isLoading: false,
      config: null,
      error: null,
      isHybridMode: true,
      isAgentConnected: true,
      isConfigurationValid: true,
      serviceSelection: {
        authService: 'mock',
        agentService: 'direct',
        dataService: 'mock'
      },
      refreshConfiguration: vi.fn(),
      testConnectivity: vi.fn(),
      getSetupInstructions: vi.fn(),
      getDiagnosticInfo: vi.fn()
    });

    render(<HybridModeIndicator />);

    expect(screen.getByText('Hybrid Mode')).toBeInTheDocument();
    expect(screen.getByText('AI Ready')).toBeInTheDocument();
    expect(screen.getByText('Mock Auth')).toBeInTheDocument();

    // Should not show descriptions in compact mode
    expect(screen.queryByText('Mock auth + Real agent')).not.toBeInTheDocument();
  });

  it('should render detailed indicators when showDetails is true', () => {
    mockUseHybridMode.mockReturnValue({
      statusIndicators: mockStatusIndicators,
      isLoading: false,
      config: null,
      error: null,
      isHybridMode: true,
      isAgentConnected: true,
      isConfigurationValid: true,
      serviceSelection: {
        authService: 'mock',
        agentService: 'direct',
        dataService: 'mock'
      },
      refreshConfiguration: vi.fn(),
      testConnectivity: vi.fn(),
      getSetupInstructions: vi.fn(),
      getDiagnosticInfo: vi.fn()
    });

    render(<HybridModeIndicator showDetails={true} />);

    expect(screen.getByText('Hybrid Mode')).toBeInTheDocument();
    expect(screen.getByText('AI Ready')).toBeInTheDocument();
    expect(screen.getByText('Mock Auth')).toBeInTheDocument();

    // Should show descriptions in detailed mode
    expect(screen.getByText('(Mock auth + Real agent)')).toBeInTheDocument();
    expect(screen.getByText('(Agent service: direct)')).toBeInTheDocument();
    expect(screen.getByText('(Development authentication)')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    mockUseHybridMode.mockReturnValue({
      statusIndicators: mockStatusIndicators,
      isLoading: false,
      config: null,
      error: null,
      isHybridMode: true,
      isAgentConnected: true,
      isConfigurationValid: true,
      serviceSelection: {
        authService: 'mock',
        agentService: 'direct',
        dataService: 'mock'
      },
      refreshConfiguration: vi.fn(),
      testConnectivity: vi.fn(),
      getSetupInstructions: vi.fn(),
      getDiagnosticInfo: vi.fn()
    });

    const { container } = render(<HybridModeIndicator className="custom-class" />);

    expect(container.firstChild).toHaveClass('custom-class');
  });
});
/**
 * Agent Service Factory for Task 12: Frontend-Backend API Integration
 * Provides the appropriate agent service based on environment configuration
 */

import { ApiBedrockAgentService } from './apiBedrockAgentService';
import { BedrockAgentService, MockBedrockAgentService } from './bedrockAgentService';

// Determine which service to use based on environment
function createAgentService() {
  // Check if we should use mock service
  if (import.meta.env.VITE_USE_MOCK_AGENT === 'true') {
    console.log('🎭 Using Mock Bedrock Agent Service');
    return new MockBedrockAgentService();
  }
  
  // Check if we should use API proxy
  if (import.meta.env.VITE_USE_API_PROXY === 'true') {
    console.log('🌐 Using API Gateway Proxy Service');
    return ApiBedrockAgentService.getInstance();
  }
  
  // Default to direct AWS SDK service
  console.log('⚡ Using Direct AWS SDK Service');
  return BedrockAgentService.getInstance();
}

// Export the configured service
export const agentService = createAgentService();

// Export types for convenience
export type {
  AgentMessage,
  Citation,
  AgentResponse
} from './bedrockAgentService';

// Export additional types from API service
export type {
  UploadResponse,
  DocumentInfo
} from './apiBedrockAgentService';
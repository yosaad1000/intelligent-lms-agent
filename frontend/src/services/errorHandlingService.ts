// Error handling service for hybrid agent testing
export interface ErrorDetails {
  code: string;
  category: 'auth' | 'network' | 'validation' | 'processing' | 'configuration';
  message: string;
  userMessage: string;
  retryable: boolean;
  retryCount?: number;
  maxRetries?: number;
  timestamp: Date;
  context?: Record<string, any>;
  suggestions?: string[];
}

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableErrors: string[];
}

// Enhanced AgentError class
export class AgentError extends Error {
  public readonly details: ErrorDetails;

  constructor(
    message: string,
    code: string,
    category: ErrorDetails['category'],
    retryable: boolean = false,
    context?: Record<string, any>
  ) {
    super(message);
    this.name = 'AgentError';
    
    this.details = {
      code,
      category,
      message,
      userMessage: this.generateUserMessage(category, message),
      retryable,
      timestamp: new Date(),
      context,
      suggestions: this.generateSuggestions(category, code)
    };
  }

  private generateUserMessage(category: ErrorDetails['category'], message: string): string {
    switch (category) {
      case 'auth':
        return 'Authentication failed. Please check your AWS credentials and try again.';
      case 'network':
        return 'Network connection issue. Please check your internet connection and try again.';
      case 'validation':
        return 'Invalid input provided. Please check your request and try again.';
      case 'processing':
        return 'Processing failed. Please try again or contact support if the issue persists.';
      case 'configuration':
        return 'Configuration error. Please check your environment settings.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }

  private generateSuggestions(category: ErrorDetails['category'], code: string): string[] {
    const suggestions: string[] = [];

    switch (category) {
      case 'auth':
        suggestions.push(
          'Run "aws configure" to set up your credentials',
          'Check if your AWS credentials have expired',
          'Verify IAM permissions for Bedrock services'
        );
        break;
      case 'network':
        suggestions.push(
          'Check your internet connection',
          'Try again in a few moments',
          'Check if AWS services are experiencing issues'
        );
        break;
      case 'validation':
        suggestions.push(
          'Check the format of your input',
          'Ensure all required fields are provided',
          'Verify the input meets the expected criteria'
        );
        break;
      case 'processing':
        suggestions.push(
          'Try with different content or parameters',
          'Check if the agent is properly deployed',
          'Contact support if the issue persists'
        );
        break;
      case 'configuration':
        suggestions.push(
          'Check your environment variables',
          'Verify agent ID and alias ID are correct',
          'Ensure AWS region is properly set'
        );
        break;
    }

    return suggestions;
  }
}

class ErrorHandlingService {
  private errorLog: ErrorDetails[] = [];
  private maxLogSize = 100;
  
  private defaultRetryConfig: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000, // 1 second
    maxDelay: 10000, // 10 seconds
    backoffMultiplier: 2,
    retryableErrors: [
      'NETWORK_ERROR',
      'THROTTLING_ERROR',
      'SERVICE_UNAVAILABLE',
      'TIMEOUT_ERROR',
      'TEMPORARY_FAILURE'
    ]
  };

  /**
   * Process and categorize errors from various sources
   */
  processError(error: any, context?: Record<string, any>): AgentError {
    let agentError: AgentError;

    if (error instanceof AgentError) {
      // Already processed, just add context if provided
      if (context) {
        error.details.context = { ...error.details.context, ...context };
      }
      agentError = error;
    } else {
      // Process raw error
      agentError = this.categorizeError(error, context);
    }

    // Log the error
    this.logError(agentError.details);

    return agentError;
  }

  /**
   * Categorize raw errors into AgentError instances
   */
  private categorizeError(error: any, context?: Record<string, any>): AgentError {
    const errorName = error?.name || '';
    const errorMessage = error?.message || 'Unknown error';
    const errorCode = error?.code || error?.$metadata?.httpStatusCode || 'UNKNOWN';

    // AWS SDK errors
    if (this.isAwsError(error)) {
      return this.processAwsError(error, context);
    }

    // Network errors
    if (this.isNetworkError(error)) {
      return new AgentError(
        errorMessage,
        'NETWORK_ERROR',
        'network',
        true,
        context
      );
    }

    // Validation errors
    if (this.isValidationError(error)) {
      return new AgentError(
        errorMessage,
        'VALIDATION_ERROR',
        'validation',
        false,
        context
      );
    }

    // Configuration errors
    if (this.isConfigurationError(error)) {
      return new AgentError(
        errorMessage,
        'CONFIGURATION_ERROR',
        'configuration',
        false,
        context
      );
    }

    // Default processing error
    return new AgentError(
      errorMessage,
      errorCode.toString(),
      'processing',
      false,
      context
    );
  }

  /**
   * Process AWS-specific errors
   */
  private processAwsError(error: any, context?: Record<string, any>): AgentError {
    const errorName = error.name || '';
    const errorMessage = error.message || '';
    const errorCode = error.code || error.$metadata?.httpStatusCode || '';

    // Authentication errors
    if (this.isAuthError(error)) {
      let code = 'AUTH_ERROR';
      let message = errorMessage;

      if (errorName === 'CredentialsError') {
        code = 'CREDENTIALS_ERROR';
        message = 'AWS credentials are not configured or are invalid';
      } else if (errorName === 'UnauthorizedError' || errorName === 'AccessDeniedException') {
        code = 'ACCESS_DENIED';
        message = 'Access denied - check IAM permissions';
      } else if (errorName === 'SignatureDoesNotMatch') {
        code = 'INVALID_CREDENTIALS';
        message = 'AWS credentials are incorrect';
      } else if (errorName === 'TokenRefreshRequired') {
        code = 'EXPIRED_CREDENTIALS';
        message = 'AWS credentials have expired';
      }

      return new AgentError(message, code, 'auth', false, context);
    }

    // Resource errors
    if (errorName === 'ResourceNotFoundException') {
      return new AgentError(
        'Agent or resource not found - check agent ID and alias',
        'RESOURCE_NOT_FOUND',
        'configuration',
        false,
        context
      );
    }

    // Throttling errors
    if (errorName === 'ThrottlingException' || errorName === 'TooManyRequestsException') {
      return new AgentError(
        'Request throttled - too many requests',
        'THROTTLING_ERROR',
        'network',
        true,
        context
      );
    }

    // Service errors
    if (errorName === 'ServiceUnavailableException' || errorName === 'InternalServerError') {
      return new AgentError(
        'Service temporarily unavailable',
        'SERVICE_UNAVAILABLE',
        'network',
        true,
        context
      );
    }

    // Validation errors
    if (errorName === 'ValidationException') {
      return new AgentError(
        'Invalid request parameters',
        'VALIDATION_ERROR',
        'validation',
        false,
        context
      );
    }

    // Default AWS error
    return new AgentError(
      errorMessage,
      errorCode.toString(),
      'processing',
      false,
      context
    );
  }

  /**
   * Execute function with retry logic
   */
  async executeWithRetry<T>(
    operation: () => Promise<T>,
    operationName: string,
    customRetryConfig?: Partial<RetryConfig>
  ): Promise<T> {
    const config = { ...this.defaultRetryConfig, ...customRetryConfig };
    let lastError: AgentError | null = null;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        const result = await operation();
        
        // Log successful retry if this wasn't the first attempt
        if (attempt > 0) {
          console.log(`✅ ${operationName} succeeded after ${attempt} retries`);
        }
        
        return result;
      } catch (error) {
        const agentError = this.processError(error, { 
          operation: operationName, 
          attempt: attempt + 1,
          maxRetries: config.maxRetries
        });

        lastError = agentError;

        // Don't retry if error is not retryable
        if (!agentError.details.retryable || !config.retryableErrors.includes(agentError.details.code)) {
          console.error(`❌ ${operationName} failed (non-retryable):`, agentError.details.message);
          throw agentError;
        }

        // Don't retry if we've reached max attempts
        if (attempt >= config.maxRetries) {
          console.error(`❌ ${operationName} failed after ${config.maxRetries} retries:`, agentError.details.message);
          agentError.details.retryCount = attempt;
          agentError.details.maxRetries = config.maxRetries;
          throw agentError;
        }

        // Calculate delay for next retry
        const delay = Math.min(
          config.baseDelay * Math.pow(config.backoffMultiplier, attempt),
          config.maxDelay
        );

        console.warn(`⚠️ ${operationName} failed (attempt ${attempt + 1}/${config.maxRetries + 1}), retrying in ${delay}ms:`, agentError.details.message);

        // Wait before retrying
        await this.delay(delay);
      }
    }

    // This should never be reached, but just in case
    throw lastError || new AgentError('Unknown retry error', 'RETRY_ERROR', 'processing');
  }

  /**
   * Log error for debugging and analytics
   */
  private logError(errorDetails: ErrorDetails): void {
    // Add to in-memory log
    this.errorLog.unshift(errorDetails);
    
    // Keep log size manageable
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize);
    }

    // Console logging with appropriate level
    const logMessage = `[${errorDetails.category.toUpperCase()}] ${errorDetails.code}: ${errorDetails.message}`;
    
    if (errorDetails.retryable) {
      console.warn(logMessage, errorDetails.context);
    } else {
      console.error(logMessage, errorDetails.context);
    }

    // In production, you might want to send to external logging service
    if (import.meta.env.PROD && errorDetails.category === 'processing') {
      this.sendToExternalLogging(errorDetails);
    }
  }

  /**
   * Get recent errors for debugging
   */
  getRecentErrors(limit: number = 10): ErrorDetails[] {
    return this.errorLog.slice(0, limit);
  }

  /**
   * Get error statistics
   */
  getErrorStatistics(): {
    total: number;
    byCategory: Record<string, number>;
    byCode: Record<string, number>;
    retryableCount: number;
  } {
    const stats = {
      total: this.errorLog.length,
      byCategory: {} as Record<string, number>,
      byCode: {} as Record<string, number>,
      retryableCount: 0
    };

    this.errorLog.forEach(error => {
      // Count by category
      stats.byCategory[error.category] = (stats.byCategory[error.category] || 0) + 1;
      
      // Count by code
      stats.byCode[error.code] = (stats.byCode[error.code] || 0) + 1;
      
      // Count retryable errors
      if (error.retryable) {
        stats.retryableCount++;
      }
    });

    return stats;
  }

  /**
   * Clear error log
   */
  clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * Get user-friendly error message with suggestions
   */
  getErrorDisplayInfo(error: AgentError): {
    title: string;
    message: string;
    suggestions: string[];
    canRetry: boolean;
    severity: 'error' | 'warning' | 'info';
  } {
    return {
      title: this.getErrorTitle(error.details.category),
      message: error.details.userMessage,
      suggestions: error.details.suggestions || [],
      canRetry: error.details.retryable,
      severity: error.details.retryable ? 'warning' : 'error'
    };
  }

  private getErrorTitle(category: ErrorDetails['category']): string {
    switch (category) {
      case 'auth':
        return 'Authentication Error';
      case 'network':
        return 'Connection Error';
      case 'validation':
        return 'Input Error';
      case 'processing':
        return 'Processing Error';
      case 'configuration':
        return 'Configuration Error';
      default:
        return 'Error';
    }
  }

  // Helper methods for error detection
  private isAwsError(error: any): boolean {
    return error?.$metadata || error?.name?.includes('Exception') || error?.code;
  }

  private isAuthError(error: any): boolean {
    const authErrorNames = [
      'CredentialsError', 'UnauthorizedError', 'AccessDeniedException',
      'SignatureDoesNotMatch', 'InvalidAccessKeyId', 'TokenRefreshRequired'
    ];
    return authErrorNames.includes(error?.name);
  }

  private isNetworkError(error: any): boolean {
    const networkErrorNames = ['NetworkError', 'TimeoutError', 'ENOTFOUND', 'ECONNREFUSED'];
    return networkErrorNames.includes(error?.name) || 
           networkErrorNames.includes(error?.code) ||
           error?.message?.includes('network') ||
           error?.message?.includes('timeout');
  }

  private isValidationError(error: any): boolean {
    return error?.name === 'ValidationException' || 
           error?.message?.includes('validation') ||
           error?.message?.includes('invalid');
  }

  private isConfigurationError(error: any): boolean {
    return error?.message?.includes('configuration') ||
           error?.message?.includes('environment') ||
           error?.message?.includes('missing');
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private sendToExternalLogging(errorDetails: ErrorDetails): void {
    // Placeholder for external logging service integration
    // In production, you might send to services like:
    // - AWS CloudWatch Logs
    // - Sentry
    // - LogRocket
    // - Custom analytics endpoint
    console.log('Would send to external logging:', errorDetails);
  }
}

// Export singleton instance
export const errorHandlingService = new ErrorHandlingService();

// Export class for testing
export { ErrorHandlingService };
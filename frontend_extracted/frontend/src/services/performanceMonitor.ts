/**
 * Performance Monitor for Hybrid Mode Services
 * Tracks response times, connection pooling, and caching metrics
 */

export interface PerformanceMetrics {
  responseTime: number;
  timestamp: Date;
  operation: string;
  success: boolean;
  error?: string;
  metadata?: Record<string, any>;
}

export interface ConnectionPoolStats {
  activeConnections: number;
  totalConnections: number;
  queuedRequests: number;
  averageResponseTime: number;
  errorRate: number;
}

export interface CacheStats {
  hitRate: number;
  missRate: number;
  totalRequests: number;
  cacheSize: number;
  evictions: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = [];
  private maxMetrics = 1000; // Keep last 1000 metrics
  private connectionPool: Map<string, any> = new Map();
  private cache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();
  private cacheStats: CacheStats = {
    hitRate: 0,
    missRate: 0,
    totalRequests: 0,
    cacheSize: 0,
    evictions: 0
  };

  /**
   * Record a performance metric
   */
  recordMetric(metric: PerformanceMetrics): void {
    this.metrics.push(metric);
    
    // Keep only the most recent metrics
    if (this.metrics.length > this.maxMetrics) {
      this.metrics = this.metrics.slice(-this.maxMetrics);
    }
  }

  /**
   * Measure execution time of an async operation
   */
  async measureOperation<T>(
    operation: string,
    fn: () => Promise<T>,
    metadata?: Record<string, any>
  ): Promise<T> {
    const startTime = Date.now();
    let success = true;
    let error: string | undefined;

    try {
      const result = await fn();
      return result;
    } catch (err) {
      success = false;
      error = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      const responseTime = Date.now() - startTime;
      
      this.recordMetric({
        responseTime,
        timestamp: new Date(),
        operation,
        success,
        error,
        metadata
      });
    }
  }

  /**
   * Get performance statistics
   */
  getPerformanceStats(timeWindow?: number): {
    averageResponseTime: number;
    successRate: number;
    totalRequests: number;
    errorRate: number;
    operationStats: Record<string, {
      count: number;
      averageTime: number;
      successRate: number;
    }>;
  } {
    const cutoffTime = timeWindow ? Date.now() - timeWindow : 0;
    const relevantMetrics = this.metrics.filter(
      m => m.timestamp.getTime() > cutoffTime
    );

    if (relevantMetrics.length === 0) {
      return {
        averageResponseTime: 0,
        successRate: 0,
        totalRequests: 0,
        errorRate: 0,
        operationStats: {}
      };
    }

    const totalRequests = relevantMetrics.length;
    const successfulRequests = relevantMetrics.filter(m => m.success).length;
    const averageResponseTime = relevantMetrics.reduce(
      (sum, m) => sum + m.responseTime, 0
    ) / totalRequests;

    // Group by operation
    const operationStats: Record<string, {
      count: number;
      averageTime: number;
      successRate: number;
    }> = {};

    relevantMetrics.forEach(metric => {
      if (!operationStats[metric.operation]) {
        operationStats[metric.operation] = {
          count: 0,
          averageTime: 0,
          successRate: 0
        };
      }
      
      const stats = operationStats[metric.operation];
      stats.count++;
      stats.averageTime = (stats.averageTime * (stats.count - 1) + metric.responseTime) / stats.count;
    });

    // Calculate success rates
    Object.keys(operationStats).forEach(operation => {
      const operationMetrics = relevantMetrics.filter(m => m.operation === operation);
      const successfulOps = operationMetrics.filter(m => m.success).length;
      operationStats[operation].successRate = successfulOps / operationMetrics.length;
    });

    return {
      averageResponseTime,
      successRate: successfulRequests / totalRequests,
      totalRequests,
      errorRate: (totalRequests - successfulRequests) / totalRequests,
      operationStats
    };
  }

  /**
   * Connection pooling for AWS SDK clients
   */
  getConnection(key: string, factory: () => any): any {
    if (!this.connectionPool.has(key)) {
      const connection = factory();
      this.connectionPool.set(key, {
        client: connection,
        createdAt: Date.now(),
        lastUsed: Date.now(),
        useCount: 0
      });
    }

    const poolEntry = this.connectionPool.get(key)!;
    poolEntry.lastUsed = Date.now();
    poolEntry.useCount++;

    return poolEntry.client;
  }

  /**
   * Clean up old connections
   */
  cleanupConnections(maxAge: number = 30 * 60 * 1000): void {
    const now = Date.now();
    
    for (const [key, entry] of this.connectionPool.entries()) {
      if (now - entry.lastUsed > maxAge) {
        this.connectionPool.delete(key);
      }
    }
  }

  /**
   * Get connection pool statistics
   */
  getConnectionPoolStats(): ConnectionPoolStats {
    const stats = this.getPerformanceStats(5 * 60 * 1000); // Last 5 minutes
    
    return {
      activeConnections: this.connectionPool.size,
      totalConnections: this.connectionPool.size,
      queuedRequests: 0, // Would need to track this separately
      averageResponseTime: stats.averageResponseTime,
      errorRate: stats.errorRate
    };
  }

  /**
   * Cache management with TTL
   */
  setCache(key: string, data: any, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });

    this.cacheStats.cacheSize = this.cache.size;
  }

  /**
   * Get from cache
   */
  getCache(key: string): any | null {
    this.cacheStats.totalRequests++;

    const entry = this.cache.get(key);
    
    if (!entry) {
      this.cacheStats.missRate = (this.cacheStats.missRate * (this.cacheStats.totalRequests - 1) + 1) / this.cacheStats.totalRequests;
      return null;
    }

    // Check if expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      this.cacheStats.evictions++;
      this.cacheStats.cacheSize = this.cache.size;
      this.cacheStats.missRate = (this.cacheStats.missRate * (this.cacheStats.totalRequests - 1) + 1) / this.cacheStats.totalRequests;
      return null;
    }

    this.cacheStats.hitRate = (this.cacheStats.hitRate * (this.cacheStats.totalRequests - 1) + 1) / this.cacheStats.totalRequests;
    return entry.data;
  }

  /**
   * Clear expired cache entries
   */
  cleanupCache(): void {
    const now = Date.now();
    let evicted = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
        evicted++;
      }
    }

    this.cacheStats.evictions += evicted;
    this.cacheStats.cacheSize = this.cache.size;
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): CacheStats {
    return { ...this.cacheStats };
  }

  /**
   * Clear all metrics and caches
   */
  reset(): void {
    this.metrics = [];
    this.connectionPool.clear();
    this.cache.clear();
    this.cacheStats = {
      hitRate: 0,
      missRate: 0,
      totalRequests: 0,
      cacheSize: 0,
      evictions: 0
    };
  }

  /**
   * Get performance recommendations
   */
  getRecommendations(): string[] {
    const stats = this.getPerformanceStats(10 * 60 * 1000); // Last 10 minutes
    const recommendations: string[] = [];

    if (stats.averageResponseTime > 5000) {
      recommendations.push('Average response time is high (>5s). Consider optimizing agent queries or checking network connectivity.');
    }

    if (stats.errorRate > 0.1) {
      recommendations.push('Error rate is high (>10%). Check agent configuration and AWS credentials.');
    }

    if (this.cacheStats.hitRate < 0.3 && this.cacheStats.totalRequests > 10) {
      recommendations.push('Cache hit rate is low (<30%). Consider increasing cache TTL or reviewing caching strategy.');
    }

    if (this.connectionPool.size > 10) {
      recommendations.push('High number of active connections. Consider connection cleanup or pooling optimization.');
    }

    if (recommendations.length === 0) {
      recommendations.push('Performance looks good! No immediate optimizations needed.');
    }

    return recommendations;
  }

  /**
   * Export metrics for analysis
   */
  exportMetrics(): {
    metrics: PerformanceMetrics[];
    stats: ReturnType<typeof this.getPerformanceStats>;
    connectionPool: ConnectionPoolStats;
    cache: CacheStats;
    recommendations: string[];
  } {
    return {
      metrics: [...this.metrics],
      stats: this.getPerformanceStats(),
      connectionPool: this.getConnectionPoolStats(),
      cache: this.getCacheStats(),
      recommendations: this.getRecommendations()
    };
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Auto-cleanup every 5 minutes
setInterval(() => {
  performanceMonitor.cleanupConnections();
  performanceMonitor.cleanupCache();
}, 5 * 60 * 1000);

export { PerformanceMonitor };
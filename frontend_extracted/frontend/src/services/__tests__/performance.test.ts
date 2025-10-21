import { describe, it, expect, beforeEach, vi } from 'vitest';
import { performanceMonitor, PerformanceMonitor } from '../performanceMonitor';

describe('Performance Monitoring', () => {
  let monitor: PerformanceMonitor;

  beforeEach(() => {
    monitor = new PerformanceMonitor();
  });

  describe('Performance Metrics', () => {
    it('should record performance metrics', () => {
      const metric = {
        responseTime: 1500,
        timestamp: new Date(),
        operation: 'sendMessage',
        success: true,
        metadata: { messageLength: 100 }
      };

      monitor.recordMetric(metric);
      
      const stats = monitor.getPerformanceStats();
      expect(stats.totalRequests).toBe(1);
      expect(stats.averageResponseTime).toBe(1500);
      expect(stats.successRate).toBe(1);
    });

    it('should calculate correct statistics', () => {
      const metrics = [
        {
          responseTime: 1000,
          timestamp: new Date(),
          operation: 'sendMessage',
          success: true
        },
        {
          responseTime: 2000,
          timestamp: new Date(),
          operation: 'sendMessage',
          success: true
        },
        {
          responseTime: 3000,
          timestamp: new Date(),
          operation: 'sendMessage',
          success: false
        }
      ];

      metrics.forEach(metric => monitor.recordMetric(metric));
      
      const stats = monitor.getPerformanceStats();
      expect(stats.totalRequests).toBe(3);
      expect(stats.averageResponseTime).toBe(2000);
      expect(stats.successRate).toBeCloseTo(0.667, 2);
      expect(stats.errorRate).toBeCloseTo(0.333, 2);
    });

    it('should group statistics by operation', () => {
      const metrics = [
        {
          responseTime: 1000,
          timestamp: new Date(),
          operation: 'sendMessage',
          success: true
        },
        {
          responseTime: 2000,
          timestamp: new Date(),
          operation: 'analyzeDocument',
          success: true
        },
        {
          responseTime: 1500,
          timestamp: new Date(),
          operation: 'sendMessage',
          success: false
        }
      ];

      metrics.forEach(metric => monitor.recordMetric(metric));
      
      const stats = monitor.getPerformanceStats();
      
      expect(stats.operationStats['sendMessage']).toBeDefined();
      expect(stats.operationStats['analyzeDocument']).toBeDefined();
      expect(stats.operationStats['sendMessage'].count).toBe(2);
      expect(stats.operationStats['analyzeDocument'].count).toBe(1);
      expect(stats.operationStats['sendMessage'].averageTime).toBe(1250);
      expect(stats.operationStats['sendMessage'].successRate).toBe(0.5);
    });

    it('should filter metrics by time window', () => {
      const now = Date.now();
      const oldMetric = {
        responseTime: 1000,
        timestamp: new Date(now - 20 * 60 * 1000), // 20 minutes ago
        operation: 'sendMessage',
        success: true
      };
      const recentMetric = {
        responseTime: 2000,
        timestamp: new Date(now - 5 * 60 * 1000), // 5 minutes ago
        operation: 'sendMessage',
        success: true
      };

      monitor.recordMetric(oldMetric);
      monitor.recordMetric(recentMetric);
      
      const stats = monitor.getPerformanceStats(10 * 60 * 1000); // Last 10 minutes
      expect(stats.totalRequests).toBe(1);
      expect(stats.averageResponseTime).toBe(2000);
    });
  });

  describe('Operation Measurement', () => {
    it('should measure async operation performance', async () => {
      const mockOperation = vi.fn().mockResolvedValue('success');
      
      const result = await monitor.measureOperation('testOp', mockOperation);
      
      expect(result).toBe('success');
      expect(mockOperation).toHaveBeenCalled();
      
      const stats = monitor.getPerformanceStats();
      expect(stats.totalRequests).toBe(1);
      expect(stats.operationStats['testOp']).toBeDefined();
      expect(stats.operationStats['testOp'].successRate).toBe(1);
    });

    it('should handle operation failures', async () => {
      const mockOperation = vi.fn().mockRejectedValue(new Error('Test error'));
      
      await expect(
        monitor.measureOperation('testOp', mockOperation)
      ).rejects.toThrow('Test error');
      
      const stats = monitor.getPerformanceStats();
      expect(stats.totalRequests).toBe(1);
      expect(stats.successRate).toBe(0);
      expect(stats.errorRate).toBe(1);
    });

    it('should include metadata in metrics', async () => {
      const mockOperation = vi.fn().mockResolvedValue('success');
      const metadata = { userId: 'test-user', messageLength: 100 };
      
      await monitor.measureOperation('testOp', mockOperation, metadata);
      
      const exportedData = monitor.exportMetrics();
      expect(exportedData.metrics[0].metadata).toEqual(metadata);
    });
  });

  describe('Connection Pooling', () => {
    it('should create and reuse connections', () => {
      const factory = vi.fn(() => ({ id: 'connection-1' }));
      
      const conn1 = monitor.getConnection('test-key', factory);
      const conn2 = monitor.getConnection('test-key', factory);
      
      expect(factory).toHaveBeenCalledTimes(1);
      expect(conn1).toBe(conn2);
    });

    it('should create separate connections for different keys', () => {
      const factory1 = vi.fn(() => ({ id: 'connection-1' }));
      const factory2 = vi.fn(() => ({ id: 'connection-2' }));
      
      const conn1 = monitor.getConnection('key1', factory1);
      const conn2 = monitor.getConnection('key2', factory2);
      
      expect(factory1).toHaveBeenCalledTimes(1);
      expect(factory2).toHaveBeenCalledTimes(1);
      expect(conn1).not.toBe(conn2);
    });

    it('should cleanup old connections', () => {
      const factory = vi.fn(() => ({ id: 'connection' }));
      
      monitor.getConnection('test-key', factory);
      
      // Simulate old connection
      const poolStats = monitor.getConnectionPoolStats();
      expect(poolStats.activeConnections).toBe(1);
      
      monitor.cleanupConnections(0); // Cleanup immediately
      
      const newPoolStats = monitor.getConnectionPoolStats();
      expect(newPoolStats.activeConnections).toBe(0);
    });
  });

  describe('Caching', () => {
    it('should cache and retrieve data', () => {
      const testData = { message: 'test response' };
      
      monitor.setCache('test-key', testData, 5000);
      const retrieved = monitor.getCache('test-key');
      
      expect(retrieved).toEqual(testData);
      
      const cacheStats = monitor.getCacheStats();
      expect(cacheStats.totalRequests).toBe(1);
      expect(cacheStats.hitRate).toBe(1);
    });

    it('should return null for cache miss', () => {
      const result = monitor.getCache('non-existent-key');
      
      expect(result).toBeNull();
      
      const cacheStats = monitor.getCacheStats();
      expect(cacheStats.totalRequests).toBe(1);
      expect(cacheStats.missRate).toBe(1);
    });

    it('should expire cached data based on TTL', () => {
      const testData = { message: 'test response' };
      
      monitor.setCache('test-key', testData, 100); // 100ms TTL
      
      // Should be available immediately
      expect(monitor.getCache('test-key')).toEqual(testData);
      
      // Wait for expiration
      return new Promise(resolve => {
        setTimeout(() => {
          expect(monitor.getCache('test-key')).toBeNull();
          resolve(undefined);
        }, 150);
      });
    });

    it('should cleanup expired cache entries', () => {
      monitor.setCache('key1', 'data1', 100);
      monitor.setCache('key2', 'data2', 5000);
      
      expect(monitor.getCacheStats().cacheSize).toBe(2);
      
      return new Promise(resolve => {
        setTimeout(() => {
          monitor.cleanupCache();
          const stats = monitor.getCacheStats();
          expect(stats.cacheSize).toBe(1);
          expect(stats.evictions).toBe(1);
          resolve(undefined);
        }, 150);
      });
    });
  });

  describe('Performance Recommendations', () => {
    it('should provide recommendations for high response times', () => {
      // Add metrics with high response times
      for (let i = 0; i < 5; i++) {
        monitor.recordMetric({
          responseTime: 6000, // 6 seconds
          timestamp: new Date(),
          operation: 'sendMessage',
          success: true
        });
      }
      
      const recommendations = monitor.getRecommendations();
      expect(recommendations.some(r => r.includes('response time is high'))).toBe(true);
    });

    it('should provide recommendations for high error rates', () => {
      // Add metrics with high error rate
      for (let i = 0; i < 10; i++) {
        monitor.recordMetric({
          responseTime: 1000,
          timestamp: new Date(),
          operation: 'sendMessage',
          success: i < 5 // 50% error rate
        });
      }
      
      const recommendations = monitor.getRecommendations();
      expect(recommendations.some(r => r.includes('Error rate is high'))).toBe(true);
    });

    it('should provide recommendations for low cache hit rate', () => {
      // Simulate low cache hit rate
      for (let i = 0; i < 20; i++) {
        monitor.getCache(`key-${i}`); // All misses
      }
      
      const recommendations = monitor.getRecommendations();
      expect(recommendations.some(r => r.includes('Cache hit rate is low'))).toBe(true);
    });

    it('should provide positive feedback for good performance', () => {
      // Add metrics with good performance
      for (let i = 0; i < 5; i++) {
        monitor.recordMetric({
          responseTime: 500, // Fast response
          timestamp: new Date(),
          operation: 'sendMessage',
          success: true
        });
      }
      
      // Good cache performance
      monitor.setCache('test', 'data', 5000);
      monitor.getCache('test'); // Hit
      
      const recommendations = monitor.getRecommendations();
      expect(recommendations.some(r => r.includes('Performance looks good'))).toBe(true);
    });
  });

  describe('Data Export', () => {
    it('should export comprehensive performance data', () => {
      // Add some test data
      monitor.recordMetric({
        responseTime: 1500,
        timestamp: new Date(),
        operation: 'sendMessage',
        success: true
      });
      
      monitor.setCache('test-key', 'test-data', 5000);
      monitor.getCache('test-key');
      
      const factory = vi.fn(() => ({ id: 'connection' }));
      monitor.getConnection('test-conn', factory);
      
      const exportedData = monitor.exportMetrics();
      
      expect(exportedData.metrics).toHaveLength(1);
      expect(exportedData.stats.totalRequests).toBe(1);
      expect(exportedData.connectionPool.activeConnections).toBe(1);
      expect(exportedData.cache.totalRequests).toBe(1);
      expect(exportedData.recommendations).toBeInstanceOf(Array);
    });
  });

  describe('Performance Targets Validation', () => {
    it('should validate response time targets', () => {
      const targetResponseTime = 3000; // 3 seconds
      
      // Add metrics within target
      monitor.recordMetric({
        responseTime: 2000,
        timestamp: new Date(),
        operation: 'sendMessage',
        success: true
      });
      
      const stats = monitor.getPerformanceStats();
      expect(stats.averageResponseTime).toBeLessThan(targetResponseTime);
    });

    it('should validate success rate targets', () => {
      const targetSuccessRate = 0.95; // 95%
      
      // Add metrics with good success rate
      for (let i = 0; i < 20; i++) {
        monitor.recordMetric({
          responseTime: 1000,
          timestamp: new Date(),
          operation: 'sendMessage',
          success: i < 19 // 95% success rate
        });
      }
      
      const stats = monitor.getPerformanceStats();
      expect(stats.successRate).toBeGreaterThanOrEqual(targetSuccessRate);
    });

    it('should validate cache performance targets', () => {
      const targetHitRate = 0.3; // 30%
      
      // Simulate cache usage
      monitor.setCache('key1', 'data1', 5000);
      monitor.setCache('key2', 'data2', 5000);
      
      // 3 hits, 2 misses = 60% hit rate
      monitor.getCache('key1'); // hit
      monitor.getCache('key2'); // hit
      monitor.getCache('key1'); // hit
      monitor.getCache('key3'); // miss
      monitor.getCache('key4'); // miss
      
      const cacheStats = monitor.getCacheStats();
      expect(cacheStats.hitRate).toBeGreaterThan(targetHitRate);
    });
  });
});
"""
Performance optimization utilities for the MCP Tool Router system.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from functools import wraps
import logging

class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def track_time(self, operation_name: str):
        """Decorator to track execution time of operations"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000
                    self._record_metric(operation_name, execution_time)
                    return result
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    self._record_metric(f"{operation_name}_error", execution_time)
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000
                    self._record_metric(operation_name, execution_time)
                    return result
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    self._record_metric(f"{operation_name}_error", execution_time)
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _record_metric(self, operation_name: str, execution_time: float):
        """Record a performance metric"""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        self.metrics[operation_name].append(execution_time)
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics"""
        stats = {}
        for operation, times in self.metrics.items():
            if times:
                stats[operation] = {
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'count': len(times),
                    'total': sum(times)
                }
        return stats
    
    def log_stats(self):
        """Log performance statistics"""
        stats = self.get_stats()
        logging.info("=== Performance Statistics ===")
        for operation, metrics in stats.items():
            logging.info(f"{operation}: avg={metrics['avg']:.2f}ms, "
                        f"min={metrics['min']:.2f}ms, max={metrics['max']:.2f}ms, "
                        f"count={metrics['count']}")

class ConcurrencyManager:
    """Manage concurrent operations with rate limiting"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_with_limit(self, coroutine):
        """Execute a coroutine with concurrency limiting"""
        async with self.semaphore:
            return await coroutine

class BatchProcessor:
    """Process items in batches for better performance"""
    
    @staticmethod
    async def process_in_batches(items: List[Any], 
                               processor_func, 
                               batch_size: int = 10,
                               max_concurrent: int = 5) -> List[Any]:
        """
        Process items in concurrent batches
        
        Args:
            items: List of items to process
            processor_func: Async function to process each item
            batch_size: Size of each batch
            max_concurrent: Maximum concurrent batches
            
        Returns:
            List of processed results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_batch(batch):
            async with semaphore:
                return await asyncio.gather(*[processor_func(item) for item in batch])
        
        # Split items into batches
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        # Process batches concurrently
        batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)
        
        return results

class MemoryOptimizer:
    """Utilities for memory optimization"""
    
    @staticmethod
    def chunked_processing(items: List[Any], chunk_size: int = 100):
        """Generator to process large lists in chunks"""
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]
    
    @staticmethod
    def clear_cache_if_needed(cache: Dict, max_size: int = 1000):
        """Clear cache if it exceeds max size"""
        if len(cache) > max_size:
            # Clear oldest 50% of cache entries
            items_to_remove = len(cache) // 2
            keys_to_remove = list(cache.keys())[:items_to_remove]
            for key in keys_to_remove:
                del cache[key]

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

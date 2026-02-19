"""Utility layers for CloudGuard AI - Caching and optimization"""
import time
import json
import hashlib
import logging
from typing import Any, Callable, Optional, Dict
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires_at']:
                return entry['value']
            else:
                # Expired, remove it
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        self.cache[key] = {
            'value': value,
            'expires_at': datetime.now() + timedelta(seconds=ttl_seconds),
            'created_at': datetime.now()
        }
    
    def invalidate(self, key: str):
        """Remove specific key from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = sum(
            1 for entry in self.cache.values()
            if datetime.now() >= entry['expires_at']
        )
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries
        }


# Global cache instance
_cache = InMemoryCache()


def get_cache() -> InMemoryCache:
    """Get global cache instance"""
    return _cache


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator to cache function results with TTL.
    
    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Optional prefix for cache keys
    
    Example:
        @cached(ttl=600, key_prefix="rules")
        def get_rules():
            return expensive_operation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    # Hash complex objects
                    arg_str = str(arg)
                    arg_hash = hashlib.md5(arg_str.encode()).hexdigest()[:8]
                    key_parts.append(arg_hash)
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")
                else:
                    v_str = str(v)
                    v_hash = hashlib.md5(v_str.encode()).hexdigest()[:8]
                    key_parts.append(f"{k}={v_hash}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl_seconds=ttl)
            
            return result
        
        return wrapper
    return decorator


class FileCache:
    """File-based cache for larger objects"""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str, max_age_seconds: Optional[int] = None) -> Optional[Any]:
        """Get value from file cache"""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        # Check age if specified
        if max_age_seconds:
            file_age = time.time() - cache_path.stat().st_mtime
            if file_age > max_age_seconds:
                cache_path.unlink()  # Delete expired cache
                return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                return data['value']
        except Exception:
            return None
    
    def set(self, key: str, value: Any):
        """Set value in file cache"""
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'value': value,
                    'created_at': datetime.now().isoformat(),
                    'key': key
                }, f)
        except Exception:
            pass  # Fail silently
    
    def invalidate(self, key: str):
        """Remove specific key from cache"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
    
    def clear(self):
        """Clear all file cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


def timed(operation_name: Optional[str] = None):
    """
    Decorator to time function execution.
    
    Args:
        operation_name: Optional name for the operation
    
    Example:
        @timed("expensive_calculation")
        def calculate():
            return sum(range(1000000))
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                
                logger.debug("%s completed in %.2fms", name, elapsed_ms)
                
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.warning("%s failed after %.2fms: %s", name, elapsed_ms, str(e))
                raise
        
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay_seconds: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries
        backoff: Backoff multiplier for delay
    
    Example:
        @retry(max_attempts=3, delay_seconds=1, backoff=2)
        def unreliable_api_call():
            return requests.get("https://api.example.com")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay_seconds
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning("Attempt %d/%d failed: %s", attempt, max_attempts, str(e))
                        logger.info("Retrying in %.1fs...", current_delay)
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error("All %d attempts failed", max_attempts)
            
            raise last_exception
        
        return wrapper
    return decorator


def memoize_to_file(file_path: str):
    """
    Decorator to memoize function results to a file.
    Useful for expensive computations that rarely change.
    
    Args:
        file_path: Path to store memoized results
    
    Example:
        @memoize_to_file("cache/feature_names.json")
        def get_feature_names():
            return expensive_feature_extraction()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_path = Path(file_path)
            
            # Try to load from cache
            if cache_path.exists():
                try:
                    with open(cache_path, 'r') as f:
                        return json.load(f)
                except Exception:
                    pass  # If cache read fails, recompute
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Save to cache
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(cache_path, 'w') as f:
                    json.dump(result, f)
            except Exception:
                pass  # Fail silently if cache write fails
            
            return result
        
        return wrapper
    return decorator

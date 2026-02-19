"""Unit tests for caching utilities"""
import pytest
import time
from pathlib import Path
from unittest.mock import Mock

# Add api to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "api"))


def test_in_memory_cache_set_get():
    """Test basic cache set and get operations"""
    from app.utils import InMemoryCache
    
    cache = InMemoryCache()
    cache.set("test_key", "test_value", ttl_seconds=60)
    
    value = cache.get("test_key")
    assert value == "test_value"


def test_in_memory_cache_expiration():
    """Test that cache entries expire after TTL"""
    from app.utils import InMemoryCache
    
    cache = InMemoryCache()
    cache.set("test_key", "test_value", ttl_seconds=1)
    
    # Should exist immediately
    assert cache.get("test_key") == "test_value"
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Should be None after expiration
    assert cache.get("test_key") is None


def test_in_memory_cache_invalidate():
    """Test cache invalidation"""
    from app.utils import InMemoryCache
    
    cache = InMemoryCache()
    cache.set("test_key", "test_value", ttl_seconds=60)
    
    assert cache.get("test_key") == "test_value"
    
    cache.invalidate("test_key")
    
    assert cache.get("test_key") is None


def test_in_memory_cache_clear():
    """Test clearing all cache entries"""
    from app.utils import InMemoryCache
    
    cache = InMemoryCache()
    cache.set("key1", "value1", ttl_seconds=60)
    cache.set("key2", "value2", ttl_seconds=60)
    
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    
    cache.clear()
    
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_in_memory_cache_stats():
    """Test cache statistics"""
    from app.utils import InMemoryCache
    
    cache = InMemoryCache()
    cache.set("key1", "value1", ttl_seconds=60)
    cache.set("key2", "value2", ttl_seconds=1)
    
    stats = cache.stats()
    assert stats["total_entries"] == 2
    
    # Wait for one to expire
    time.sleep(1.1)
    
    stats = cache.stats()
    assert stats["expired_entries"] == 1
    assert stats["active_entries"] == 1


def test_cached_decorator_basic():
    """Test @cached decorator caches function results"""
    from app.utils import cached, get_cache
    
    call_count = {"count": 0}
    
    @cached(ttl=60, key_prefix="test")
    def expensive_function(x):
        call_count["count"] += 1
        return x * 2
    
    # Clear cache before test
    get_cache().clear()
    
    # First call should execute function
    result1 = expensive_function(5)
    assert result1 == 10
    assert call_count["count"] == 1
    
    # Second call should use cache
    result2 = expensive_function(5)
    assert result2 == 10
    assert call_count["count"] == 1  # Not incremented


def test_cached_decorator_different_args():
    """Test @cached decorator with different arguments"""
    from app.utils import cached, get_cache
    
    call_count = {"count": 0}
    
    @cached(ttl=60, key_prefix="test")
    def expensive_function(x):
        call_count["count"] += 1
        return x * 2
    
    get_cache().clear()
    
    result1 = expensive_function(5)
    assert result1 == 10
    assert call_count["count"] == 1
    
    # Different argument should not use cache
    result2 = expensive_function(10)
    assert result2 == 20
    assert call_count["count"] == 2


def test_cached_decorator_with_kwargs():
    """Test @cached decorator with keyword arguments"""
    from app.utils import cached, get_cache
    
    call_count = {"count": 0}
    
    @cached(ttl=60)
    def func(x, y=5):
        call_count["count"] += 1
        return x + y
    
    get_cache().clear()
    
    result1 = func(10, y=5)
    assert result1 == 15
    assert call_count["count"] == 1
    
    result2 = func(10, y=5)
    assert result2 == 15
    assert call_count["count"] == 1  # Cached


def test_file_cache_set_get(tmp_path):
    """Test FileCache set and get operations"""
    from app.utils import FileCache
    
    cache_dir = tmp_path / "cache"
    cache = FileCache(cache_dir=str(cache_dir))
    
    cache.set("test_key", {"data": "test_value"})
    value = cache.get("test_key")
    
    assert value == {"data": "test_value"}


def test_file_cache_max_age(tmp_path):
    """Test FileCache respects max age"""
    from app.utils import FileCache
    
    cache_dir = tmp_path / "cache"
    cache = FileCache(cache_dir=str(cache_dir))
    
    cache.set("test_key", "test_value")
    
    # Should exist with no max age
    assert cache.get("test_key") is not None
    
    # Should be None with very short max age after waiting
    time.sleep(0.3)
    assert cache.get("test_key", max_age_seconds=0.2) is None


def test_file_cache_invalidate(tmp_path):
    """Test FileCache invalidation"""
    from app.utils import FileCache
    
    cache_dir = tmp_path / "cache"
    cache = FileCache(cache_dir=str(cache_dir))
    
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"
    
    cache.invalidate("test_key")
    assert cache.get("test_key") is None


def test_file_cache_clear(tmp_path):
    """Test FileCache clear all entries"""
    from app.utils import FileCache
    
    cache_dir = tmp_path / "cache"
    cache = FileCache(cache_dir=str(cache_dir))
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    
    cache.clear()
    
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_timed_decorator():
    """Test @timed decorator logs execution time"""
    from app.utils import timed
    import io
    import logging
    
    @timed("test_operation")
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    # Capture logging output from app.utils logger
    log_stream = io.StringIO()
    utils_logger = logging.getLogger("app.utils")
    utils_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    utils_logger.addHandler(handler)
    
    result = slow_function()
    
    utils_logger.removeHandler(handler)
    output = log_stream.getvalue()
    
    assert result == "done"
    assert "test_operation" in output
    assert "completed in" in output
    assert "ms" in output


def test_retry_decorator_success():
    """Test @retry decorator on successful function"""
    from app.utils import retry
    
    call_count = {"count": 0}
    
    @retry(max_attempts=3, delay_seconds=0.1)
    def successful_function():
        call_count["count"] += 1
        return "success"
    
    result = successful_function()
    
    assert result == "success"
    assert call_count["count"] == 1


def test_retry_decorator_eventual_success():
    """Test @retry decorator retries until success"""
    from app.utils import retry
    
    call_count = {"count": 0}
    
    @retry(max_attempts=3, delay_seconds=0.1, backoff=1.0)
    def flaky_function():
        call_count["count"] += 1
        if call_count["count"] < 3:
            raise ValueError("Temporary error")
        return "success"
    
    result = flaky_function()
    
    assert result == "success"
    assert call_count["count"] == 3


def test_retry_decorator_max_attempts():
    """Test @retry decorator exhausts max attempts"""
    from app.utils import retry
    
    call_count = {"count": 0}
    
    @retry(max_attempts=3, delay_seconds=0.1)
    def failing_function():
        call_count["count"] += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        failing_function()
    
    assert call_count["count"] == 3


def test_memoize_to_file_decorator(tmp_path):
    """Test @memoize_to_file decorator"""
    from app.utils import memoize_to_file
    
    cache_file = tmp_path / "memo.json"
    call_count = {"count": 0}
    
    @memoize_to_file(str(cache_file))
    def expensive_computation():
        call_count["count"] += 1
        return {"result": 42}
    
    # First call should execute
    result1 = expensive_computation()
    assert result1 == {"result": 42}
    assert call_count["count"] == 1
    assert cache_file.exists()
    
    # Second call should use cached file
    result2 = expensive_computation()
    assert result2 == {"result": 42}
    assert call_count["count"] == 1  # Not incremented

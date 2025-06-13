"""
Redis-based caching layer for improved performance.

This module provides:
- Query result caching
- Schema information caching
- Session management
- Rate limiting
- Distributed locking
"""

import logging
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError
import asyncio
from functools import wraps
import redis.asyncio as redis
from core.config import get_settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service with comprehensive features.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        self._connect()
        
        # Cache configuration
        self.default_ttl = 3600  # 1 hour
        self.query_cache_ttl = 1800  # 30 minutes
        self.schema_cache_ttl = 3600 * 24  # 24 hours
        self.session_ttl = 3600 * 24 * 7  # 7 days
        
        # Key prefixes
        self.QUERY_PREFIX = "query:"
        self.SCHEMA_PREFIX = "schema:"
        self.SESSION_PREFIX = "session:"
        self.RATE_LIMIT_PREFIX = "rate_limit:"
        self.LOCK_PREFIX = "lock:"
        self.USER_PREFIX = "user:"
        self.ANALYTICS_PREFIX = "analytics:"
    
    def _connect(self):
        """Connect to Redis with fallback to in-memory cache."""
        try:
            if self.settings.redis_enabled:
                self.redis_client = redis.Redis(
                    host=self.settings.redis_host,
                    port=self.settings.redis_port,
                    password=self.settings.redis_password,
                    db=self.settings.redis_db,
                    decode_responses=False,  # We'll handle encoding ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test connection (will be tested later in async context)
                logger.info("Redis client initialized")
            else:
                logger.info("Redis disabled, using in-memory cache fallback")
                self._init_memory_cache()
                
        except (RedisError, Exception) as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}, falling back to memory cache")
            self._init_memory_cache()
    
    def _init_memory_cache(self):
        """Initialize in-memory cache as fallback."""
        self.redis_client = None
        self._memory_cache = {}
        self._memory_cache_ttl = {}
    
    def _is_redis_available(self) -> bool:
        """Check if Redis is available."""
        if not self.redis_client:
            return False
        
        try:
            # For sync check, just return if client exists
            # Actual ping should be done in async context
            return True
        except:
            return False
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first (for simple types)
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle for complex types
            return pickle.loads(value)
    
    def _make_key(self, prefix: str, *args: str) -> str:
        """Create a cache key with prefix."""
        key_parts = [prefix] + list(args)
        return ":".join(str(part) for part in key_parts)
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            ttl = ttl or self.default_ttl
            
            if self._is_redis_available():
                serialized_value = self._serialize_value(value)
                result = self.redis_client.setex(key, ttl, serialized_value)
                return bool(result)
            else:
                # Memory cache fallback
                self._memory_cache[key] = value
                self._memory_cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)
                return True
                
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            if self._is_redis_available():
                value = self.redis_client.get(key)
                if value is not None:
                    return self._deserialize_value(value)
                return None
            else:
                # Memory cache fallback
                if key in self._memory_cache:
                    # Check TTL
                    if datetime.now() < self._memory_cache_ttl.get(key, datetime.now()):
                        return self._memory_cache[key]
                    else:
                        # Expired, remove from cache
                        del self._memory_cache[key]
                        if key in self._memory_cache_ttl:
                            del self._memory_cache_ttl[key]
                return None
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            if self._is_redis_available():
                result = self.redis_client.delete(key)
                return bool(result)
            else:
                # Memory cache fallback
                if key in self._memory_cache:
                    del self._memory_cache[key]
                if key in self._memory_cache_ttl:
                    del self._memory_cache_ttl[key]
                return True
                
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            if self._is_redis_available():
                return bool(self.redis_client.exists(key))
            else:
                # Memory cache fallback with TTL check
                if key in self._memory_cache:
                    if datetime.now() < self._memory_cache_ttl.get(key, datetime.now()):
                        return True
                    else:
                        # Expired
                        del self._memory_cache[key]
                        if key in self._memory_cache_ttl:
                            del self._memory_cache_ttl[key]
                return False
                
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    def cache_query_result(
        self, 
        sql_query: str, 
        params: tuple, 
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache query result with SQL and parameters as key."""
        try:
            # Create cache key from SQL query and parameters
            query_hash = hashlib.md5(
                f"{sql_query}:{str(params)}".encode('utf-8')
            ).hexdigest()
            
            cache_key = self._make_key(self.QUERY_PREFIX, query_hash)
            ttl = ttl or self.query_cache_ttl
            
            # Add metadata to cached result
            cached_data = {
                "result": result,
                "cached_at": datetime.now().isoformat(),
                "sql_query": sql_query,
                "params": params
            }
            
            return self.set(cache_key, cached_data, ttl)
            
        except Exception as e:
            logger.error(f"Error caching query result: {str(e)}")
            return False
    
    def get_cached_query_result(
        self, 
        sql_query: str, 
        params: tuple
    ) -> Optional[Dict[str, Any]]:
        """Get cached query result."""
        try:
            query_hash = hashlib.md5(
                f"{sql_query}:{str(params)}".encode('utf-8')
            ).hexdigest()
            
            cache_key = self._make_key(self.QUERY_PREFIX, query_hash)
            cached_data = self.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                return cached_data.get("result")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached query result: {str(e)}")
            return None
    
    def cache_schema_info(
        self, 
        database_name: str, 
        schema_info: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache database schema information."""
        try:
            cache_key = self._make_key(self.SCHEMA_PREFIX, database_name)
            ttl = ttl or self.schema_cache_ttl
            
            cached_data = {
                "schema_info": schema_info,
                "cached_at": datetime.now().isoformat()
            }
            
            return self.set(cache_key, cached_data, ttl)
            
        except Exception as e:
            logger.error(f"Error caching schema info: {str(e)}")
            return False
    
    def get_cached_schema_info(self, database_name: str) -> Optional[Dict[str, Any]]:
        """Get cached schema information."""
        try:
            cache_key = self._make_key(self.SCHEMA_PREFIX, database_name)
            cached_data = self.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                return cached_data.get("schema_info")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached schema info: {str(e)}")
            return None
    
    def set_user_session(
        self, 
        session_id: str, 
        user_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store user session data."""
        try:
            cache_key = self._make_key(self.SESSION_PREFIX, session_id)
            ttl = ttl or self.session_ttl
            
            session_data = {
                "user_data": user_data,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat()
            }
            
            return self.set(cache_key, session_data, ttl)
            
        except Exception as e:
            logger.error(f"Error setting user session: {str(e)}")
            return False
    
    def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data."""
        try:
            cache_key = self._make_key(self.SESSION_PREFIX, session_id)
            session_data = self.get(cache_key)
            
            if session_data and isinstance(session_data, dict):
                # Update last accessed time
                session_data["last_accessed"] = datetime.now().isoformat()
                self.set(cache_key, session_data, self.session_ttl)
                
                return session_data.get("user_data")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user session: {str(e)}")
            return None
    
    def delete_user_session(self, session_id: str) -> bool:
        """Delete user session."""
        try:
            cache_key = self._make_key(self.SESSION_PREFIX, session_id)
            return self.delete(cache_key)
            
        except Exception as e:
            logger.error(f"Error deleting user session: {str(e)}")
            return False
    
    def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int
    ) -> Dict[str, Any]:
        """Check and update rate limit for an identifier."""
        try:
            cache_key = self._make_key(self.RATE_LIMIT_PREFIX, identifier)
            
            if self._is_redis_available():
                # Use Redis for accurate rate limiting
                pipe = self.redis_client.pipeline()
                pipe.incr(cache_key)
                pipe.expire(cache_key, window_seconds)
                results = pipe.execute()
                
                current_count = results[0]
                
                return {
                    "allowed": current_count <= limit,
                    "count": current_count,
                    "limit": limit,
                    "window_seconds": window_seconds,
                    "reset_at": datetime.now() + timedelta(seconds=window_seconds)
                }
            else:
                # Memory-based rate limiting (less accurate)
                current_data = self.get(cache_key) or {"count": 0, "reset_at": datetime.now()}
                
                # Check if window has reset
                if datetime.now() > datetime.fromisoformat(current_data["reset_at"]):
                    current_data = {"count": 0, "reset_at": datetime.now() + timedelta(seconds=window_seconds)}
                
                current_data["count"] += 1
                self.set(cache_key, current_data, window_seconds)
                
                return {
                    "allowed": current_data["count"] <= limit,
                    "count": current_data["count"],
                    "limit": limit,
                    "window_seconds": window_seconds,
                    "reset_at": current_data["reset_at"]
                }
                
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # On error, allow the request
            return {
                "allowed": True,
                "count": 0,
                "limit": limit,
                "window_seconds": window_seconds,
                "error": str(e)
            }
    
    def acquire_lock(
        self, 
        lock_name: str, 
        timeout: int = 10,
        blocking_timeout: int = 5
    ) -> Optional[str]:
        """Acquire a distributed lock."""
        try:
            if not self._is_redis_available():
                # No distributed locking without Redis
                return None
            
            lock_key = self._make_key(self.LOCK_PREFIX, lock_name)
            lock_value = str(datetime.now().timestamp())
            
            # Try to acquire lock
            if self.redis_client.set(lock_key, lock_value, nx=True, ex=timeout):
                return lock_value
            
            return None
            
        except Exception as e:
            logger.error(f"Error acquiring lock {lock_name}: {str(e)}")
            return None
    
    def release_lock(self, lock_name: str, lock_value: str) -> bool:
        """Release a distributed lock."""
        try:
            if not self._is_redis_available():
                return False
            
            lock_key = self._make_key(self.LOCK_PREFIX, lock_name)
            
            # Lua script to atomically check and delete
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            else
                return 0
            end
            """
            
            result = self.redis_client.eval(lua_script, 1, lock_key, lock_value)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error releasing lock {lock_name}: {str(e)}")
            return False
    
    def cache_user_analytics(
        self, 
        user_id: str, 
        analytics_data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Cache user analytics data."""
        try:
            cache_key = self._make_key(self.ANALYTICS_PREFIX, "user", user_id)
            return self.set(cache_key, analytics_data, ttl)
            
        except Exception as e:
            logger.error(f"Error caching user analytics: {str(e)}")
            return False
    
    def get_cached_user_analytics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user analytics data."""
        try:
            cache_key = self._make_key(self.ANALYTICS_PREFIX, "user", user_id)
            return self.get(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached user analytics: {str(e)}")
            return None
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern (Redis only)."""
        try:
            if not self._is_redis_available():
                return 0
            
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if self._is_redis_available():
                info = self.redis_client.info()
                return {
                    "type": "redis",
                    "connected": True,
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0,
                    "hit_rate": "unknown",  # Would need to track this separately
                    "uptime": info.get("uptime_in_seconds", 0)
                }
            else:
                return {
                    "type": "memory",
                    "connected": True,
                    "total_keys": len(self._memory_cache),
                    "memory_used": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "type": "unknown",
                "connected": False,
                "error": str(e)
            }

# Global cache instance
cache = CacheService()

# Decorator for caching function results
def cached(ttl: int = 3600, key_prefix: str = "func"):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class CacheManager:
    """Redis cache manager for caching query results and schema information."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.settings = get_settings()
        
    async def initialize(self):
        """Initialize Redis connection."""
        if not self.settings.redis_enabled:
            logger.info("Redis caching is disabled")
            return
            
        try:
            self.redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                password=self.settings.redis_password,
                db=self.settings.redis_db,
                ssl=self.settings.redis_ssl,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
            
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.redis_client:
            return False
            
        try:
            ttl = ttl or self.settings.cache_ttl_seconds
            serialized_value = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
            
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.redis_client:
            return 0
            
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()

# Global cache instance
cache = CacheManager()

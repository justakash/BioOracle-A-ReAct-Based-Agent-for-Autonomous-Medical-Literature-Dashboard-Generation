"""
Redis Cache Layer
Caches API responses and query results to avoid redundant fetches.
"""

import hashlib
import json
import os
from typing import Any, Optional

from loguru import logger

try:
    import redis

    _client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
    _client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis cache connected.")
except Exception as e:
    logger.warning(f"Redis not available, caching disabled: {e}")
    REDIS_AVAILABLE = False
    _client = None

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 86400))


def _make_key(namespace: str, payload: Any) -> str:
    """Generate a deterministic cache key from namespace and payload."""
    raw = json.dumps(payload, sort_keys=True)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"biooracle:{namespace}:{digest}"


def get(namespace: str, payload: Any) -> Optional[Any]:
    """Retrieve a cached value. Returns None if not found or Redis unavailable."""
    if not REDIS_AVAILABLE:
        return None
    key = _make_key(namespace, payload)
    try:
        value = _client.get(key)
        if value:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache get failed: {e}")
    return None


def set(namespace: str, payload: Any, value: Any, ttl: int = CACHE_TTL) -> bool:
    """Store a value in the cache. Returns True on success."""
    if not REDIS_AVAILABLE:
        return False
    key = _make_key(namespace, payload)
    try:
        _client.setex(key, ttl, json.dumps(value))
        logger.debug(f"Cache SET: {key} (ttl={ttl}s)")
        return True
    except Exception as e:
        logger.warning(f"Cache set failed: {e}")
        return False


def invalidate(namespace: str, payload: Any) -> bool:
    """Remove a single key from the cache."""
    if not REDIS_AVAILABLE:
        return False
    key = _make_key(namespace, payload)
    try:
        _client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache invalidation failed: {e}")
        return False


def flush_namespace(namespace: str) -> int:
    """Delete all keys under a given namespace prefix. Returns count deleted."""
    if not REDIS_AVAILABLE:
        return 0
    pattern = f"biooracle:{namespace}:*"
    try:
        keys = _client.keys(pattern)
        if keys:
            return _client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache flush failed: {e}")
        return 0

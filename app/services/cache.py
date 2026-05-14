import json
import redis
from typing import Optional, Any
from app.config import get_settings
from app.logger import app_logger

settings = get_settings()

# Metrics storage (in-memory for demo; use Redis/Prometheus in prod)
cache_metrics = {"hits": 0, "misses": 0}

try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    app_logger.info("Redis connection established successfully")
except Exception as e:
    REDIS_AVAILABLE = False
    redis_client = None
    app_logger.warning(f"Redis not available, caching disabled: {e}")


def get_cache(key: str) -> Optional[Any]:
    if not REDIS_AVAILABLE:
        cache_metrics["misses"] += 1
        return None
    try:
        data = redis_client.get(key)
        if data:
            cache_metrics["hits"] += 1
            app_logger.debug(f"Cache HIT: {key}")
            return json.loads(data)
        cache_metrics["misses"] += 1
        app_logger.debug(f"Cache MISS: {key}")
        return None
    except Exception as e:
        app_logger.error(f"Cache GET error for key '{key}': {e}")
        cache_metrics["misses"] += 1
        return None


def set_cache(key: str, value: Any, ttl: int = None) -> bool:
    if not REDIS_AVAILABLE:
        return False
    try:
        ttl = ttl or settings.CACHE_TTL
        redis_client.setex(key, ttl, json.dumps(value, default=str))
        app_logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
        return True
    except Exception as e:
        app_logger.error(f"Cache SET error for key '{key}': {e}")
        return False


def delete_cache(key: str) -> bool:
    if not REDIS_AVAILABLE:
        return False
    try:
        redis_client.delete(key)
        app_logger.debug(f"Cache DELETE: {key}")
        return True
    except Exception as e:
        app_logger.error(f"Cache DELETE error for key '{key}': {e}")
        return False


def delete_pattern(pattern: str) -> int:
    if not REDIS_AVAILABLE:
        return 0
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            app_logger.debug(f"Cache PURGE pattern '{pattern}': {len(keys)} keys deleted")
        return len(keys)
    except Exception as e:
        app_logger.error(f"Cache PURGE error for pattern '{pattern}': {e}")
        return 0


def get_cache_info() -> dict:
    if not REDIS_AVAILABLE:
        return {"status": "unavailable", "hits": cache_metrics["hits"], "misses": cache_metrics["misses"]}
    try:
        info = redis_client.info()
        return {
            "status": "available",
            "hits": cache_metrics["hits"],
            "misses": cache_metrics["misses"],
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

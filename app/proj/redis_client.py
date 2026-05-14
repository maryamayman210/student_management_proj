import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(_name_)


class RedisClient:
    _instance = None

    def _new_(cls):
        if cls._instance is None:
            cls.instance = super().new_(cls)

            try:
                cls._instance.client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                cls._instance._connected = True
                logger.info("Redis connected successfully")

            except Exception as e:
                logger.warning(f"Redis not available, using local cache. Error: {e}")
                cls._instance.client = None
                cls._instance._connected = False
                cls._instance._local_cache = {}
                cls._instance._expiry = {}

        return cls._instance

    # ---------- helpers ----------
    def is_connected(self):
        return self._connected and self.client

    def _serialize(self, value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    def _deserialize(self, value: str) -> Any:
        try:
            return json.loads(value)
        except:
            return value

    # ---------- GET ----------
    def get(self, key: str) -> Optional[Any]:
        if self.is_connected():
            value = self.client.get(key)
            return self._deserialize(value) if value else None

        # local cache
        if key in getattr(self, "_expiry", {}):
            if datetime.now() > self._expiry[key]:
                self._local_cache.pop(key, None)
                self._expiry.pop(key, None)
                return None

        return self._local_cache.get(key)

    # ---------- SET ----------
    def set(self, key: str, value: Any, expire: int = 60) -> None:
        value = self._serialize(value)

        if self.is_connected():
            self.client.setex(key, expire, value)
        else:
            self._local_cache[key] = value
            self._expiry[key] = datetime.now() + timedelta(seconds=expire)

    # ---------- DELETE ----------
    def delete(self, key: str) -> None:
        if self.is_connected():
            self.client.delete(key)
        else:
            self._local_cache.pop(key, None)
            self._expiry.pop(key, None)

    # ---------- PATTERN DELETE ----------
    def delete_pattern(self, pattern: str) -> None:
        if self.is_connected():
            keys = self.client.keys(f"{pattern}")
            if keys:
                self.client.delete(*keys)
        else:
            for key in list(self._local_cache.keys()):
                if pattern in key:
                    self.delete(key)


# Singleton (IMPORTANT FIX)
redis_client = RedisClient()
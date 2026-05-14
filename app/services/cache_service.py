from typing import Optional, Any
import json
from app.core.redis_client import redis_client


class CacheService:
    """
    Unified Cache Service
    Handles Redis + fallback safely
    """

    @staticmethod
    def _serialize(value: Any) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

    @staticmethod
    def _deserialize(value: Any) -> Any:
        if value is None:
            return None
        try:
            return json.loads(value)
        except:
            return value

    # ---------- GET ----------
    @staticmethod
    def get(key: str) -> Optional[Any]:
        try:
            value = redis_client.get(key)
            return CacheService._deserialize(value)
        except Exception:
            return None

    # ---------- SET ----------
    @staticmethod
    def set(key: str, value: Any, expire: int = 60) -> None:
        try:
            value = CacheService._serialize(value)
            redis_client.set(key, value, expire)
        except Exception:
            pass  # fail silently (cache is not critical)

    # ---------- DELETE ----------
    @staticmethod
    def delete(key: str) -> None:
        try:
            redis_client.delete(key)
        except Exception:
            pass

    # ---------- PATTERN DELETE ----------
    @staticmethod
    def delete_pattern(pattern: str) -> None:
        try:
            redis_client.delete_pattern(pattern)
        except Exception:
            pass

    # ---------- CLEAR ALL ----------
    @staticmethod
    def clear_all() -> None:
        try:
            redis_client.delete_pattern("*")
        except Exception:
            pass


cache_service = CacheService()
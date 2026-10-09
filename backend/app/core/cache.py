"""
Thin Redis wrapper used to cache market data and indicator results.

Falls back to a no-op in-memory dict if Redis is unreachable, so the
application remains usable in local/dev environments without Redis running.
"""
import json
from typing import Any, Optional

import redis

from app.core.config import settings


class Cache:
    def __init__(self, url: str):
        self._memory_fallback: dict[str, str] = {}
        try:
            self._client: Optional[redis.Redis] = redis.Redis.from_url(
                url, decode_responses=True, socket_connect_timeout=1
            )
            self._client.ping()
        except Exception:
            self._client = None

    def get_json(self, key: str) -> Optional[Any]:
        raw = self._get_raw(key)
        return json.loads(raw) if raw is not None else None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        raw = json.dumps(value, default=str)
        self._set_raw(key, raw, ttl_seconds)

    def _get_raw(self, key: str) -> Optional[str]:
        if self._client is not None:
            try:
                return self._client.get(key)
            except Exception:
                pass
        return self._memory_fallback.get(key)

    def _set_raw(self, key: str, value: str, ttl_seconds: int) -> None:
        if self._client is not None:
            try:
                self._client.setex(key, ttl_seconds, value)
                return
            except Exception:
                pass
        self._memory_fallback[key] = value

    def stats(self) -> dict:
        """Rough cache stats used for the README's engineering metrics."""
        if self._client is not None:
            try:
                info = self._client.info(section="stats")
                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                total = hits + misses
                return {
                    "backend": "redis",
                    "hits": hits,
                    "misses": misses,
                    "hit_rate": (hits / total) if total else 0.0,
                }
            except Exception:
                pass
        return {"backend": "in-memory-fallback", "keys": len(self._memory_fallback)}


cache = Cache(settings.REDIS_URL)

from cache.abstract_cache import AbstractCache
from datetime import datetime, timedelta, timezone


_CacheEntry = tuple[object, datetime]


class InMemoryCache(AbstractCache):
    def __init__(self) -> None:
        self._store: dict[str, _CacheEntry] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None

        value, expires_at = entry
        if datetime.now(tz=timezone.utc) >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value, ttl_seconds: int) -> None:
        expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=ttl_seconds)
        self._store[key] = (value, expires_at)

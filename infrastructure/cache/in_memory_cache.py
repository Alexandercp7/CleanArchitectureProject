from cache.abstract_cache import AbstractCache


class InMemoryCache(AbstractCache):
    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value, ttl_seconds: int) -> None:
        self._store[key] = value

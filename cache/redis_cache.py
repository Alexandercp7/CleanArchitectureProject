import json
import redis
from dataclasses import asdict
from domain.product import Product
from cache.abstract_cache import AbstractCache

DEFAULT_TTL = 300


class RedisCache(AbstractCache):

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    def get(self, key: str) -> list[Product] | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        return [Product(**item) for item in json.loads(raw)]

    def set(self, key: str, value: list[Product], ttl_seconds: int = DEFAULT_TTL) -> None:
        self._client.setex(key, ttl_seconds, json.dumps([asdict(p) for p in value]))

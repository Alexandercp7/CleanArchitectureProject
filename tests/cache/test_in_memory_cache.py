from datetime import datetime, timedelta, timezone

from infrastructure.cache.in_memory_cache import InMemoryCache


def test_returns_none_for_missing_key() -> None:
    cache = InMemoryCache()
    assert cache.get("missing") is None


def test_returns_value_before_ttl_expires() -> None:
    cache = InMemoryCache()
    cache.set("key", ["value"], ttl_seconds=10)

    assert cache.get("key") == ["value"]


def test_returns_none_after_ttl_expired() -> None:
    cache = InMemoryCache()
    cache.set("key", ["value"], ttl_seconds=10)

    value, _ = cache._store["key"]
    cache._store["key"] = (value, datetime.now(tz=timezone.utc) - timedelta(seconds=1))

    assert cache.get("key") is None
    assert "key" not in cache._store

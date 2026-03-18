from unittest.mock import MagicMock
from dataclasses import asdict
import json
import redis
from domain.product import Product
from cache.redis_cache import RedisCache, build_cache_key


def make_product(**overrides) -> Product:
    defaults = dict(
        title="Laptop",
        price=1000.0,
        in_stock=True,
        delivery_days=5,
        source="mercadolibre",
    )
    return Product(**{**defaults, **overrides})


def make_cache() -> tuple[RedisCache, MagicMock]:
    mock_client = MagicMock(spec=redis.Redis)
    return RedisCache(client=mock_client), mock_client


def test_returns_none_when_cache_miss():
    cache, mock_client = make_cache()
    mock_client.get.return_value = None

    result = cache.get("nonexistent-key")

    assert result is None


def test_returns_products_when_cache_hit():
    cache, mock_client = make_cache()
    product = make_product()
    mock_client.get.return_value = json.dumps([asdict(product)]).encode()

    result = cache.get("some-key")

    assert len(result) == 1
    assert result[0].title == "Laptop"


def test_stores_products_with_ttl():
    cache, mock_client = make_cache()
    product = make_product()

    cache.set("some-key", [product], ttl_seconds=60)

    mock_client.setex.assert_called_once()
    args = mock_client.setex.call_args[0]
    assert args[0] == "some-key"
    assert args[1] == 60


def test_same_query_and_weights_produce_same_cache_key():
    key1 = build_cache_key("laptop", {"price": 0.6, "availability": 0.4})
    key2 = build_cache_key("laptop", {"price": 0.6, "availability": 0.4})

    assert key1 == key2


def test_different_queries_produce_different_cache_keys():
    key1 = build_cache_key("laptop", {"price": 1.0})
    key2 = build_cache_key("phone", {"price": 1.0})

    assert key1 != key2
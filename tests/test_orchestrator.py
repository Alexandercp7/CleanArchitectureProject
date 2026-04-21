from unittest.mock import AsyncMock, MagicMock
import pytest
from normalizer.engine import Normalizer
from ranker.strategy import RankStrategy
from cache.abstract_cache import AbstractCache
from domain.ports import RawProduct, StoreAdapter
from domain.product import Product
from application.search.search_service import SearchRequest, SearchService


def make_product(**overrides) -> Product:
    defaults = dict(
        title="Laptop",
        cash_price=1000.0,
        installment_price=None,
        months_without_interest=False,
        msi_months=None,
        in_stock=True,
        delivery_days=None,
        url="https://example.com/product",
    )
    return Product(**{**defaults, **overrides})


def make_orchestrator(
    products: list[Product],
    cache_hit: bool = False,
) -> SearchService:
    adapter = MagicMock(spec=StoreAdapter)
    adapter.source_name = "mercadolibrescraperadapter"
    adapter.fetch_raw_products = AsyncMock(return_value=[
        RawProduct(source_id="1", fields={"title": "Laptop", "cash_price": "1000"})
    ])

    normalizer = MagicMock(spec=Normalizer)
    normalizer.normalize_to_product.return_value = products[0] if products else make_product()

    ranker = MagicMock(spec=RankStrategy)
    ranker.score_all.return_value = products

    cache = MagicMock(spec=AbstractCache)
    cache.get.return_value = products if cache_hit else None

    return SearchService(
        adapters=[adapter],
        normalizer=normalizer,
        ranker=ranker,
        cache=cache,
    )


@pytest.mark.asyncio
async def test_returns_cached_results_when_cache_hit():
    product = make_product(title="Cached laptop")
    orchestrator = make_orchestrator([product], cache_hit=True)

    result = await orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    assert result[0].title == "Cached laptop"


@pytest.mark.asyncio
async def test_skips_adapters_when_cache_hit():
    product = make_product()
    orchestrator = make_orchestrator([product], cache_hit=True)

    await orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    orchestrator._adapters[0].fetch_raw_products.assert_not_called()


@pytest.mark.asyncio
async def test_calls_adapters_when_cache_miss():
    product = make_product()
    orchestrator = make_orchestrator([product], cache_hit=False)

    await orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    orchestrator._adapters[0].fetch_raw_products.assert_awaited_once_with("laptop")


@pytest.mark.asyncio
async def test_stores_results_in_cache_after_miss():
    product = make_product()
    orchestrator = make_orchestrator([product], cache_hit=False)

    await orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    orchestrator._cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_returns_ranked_products_after_cache_miss():
    products = [
        make_product(title="Best laptop", cash_price=500.0),
        make_product(title="Worst laptop", cash_price=9000.0),
    ]
    orchestrator = make_orchestrator(products, cache_hit=False)

    result = await orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    assert result[0].title == "Best laptop"


@pytest.mark.asyncio
async def test_returns_cache_hit_status_when_result_comes_from_cache():
    product = make_product(title="Cached laptop")
    orchestrator = make_orchestrator([product], cache_hit=True)

    result, from_cache = await orchestrator.search(query="laptop", weights={"price": 1.0})

    assert from_cache is True
    assert result[0].title == "Cached laptop"


@pytest.mark.asyncio
async def test_returns_cache_miss_status_when_result_comes_from_web():
    product = make_product(title="Web laptop")
    orchestrator = make_orchestrator([product], cache_hit=False)

    result, from_cache = await orchestrator.search(query="laptop", weights={"price": 1.0})

    assert from_cache is False
    assert result[0].title == "Web laptop"


@pytest.mark.asyncio
async def test_continues_with_other_adapters_when_one_fails() -> None:
    failing_adapter = MagicMock(spec=StoreAdapter)
    failing_adapter.source_name = "amazonscraperadapter"
    failing_adapter.fetch_raw_products = AsyncMock(side_effect=RuntimeError("boom"))

    working_adapter = MagicMock(spec=StoreAdapter)
    working_adapter.source_name = "mercadolibrescraperadapter"
    working_adapter.fetch_raw_products = AsyncMock(
        return_value=[RawProduct(source_id="1", fields={"title": "Laptop", "cash_price": "1000"})]
    )

    normalizer = MagicMock(spec=Normalizer)
    normalizer.normalize_to_product.return_value = make_product(title="Recovered laptop")

    ranker = MagicMock(spec=RankStrategy)
    ranker.score_all.side_effect = lambda products, _weights: products

    cache = MagicMock(spec=AbstractCache)
    cache.get.return_value = None

    orchestrator = SearchService(
        adapters=[failing_adapter, working_adapter],
        normalizer=normalizer,
        ranker=ranker,
        cache=cache,
    )

    result, from_cache = await orchestrator.search(query="laptop", weights={"price": 1.0})

    assert from_cache is False
    assert len(result) == 1
    assert result[0].title == "Recovered laptop"
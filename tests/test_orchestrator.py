from unittest.mock import MagicMock
from adapters.base import StoreAdapter, RawProduct
from normalizer.engine import Normalizer
from ranker.strategy import RankStrategy
from cache.abstract_cache import AbstractCache
from domain.product import Product
from orchestrator import SearchOrchestrator, SearchRequest


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
) -> SearchOrchestrator:
    adapter = MagicMock(spec=StoreAdapter)
    adapter.source_name = "mercadolibrescraperadapter"
    adapter.fetch_raw_products.return_value = [
        RawProduct(source_id="1", fields={"title": "Laptop", "cash_price": "1000"})
    ]

    normalizer = MagicMock(spec=Normalizer)
    normalizer.normalize_to_product.return_value = products[0] if products else make_product()

    ranker = MagicMock(spec=RankStrategy)
    ranker.score_all.return_value = products

    cache = MagicMock(spec=AbstractCache)
    cache.get.return_value = products if cache_hit else None

    return SearchOrchestrator(
        adapters=[adapter],
        normalizer=normalizer,
        ranker=ranker,
        cache=cache,
    )


def test_returns_cached_results_when_cache_hit():
    product = make_product(title="Cached laptop")
    orchestrator = make_orchestrator([product], cache_hit=True)

    result = orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    assert result[0].title == "Cached laptop"


def test_skips_adapters_when_cache_hit():
    product = make_product()
    orchestrator = make_orchestrator([product], cache_hit=True)

    orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    orchestrator._adapters[0].fetch_raw_products.assert_not_called()


def test_calls_adapters_when_cache_miss():
    product = make_product()
    orchestrator = make_orchestrator([product], cache_hit=False)

    orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    orchestrator._adapters[0].fetch_raw_products.assert_called_once_with("laptop")


def test_stores_results_in_cache_after_miss():
    product = make_product()
    orchestrator = make_orchestrator([product], cache_hit=False)

    orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    orchestrator._cache.set.assert_called_once()


def test_returns_ranked_products_after_cache_miss():
    products = [
        make_product(title="Best laptop", cash_price=500.0),
        make_product(title="Worst laptop", cash_price=9000.0),
    ]
    orchestrator = make_orchestrator(products, cache_hit=False)

    result = orchestrator.search_and_rank(
        SearchRequest(query="laptop", weights={"price": 1.0})
    )

    assert result[0].title == "Best laptop"
from dataclasses import dataclass
from adapters.base import StoreAdapter
from normalizer.engine import Normalizer
from ranker.strategy import RankStrategy
from cache.abstract_cache import AbstractCache
from cache.key_builder import build_cache_key
from domain.product import Product

DEFAULT_CACHE_TTL = 300


@dataclass(frozen=True)
class SearchRequest:
    query: str
    weights: dict[str, float]


class SearchOrchestrator:

    def __init__(
        self,
        adapters: list[StoreAdapter],
        normalizer: Normalizer,
        ranker: RankStrategy,
        cache: AbstractCache,
    ) -> None:
        self._adapters = adapters
        self._normalizer = normalizer
        self._ranker = ranker
        self._cache = cache

    def search_and_rank(self, request: SearchRequest) -> list[Product]:
        ranked_products, _ = self.search_and_rank_with_cache_status(request)
        return ranked_products

    def search_and_rank_with_cache_status(self, request: SearchRequest) -> tuple[list[Product], bool]:
        cache_key = build_cache_key(request.query, request.weights)

        cached_products = self._cache.get(cache_key)
        if cached_products is not None:
            return cached_products, True

        products = self._collect_products(request.query)
        ranked_products = self._ranker.score_all(products, request.weights)

        self._cache.set(cache_key, ranked_products, DEFAULT_CACHE_TTL)
        return ranked_products, False

    def _collect_products(self, query: str) -> list[Product]:
        products: list[Product] = []
        for adapter in self._adapters:
            source_name = adapter.source_name
            raw_items = adapter.fetch_raw_products(query)
            for raw in raw_items:
                products.append(
                    self._normalizer.normalize_to_product(raw, source_name)
                )
        return products
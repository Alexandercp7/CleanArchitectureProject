import asyncio
from dataclasses import dataclass

from adapters.base import StoreAdapter
from cache.abstract_cache import AbstractCache
from cache.key_builder import build_cache_key
from domain.product import Product
from normalizer.engine import Normalizer
from ranker.strategy import RankStrategy

DEFAULT_CACHE_TTL = 300


@dataclass(frozen=True)
class SearchRequest:
    query: str
    weights: dict[str, float]


class SearchService:
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

    async def search(self, query: str, weights: dict[str, float]) -> tuple[list[Product], bool]:
        cache_key = build_cache_key(query, weights)

        cached_products = self._cache.get(cache_key)
        if cached_products is not None:
            return cached_products, True

        products = await self._collect_products(query)
        ranked_products = self._ranker.score_all(products, weights)

        self._cache.set(cache_key, ranked_products, DEFAULT_CACHE_TTL)
        return ranked_products, False

    async def search_and_rank(self, request: SearchRequest) -> list[Product]:
        ranked_products, _ = await self.search(query=request.query, weights=request.weights)
        return ranked_products

    async def _collect_products(self, query: str) -> list[Product]:
        products: list[Product] = []
        raw_items_per_adapter = await asyncio.gather(
            *(adapter.fetch_raw_products(query) for adapter in self._adapters)
        )
        for adapter, raw_items in zip(self._adapters, raw_items_per_adapter):
            source_name = adapter.source_name
            for raw in raw_items:
                products.append(self._normalizer.normalize_to_product(raw, source_name))
        return products

import asyncio
import logging
import time
from dataclasses import dataclass

from cache.abstract_cache import AbstractCache
from cache.key_builder import build_cache_key
from domain.ports import RawProduct, StoreAdapter
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
        self._logger = logging.getLogger(__name__)

    async def search(self, query: str, weights: dict[str, float]) -> tuple[list[Product], bool]:
        started_at = time.perf_counter()
        cache_key = build_cache_key(query, weights)

        cached_products = self._cache.get(cache_key)
        if cached_products is not None:
            self._logger.info(
                "search_completed",
                extra={
                    "query": query,
                    "cache": "hit",
                    "total_results": len(cached_products),
                    "total_duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                },
            )
            return cached_products, True

        products = await self._collect_products(query)
        ranked_products = self._ranker.score_all(products, weights)

        self._cache.set(cache_key, ranked_products, DEFAULT_CACHE_TTL)
        self._logger.info(
            "search_completed",
            extra={
                "query": query,
                "cache": "miss",
                "total_results": len(ranked_products),
                "total_duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            },
        )
        return ranked_products, False

    async def search_and_rank(self, request: SearchRequest) -> list[Product]:
        ranked_products, _ = await self.search(query=request.query, weights=request.weights)
        return ranked_products

    async def _collect_products(self, query: str) -> list[Product]:
        products: list[Product] = []
        raw_items_per_adapter = await asyncio.gather(
            *(self._fetch_with_retry(adapter, query) for adapter in self._adapters)
        )
        for adapter, raw_items in zip(self._adapters, raw_items_per_adapter):
            source_name = adapter.source_name
            for raw in raw_items:
                products.append(self._normalizer.normalize_to_product(raw, source_name))
        return products

    async def _fetch_with_retry(self, adapter: StoreAdapter, query: str) -> list[RawProduct]:
        retries = 2
        for attempt in range(retries + 1):
            adapter_started_at = time.perf_counter()
            try:
                raw_items = await adapter.fetch_raw_products(query)
                self._logger.info(
                    "adapter_fetch_completed",
                    extra={
                        "adapter": adapter.source_name,
                        "query": query,
                        "result_count": len(raw_items),
                        "attempt": attempt + 1,
                        "duration_ms": round((time.perf_counter() - adapter_started_at) * 1000, 2),
                    },
                )
                return raw_items
            except Exception as exc:
                if attempt == retries:
                    self._logger.error(
                        "adapter_fetch_failed",
                        extra={
                            "adapter": adapter.source_name,
                            "query": query,
                            "attempt": attempt + 1,
                        },
                        exc_info=exc,
                    )
                    return []

                backoff_seconds = 0.2 * (2**attempt)
                self._logger.warning(
                    "adapter_fetch_retrying",
                    extra={
                        "adapter": adapter.source_name,
                        "query": query,
                        "attempt": attempt + 1,
                        "backoff_seconds": backoff_seconds,
                    },
                    exc_info=exc,
                )
                await asyncio.sleep(backoff_seconds)

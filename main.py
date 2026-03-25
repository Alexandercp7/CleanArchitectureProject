import httpx
from pathlib import Path

from adapters.amazon_scraper_adapter import AmazonScraperAdapter
from adapters.mercadolibre_scraper_adapter import MercadoLibreScraperAdapter
from normalizer.engine import Normalizer
from normalizer.yaml_mapping_loader import YamlMappingLoader
from ranker.weighted_scorer import WeightedScorer
from cache.abstract_cache import AbstractCache
from domain.product.product import Product
from orchestrator import SearchOrchestrator
from api.routes import create_router


class InMemoryCache(AbstractCache):
    def __init__(self):
        self._store = {}

    def get(self, key: str) -> list[Product] | None:
        return self._store.get(key)

    def set(self, key: str, value: list[Product], ttl_seconds: int) -> None:
        self._store[key] = value


orchestrator = SearchOrchestrator(
    adapters=[
        AmazonScraperAdapter(
            http_client=httpx.Client(timeout=10.0, follow_redirects=True)
        ),
        MercadoLibreScraperAdapter(
            http_client=httpx.Client(timeout=10.0, follow_redirects=True)
        ),
    ],
    normalizer=Normalizer(
        mapping_loader=YamlMappingLoader(
            mappings_dir=Path("normalizer/mappings")
        )
    ),
    ranker=WeightedScorer(),
    cache=InMemoryCache(),
)

app = create_router(orchestrator)
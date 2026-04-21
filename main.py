from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from adapters.amazon_scraper_adapter import AmazonScraperAdapter
from adapters.mercadolibre_scraper_adapter import MercadoLibreScraperAdapter
from alerts.notifier import Notifier
from alerts.repository import AlertRepository
from alerts.scheduler import AlertScheduler
from alerts.tracker import AlertTracker
from api.alert_routes import AlertRouteDependencies, get_alert_dependencies, router as alert_router
from api.auth_routes import router as auth_router
from api.search_routes import SearchRouteDependencies, get_search_dependencies, router as search_router
from auth.service import AuthService
from auth.user_repository import UserRepository
from application.search.search_service import SearchService
from cache.abstract_cache import AbstractCache
from cache.redis_cache import RedisCache
from config import AppConfig
from infrastructure.cache.in_memory_cache import InMemoryCache
from infrastructure.persistence.models.alert_model import AlertBase
from infrastructure.persistence.models.user_model import UserBase
from logging_config import configure_logging
from normalizer.engine import Normalizer
from normalizer.yaml_mapping_loader import YamlMappingLoader
from ranker.weighted_scorer import WeightedScorer


@dataclass
class AppDependencies:
    auth_service: AuthService
    alert_repository: AlertRepository
    orchestrator: SearchService
    scheduler: AlertScheduler | None
    httpx_client: httpx.AsyncClient
    database_engine: AsyncEngine
    redis_client: Redis | None


def _assert_safe_to_start(settings: AppConfig) -> None:
    if settings.cors.allow_credentials and "*" in settings.cors.allow_methods:
        raise RuntimeError("CORS cannot allow credentials with wildcard methods")
    if settings.cors.allow_credentials and "*" in settings.cors.allow_headers:
        raise RuntimeError("CORS cannot allow credentials with wildcard headers")


def _create_database_engine(settings: AppConfig) -> AsyncEngine:
    engine_kwargs = {"echo": settings.database.echo_sql}

    # Why: SQLite does not support pool_size/max_overflow options.
    if settings.database.requires_connection_pool():
        engine_kwargs["pool_size"] = settings.database.pool_size
        engine_kwargs["max_overflow"] = settings.database.max_overflow

    return create_async_engine(settings.database.url, **engine_kwargs)


def _create_redis_client(settings: AppConfig) -> Redis | None:
    if not settings.redis.enabled:
        return None
    return Redis.from_url(settings.redis.url, decode_responses=False)


def _create_orchestrator(cache: AbstractCache) -> SearchService:
    adapters = [
        AmazonScraperAdapter(http_client=httpx.AsyncClient(timeout=10.0, follow_redirects=True)),
        MercadoLibreScraperAdapter(http_client=httpx.AsyncClient(timeout=10.0, follow_redirects=True)),
    ]
    normalizer = Normalizer(mapping_loader=YamlMappingLoader(mappings_dir=Path("normalizer/mappings")))
    return SearchService(adapters=adapters, normalizer=normalizer, ranker=WeightedScorer(), cache=cache)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = AppConfig()
    configure_logging()
    _assert_safe_to_start(settings)

    engine = _create_database_engine(settings)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    redis_client = _create_redis_client(settings)
    cache: AbstractCache = RedisCache(redis_client) if redis_client is not None else InMemoryCache()
    orchestrator = _create_orchestrator(cache)

    user_repo = UserRepository(session_factory)
    auth_service = AuthService(repo=user_repo)

    alert_repo = AlertRepository(session_factory)
    notifier_client = httpx.AsyncClient(base_url=settings.notifier.endpoint_url) if settings.notifier.can_send_email() else None
    notifier = Notifier(http_client=notifier_client)
    tracker = AlertTracker()

    scheduler = None
    if settings.scheduler.enabled:
        scheduler = AlertScheduler(
            orchestrator=orchestrator,
            repo=alert_repo,
            tracker=tracker,
            notifier=notifier,
        )
        scheduler.start()

    async with engine.begin() as connection:
        await connection.run_sync(UserBase.metadata.create_all)
        await connection.run_sync(AlertBase.metadata.create_all)

    deps = AppDependencies(
        auth_service=auth_service,
        alert_repository=alert_repo,
        orchestrator=orchestrator,
        scheduler=scheduler,
        httpx_client=httpx.AsyncClient(),
        database_engine=engine,
        redis_client=redis_client,
    )
    app.state.deps = deps

    try:
        yield
    finally:
        if scheduler is not None:
            await scheduler.stop()
        await deps.httpx_client.aclose()
        if notifier_client is not None:
            await notifier_client.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = AppConfig()
    app = FastAPI(title="Search Orchestrator API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors.allow_origins),
        allow_methods=list(settings.cors.allow_methods),
        allow_headers=list(settings.cors.allow_headers),
        allow_credentials=settings.cors.allow_credentials,
    )

    app.include_router(search_router)
    app.include_router(auth_router)
    app.include_router(alert_router)

    def _provide_search_deps() -> SearchRouteDependencies:
        return SearchRouteDependencies(orchestrator=app.state.deps.orchestrator)

    def _provide_alert_deps() -> AlertRouteDependencies:
        return AlertRouteDependencies(repo=app.state.deps.alert_repository)

    app.dependency_overrides[get_search_dependencies] = _provide_search_deps
    app.dependency_overrides[get_alert_dependencies] = _provide_alert_deps
    return app


app = create_app()

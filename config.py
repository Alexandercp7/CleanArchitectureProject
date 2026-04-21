from __future__ import annotations

from dataclasses import dataclass
import os


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    return int(raw_value) if raw_value is not None else default


@dataclass(frozen=True)
class AuthConfig:
    jwt_secret: str = os.getenv("AUTH_JWT_SECRET", "dev-secret-change-me-please-use-32-bytes")
    algorithm: str = os.getenv("AUTH_JWT_ALGORITHM", "HS256")
    access_token_ttl_seconds: int = _get_int("AUTH_ACCESS_TTL_SECONDS", 900)
    refresh_token_ttl_seconds: int = _get_int("AUTH_REFRESH_TTL_SECONDS", 1209600)

    def is_safe_for_production(self) -> bool:
        has_non_default_secret = self.jwt_secret != "dev-secret-change-me-please-use-32-bytes"
        has_minimum_length = len(self.jwt_secret) >= 32
        return has_non_default_secret and has_minimum_length


@dataclass(frozen=True)
class DatabaseConfig:
    url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./search_orchestrator.db")
    echo_sql: bool = _get_bool("DATABASE_ECHO_SQL", False)
    pool_size: int = _get_int("DATABASE_POOL_SIZE", 5)
    max_overflow: int = _get_int("DATABASE_MAX_OVERFLOW", 10)

    def requires_connection_pool(self) -> bool:
        return not self.url.startswith("sqlite")


@dataclass(frozen=True)
class RedisConfig:
    url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    enabled: bool = _get_bool("REDIS_ENABLED", False)


@dataclass(frozen=True)
class SchedulerConfig:
    enabled: bool = _get_bool("SCHEDULER_ENABLED", False)
    tick_interval_seconds: int = _get_int("SCHEDULER_TICK_SECONDS", 30)


@dataclass(frozen=True)
class NotifierConfig:
    enabled: bool = _get_bool("NOTIFIER_ENABLED", False)
    endpoint_url: str = os.getenv("NOTIFIER_ENDPOINT_URL", "")
    api_key: str = os.getenv("NOTIFIER_API_KEY", "")

    def can_send_email(self) -> bool:
        has_credentials = bool(self.endpoint_url and self.api_key)
        return self.enabled and has_credentials


@dataclass(frozen=True)
class CorsConfig:
    allow_origins: tuple[str, ...] = tuple(
        value.strip()
        for value in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",")
        if value.strip()
    )
    allow_methods: tuple[str, ...] = tuple(
        value.strip().upper()
        for value in os.getenv("CORS_ALLOW_METHODS", "GET,POST,DELETE").split(",")
        if value.strip()
    )
    allow_headers: tuple[str, ...] = tuple(
        value.strip()
        for value in os.getenv("CORS_ALLOW_HEADERS", "Authorization,Content-Type").split(",")
        if value.strip()
    )
    allow_credentials: bool = _get_bool("CORS_ALLOW_CREDENTIALS", True)

    def permits_any_origin(self) -> bool:
        return "*" in self.allow_origins


@dataclass(frozen=True)
class AppConfig:
    auth: AuthConfig = AuthConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    scheduler: SchedulerConfig = SchedulerConfig()
    notifier: NotifierConfig = NotifierConfig()
    cors: CorsConfig = CorsConfig()


settings = AppConfig()

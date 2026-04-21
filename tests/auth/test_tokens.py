import time

import jwt
import pytest

from auth.token_service import (
    InMemoryRefreshTokenStore,
    TokenService,
    TokenSettings,
)
from auth.tokens import (
    ExpiredTokenError,
    InvalidTokenError,
    ReplayDetectedError,
)


def make_service(
    access_ttl_seconds: int = 60,
    refresh_ttl_seconds: int = 120,
) -> TokenService:
    settings = TokenSettings(
        algorithm="HS256",
        issuer="search-orchestrator",
        audience="search-api",
        access_ttl_seconds=access_ttl_seconds,
        refresh_ttl_seconds=refresh_ttl_seconds,
        leeway_seconds=0,
        private_key="dev-secret-key-with-at-least-32-bytes!!",
        public_key="dev-secret-key-with-at-least-32-bytes!!",
        key_id="v1",
    )
    return TokenService(settings=settings, store=InMemoryRefreshTokenStore())


def test_issue_and_verify_access_token() -> None:
    service = make_service()

    access_token, refresh_token = service.issue_tokens("user-123", scopes=["search:read"])

    payload = service.verify_access_token(access_token)

    assert payload["sub"] == "user-123"
    assert payload["typ"] == "access"
    assert payload["scope"] == "search:read"
    assert isinstance(refresh_token, str)


def test_verify_rejects_wrong_header_type() -> None:
    service = make_service()
    now = int(time.time())

    token = jwt.encode(
        {
            "iss": service.settings.issuer,
            "sub": "user-123",
            "aud": service.settings.audience,
            "iat": now,
            "nbf": now,
            "exp": now + 60,
            "jti": "jti-1",
            "sid": "sid-1",
            "typ": "access",
        },
        service.settings.private_key,
        algorithm=service.settings.algorithm,
        headers={"typ": "NOT-JWT", "kid": "v1"},
    )

    with pytest.raises(InvalidTokenError):
        service.verify_access_token(token)


def test_refresh_rotates_refresh_token() -> None:
    service = make_service()
    _, refresh_token = service.issue_tokens("user-123")

    new_access, new_refresh = service.refresh(refresh_token)

    assert new_refresh != refresh_token
    payload = service.verify_access_token(new_access)
    assert payload["sub"] == "user-123"


def test_refresh_reuse_triggers_replay_detection() -> None:
    service = make_service()
    _, refresh_token = service.issue_tokens("user-123")

    _, new_refresh = service.refresh(refresh_token)

    with pytest.raises(ReplayDetectedError):
        service.refresh(refresh_token)

    with pytest.raises(ReplayDetectedError):
        service.refresh(new_refresh)


def test_expired_refresh_token_is_rejected() -> None:
    service = make_service(refresh_ttl_seconds=-1)
    _, refresh_token = service.issue_tokens("user-123")

    with pytest.raises(ExpiredTokenError):
        service.refresh(refresh_token)


def test_logout_revokes_refresh_family() -> None:
    service = make_service()
    _, refresh_token = service.issue_tokens("user-123")

    service.logout(refresh_token)

    with pytest.raises(ReplayDetectedError):
        service.refresh(refresh_token)

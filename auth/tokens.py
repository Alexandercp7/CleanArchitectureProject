from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import uuid

import jwt

from domain.token import TokenPayload


class TokenError(Exception):
    pass


class InvalidTokenError(TokenError):
    pass


class ExpiredTokenError(TokenError):
    pass


class ReplayDetectedError(TokenError):
    pass


def create_access_token(user_id: str) -> str:
    return _create_token(user_id=user_id, token_type="access", ttl_env="AUTH_ACCESS_TTL_SECONDS", default_ttl=900)


def create_refresh_token(user_id: str) -> str:
    return _create_token(user_id=user_id, token_type="refresh", ttl_env="AUTH_REFRESH_TTL_SECONDS", default_ttl=1209600)


def decode_access_token(raw_token: str) -> TokenPayload:
    return _decode_token(raw_token=raw_token, expected_type="access")


def decode_refresh_token(raw_token: str) -> TokenPayload:
    return _decode_token(raw_token=raw_token, expected_type="refresh")


def _create_token(user_id: str, token_type: str, ttl_env: str, default_ttl: int) -> str:
    issued_at = datetime.now(tz=timezone.utc)
    expires_at = issued_at + timedelta(seconds=_read_ttl_seconds(ttl_env, default_ttl))
    payload = {
        "sub": user_id,
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(payload, _read_secret(), algorithm=_read_algorithm())


def _decode_token(raw_token: str, expected_type: str) -> TokenPayload:
    try:
        payload = jwt.decode(raw_token, _read_secret(), algorithms=[_read_algorithm()])
    except jwt.ExpiredSignatureError as error:
        raise ExpiredTokenError("Token is expired") from error
    except jwt.PyJWTError as error:
        raise InvalidTokenError("Token is invalid") from error

    token_type = str(payload.get("type", ""))
    if token_type != expected_type:
        raise InvalidTokenError(f"Expected token type '{expected_type}' but received '{token_type}'")

    subject = str(payload.get("sub", "")).strip()
    if not subject:
        raise InvalidTokenError("Token subject is missing")

    jti = str(payload.get("jti", "")).strip()
    if not jti:
        raise InvalidTokenError("Token identifier is missing")

    issued_at = _to_datetime(payload.get("iat"))
    expires_at = _to_datetime(payload.get("exp"))
    return TokenPayload(
        subject=subject,
        token_type=token_type,
        jti=jti,
        issued_at=issued_at,
        expires_at=expires_at,
    )


def _read_secret() -> str:
    secret = os.getenv("AUTH_JWT_SECRET", "dev-secret-change-me-please-use-32-bytes")
    if len(secret) < 16:
        raise TokenError("JWT secret is too short")
    return secret


def _read_algorithm() -> str:
    return os.getenv("AUTH_JWT_ALGORITHM", "HS256")


def _read_ttl_seconds(environment_name: str, default_ttl: int) -> int:
    raw_value = os.getenv(environment_name)
    return int(raw_value) if raw_value else default_ttl


def _to_datetime(raw_value: datetime | int | float | None) -> datetime:
    if isinstance(raw_value, datetime):
        if raw_value.tzinfo is None:
            return raw_value.replace(tzinfo=timezone.utc)
        return raw_value.astimezone(timezone.utc)
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value, tz=timezone.utc)
    raise TokenError("Token timestamp format is invalid")

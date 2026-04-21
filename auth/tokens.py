from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import os
import secrets
import time
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


@dataclass(frozen=True)
class TokenSettings:
    algorithm: str
    issuer: str
    audience: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int
    leeway_seconds: int
    private_key: str
    public_key: str
    key_id: str | None = None


@dataclass
class RefreshTokenRow:
    family_id: str
    user_id: str
    token_hash: str
    expires_at: int
    revoked_at: int | None = None


class InMemoryRefreshTokenStore:
    def __init__(self) -> None:
        self._rows: dict[str, RefreshTokenRow] = {}
        self._families: dict[str, set[str]] = {}

    def save(self, row: RefreshTokenRow) -> None:
        self._rows[row.token_hash] = row
        self._families.setdefault(row.family_id, set()).add(row.token_hash)

    def get(self, token_hash: str) -> RefreshTokenRow | None:
        return self._rows.get(token_hash)

    def revoke(self, token_hash: str) -> None:
        row = self._rows.get(token_hash)
        if row is not None and row.revoked_at is None:
            row.revoked_at = int(time.time())

    def revoke_family(self, family_id: str) -> None:
        for token_hash in self._families.get(family_id, set()):
            self.revoke(token_hash)


class TokenService:
    def __init__(self, settings: TokenSettings, store: InMemoryRefreshTokenStore) -> None:
        self.settings = settings
        self.store = store

    def issue_tokens(self, user_id: str, scopes: list[str] | tuple[str, ...] = ()) -> tuple[str, str]:
        now = int(time.time())
        family_id = secrets.token_urlsafe(24)
        access_token = self._encode_access_token(user_id, now, family_id, scopes)

        refresh_token = secrets.token_urlsafe(48)
        refresh_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
        row = RefreshTokenRow(
            family_id=family_id,
            user_id=user_id,
            token_hash=refresh_hash,
            expires_at=now + self.settings.refresh_ttl_seconds,
        )
        self.store.save(row)
        return access_token, refresh_token

    def verify_access_token(self, token: str) -> dict:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as error:
            raise InvalidTokenError("Malformed JWT header") from error

        if header.get("typ") != "JWT":
            raise InvalidTokenError("Invalid JWT header type")
        if header.get("alg") != self.settings.algorithm:
            raise InvalidTokenError("Unexpected signing algorithm")
        if self.settings.key_id and header.get("kid") != self.settings.key_id:
            raise InvalidTokenError("Unexpected key identifier")

        try:
            payload = jwt.decode(
                token,
                self.settings.public_key,
                algorithms=[self.settings.algorithm],
                audience=self.settings.audience,
                issuer=self.settings.issuer,
                leeway=self.settings.leeway_seconds,
                options={"require": ["exp", "iat", "nbf", "iss", "aud", "sub", "jti", "sid", "typ"]},
            )
        except jwt.ExpiredSignatureError as error:
            raise ExpiredTokenError("Access token expired") from error
        except jwt.PyJWTError as error:
            raise InvalidTokenError("Invalid access token") from error

        if payload.get("typ") != "access":
            raise InvalidTokenError("Invalid payload type")
        return payload

    def refresh(self, refresh_token: str, scopes: list[str] | tuple[str, ...] = ()) -> tuple[str, str]:
        now = int(time.time())
        token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
        row = self.store.get(token_hash)

        if row is None:
            raise InvalidTokenError("Invalid refresh token")
        if row.revoked_at is not None:
            self.store.revoke_family(row.family_id)
            raise ReplayDetectedError("Refresh token replay detected")
        if row.expires_at <= now:
            self.store.revoke(token_hash)
            raise ExpiredTokenError("Refresh token expired")

        self.store.revoke(token_hash)
        new_refresh_token = secrets.token_urlsafe(48)
        new_hash = hashlib.sha256(new_refresh_token.encode("utf-8")).hexdigest()
        self.store.save(
            RefreshTokenRow(
                family_id=row.family_id,
                user_id=row.user_id,
                token_hash=new_hash,
                expires_at=now + self.settings.refresh_ttl_seconds,
            )
        )
        access_token = self._encode_access_token(row.user_id, now, row.family_id, scopes)
        return access_token, new_refresh_token

    def logout(self, refresh_token: str) -> None:
        token_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
        row = self.store.get(token_hash)
        if row is not None:
            self.store.revoke_family(row.family_id)

    def _encode_access_token(self, user_id: str, now: int, family_id: str, scopes: list[str] | tuple[str, ...]) -> str:
        payload = {
            "iss": self.settings.issuer,
            "sub": user_id,
            "aud": self.settings.audience,
            "iat": now,
            "nbf": now,
            "exp": now + self.settings.access_ttl_seconds,
            "jti": secrets.token_urlsafe(16),
            "sid": family_id,
            "scope": " ".join(scopes),
            "typ": "access",
            "type": "access",
        }
        headers = {"typ": "JWT"}
        if self.settings.key_id:
            headers["kid"] = self.settings.key_id
        return jwt.encode(payload, self.settings.private_key, algorithm=self.settings.algorithm, headers=headers)

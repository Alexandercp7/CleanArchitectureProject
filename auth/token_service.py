from __future__ import annotations

from dataclasses import dataclass
import hashlib
import secrets
import time

import jwt

from auth.tokens import ExpiredTokenError, InvalidTokenError, ReplayDetectedError


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

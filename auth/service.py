from __future__ import annotations

import logging

from auth.password import hash_password, verify_password
from auth.password_rules import validate
from auth.pii import obscure_email
from auth.tokens import TokenError, create_access_token, create_refresh_token, decode_refresh_token
from auth.user_repository import UserRepository
from domain.token import AccessTokenResult, TokenPair
from domain.user import User


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._logger = logging.getLogger(__name__)
        self._dummy_password_hash = hash_password("DummyPassword123")

    async def register(self, email: str, password: str) -> User:
        validate(password)
        existing_user = await self._repo.get_by_email(email)
        if existing_user is not None:
            raise AuthError("Email is already registered")
        hashed_password = hash_password(password)
        return await self._repo.create(email=email, hashed_password=hashed_password)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._repo.get_by_email(email)
        hashed_password = user.hashed_password if user is not None else self._dummy_password_hash

        # Why: always run bcrypt verification to reduce user enumeration via timing.
        is_valid_password = verify_password(password, hashed_password)
        if user is None or not is_valid_password:
            context = obscure_email(email)
            self._logger.warning(
                "Login failed for email hash",
                extra={"email_domain": context.domain, "email_hash": context.short_hash},
            )
            raise AuthError("Invalid credentials")

        if not user.is_active:
            raise AuthError("User is inactive")

        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh_access_token(self, raw_refresh_token: str) -> AccessTokenResult:
        try:
            payload = decode_refresh_token(raw_refresh_token)
        except TokenError as error:
            raise AuthError("Refresh token is invalid") from error
        return AccessTokenResult(access_token=create_access_token(payload.subject))

    async def get_active_user(self, user_id: str) -> User:
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise AuthError("User not found")
        if not user.is_active:
            raise AuthError("User is inactive")
        return user

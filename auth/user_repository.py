from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.user import User
from infrastructure.persistence.models.user_model import UserBase, UserRow


class UserRepositoryError(Exception):
    pass


_Base = UserBase


SessionFactory = Callable[[], AsyncSession]


class UserRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def create(self, email: str, hashed_password: str) -> User:
        normalized_email = email.strip().lower()
        now = datetime.now(tz=timezone.utc)
        new_row = UserRow(
            id=str(uuid4()),
            email=normalized_email,
            hashed_password=hashed_password,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session:
            session.add(new_row)
            await session.commit()
            await session.refresh(new_row)
        return self._to_user(new_row)

    async def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        statement = select(UserRow).where(UserRow.email == normalized_email)
        async with self._session_factory() as session:
            result = await session.execute(statement)
            row = result.scalar_one_or_none()
        return None if row is None else self._to_user(row)

    async def get_by_id(self, user_id: str) -> User | None:
        statement = select(UserRow).where(UserRow.id == user_id)
        async with self._session_factory() as session:
            result = await session.execute(statement)
            row = result.scalar_one_or_none()
        return None if row is None else self._to_user(row)

    def _to_user(self, row: UserRow) -> User:
        return User(
            id=row.id,
            email=row.email,
            hashed_password=row.hashed_password,
            role="user",
            is_active=row.is_active,
        )

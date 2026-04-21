from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.user import User


class UserRepositoryError(Exception):
    pass


class _Base(DeclarativeBase):
    pass


class UserRow(_Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


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
            is_active=row.is_active,
        )

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from alerts.repository import _Base as AlertBase
from auth.user_repository import _Base as UserBase


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(UserBase.metadata.create_all)
        await connection.run_sync(AlertBase.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()

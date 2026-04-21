import pytest

from auth.user_repository import UserRepository


@pytest.mark.asyncio
async def test_create_and_get_user(session_factory) -> None:
    repo = UserRepository(session_factory)

    created = await repo.create(email="user@example.com", hashed_password="hash")
    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.email == "user@example.com"

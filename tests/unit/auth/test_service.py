import pytest

from auth.service import AuthError, AuthService
from domain.user import User


class FakeRepo:
    def __init__(self) -> None:
        self.users_by_email: dict[str, User] = {}

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(id="u1", email=email.lower(), hashed_password=hashed_password, is_active=True)
        self.users_by_email[email.lower()] = user
        return user

    async def get_by_email(self, email: str) -> User | None:
        return self.users_by_email.get(email.lower())

    async def get_by_id(self, user_id: str) -> User | None:
        for user in self.users_by_email.values():
            if user.id == user_id:
                return user
        return None


@pytest.mark.asyncio
async def test_register_creates_user() -> None:
    service = AuthService(FakeRepo())
    user = await service.register("test@example.com", "Password1")
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_login_returns_tokens() -> None:
    repo = FakeRepo()
    service = AuthService(repo)
    await service.register("test@example.com", "Password1")

    token_pair = await service.login("test@example.com", "Password1")

    assert token_pair.access_token
    assert token_pair.refresh_token


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    repo = FakeRepo()
    service = AuthService(repo)
    await service.register("test@example.com", "Password1")

    with pytest.raises(AuthError):
        await service.login("test@example.com", "wrong")

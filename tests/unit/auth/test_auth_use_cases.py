from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest
from ssah.auth.application.use_cases.login_user import LoginUser
from ssah.auth.application.use_cases.register_user import RegisterUser
from ssah.auth.application.use_cases.request_password_reset import RequestPasswordReset
from ssah.auth.application.use_cases.reset_password import ResetPassword
from ssah.auth.domain.entities.auth_token import StoredToken
from ssah.auth.domain.entities.user import User
from ssah.auth.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError


class FakeUserRepository:
    def __init__(self, users: list[User] | None = None):
        self.users = {user.email: user for user in users or []}

    async def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    async def get_by_id(self, user_id: str) -> User | None:
        return next((user for user in self.users.values() if user.id == user_id), None)

    async def create(self, user: User) -> User:
        self.users[user.email] = user
        return user

    async def update_password(self, user_id: str, hashed_password: str) -> None:
        user = await self.get_by_id(user_id)
        assert user is not None
        user.hashed_password = hashed_password


class FakePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        return hashed_password == self.hash(password)


class FakeTokenService:
    def create_access_token(self, subject: str) -> str:
        return f"access:{subject}"

    def create_refresh_token(self, subject: str):
        return (
            f"refresh:{subject}",
            "refresh-id",
            datetime.now(UTC) + timedelta(days=7),
        )

    def fingerprint(self, token: str) -> str:
        return sha256(token.encode()).hexdigest()


class FakeTokenRepository:
    def __init__(self):
        self.refresh_tokens: dict[str, StoredToken] = {}
        self.reset_tokens: dict[str, StoredToken] = {}
        self.revoked_users: list[str] = []

    async def save_refresh_token(self, user_id, token_id, token_hash, expires_at) -> None:
        self.refresh_tokens[token_id] = StoredToken(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    async def save_password_reset_token(self, user_id, token_id, token_hash, expires_at) -> None:
        self.reset_tokens[token_hash] = StoredToken(
            id=token_id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    async def get_active_password_reset_token(self, token_hash):
        return self.reset_tokens.get(token_hash)

    async def consume_password_reset_token(self, token_id) -> None:
        self.reset_tokens = {
            key: value for key, value in self.reset_tokens.items() if value.id != token_id
        }

    async def revoke_password_reset_tokens(self, user_id) -> None:
        self.reset_tokens = {
            key: value for key, value in self.reset_tokens.items() if value.user_id != user_id
        }

    async def revoke_all_refresh_tokens(self, user_id) -> None:
        self.revoked_users.append(user_id)


@pytest.mark.asyncio
async def test_register_user_normalizes_email_and_hashes_password() -> None:
    repository = FakeUserRepository()

    user = await RegisterUser(repository, FakePasswordHasher()).execute(
        "Ana Pérez", "  ANA@EXAMPLE.COM ", "secret123"
    )

    assert user.email == "ana@example.com"
    assert user.hashed_password == "hashed:secret123"
    assert await repository.get_by_email("ana@example.com") == user


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email() -> None:
    existing = User("user-id", "Ana", "ana@example.com", "hashed:secret123")
    repository = FakeUserRepository([existing])

    with pytest.raises(UserAlreadyExistsError):
        await RegisterUser(repository, FakePasswordHasher()).execute(
            "Otra Ana", "ANA@example.com", "secret123"
        )


@pytest.mark.asyncio
async def test_login_returns_and_persists_token_pair() -> None:
    user = User("user-id", "Ana", "ana@example.com", "hashed:secret123")
    token_repository = FakeTokenRepository()

    result = await LoginUser(
        FakeUserRepository([user]),
        FakePasswordHasher(),
        FakeTokenService(),
        token_repository,
    ).execute("ana@example.com", "secret123")

    assert result["access_token"] == "access:user-id"
    assert result["refresh_token"] == "refresh:user-id"
    assert "refresh-id" in token_repository.refresh_tokens


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    user = User("user-id", "Ana", "ana@example.com", "hashed:secret123")

    with pytest.raises(InvalidCredentialsError):
        await LoginUser(
            FakeUserRepository([user]),
            FakePasswordHasher(),
            FakeTokenService(),
            FakeTokenRepository(),
        ).execute("ana@example.com", "incorrecta")


@pytest.mark.asyncio
async def test_password_reset_changes_password_and_revokes_sessions() -> None:
    user = User("user-id", "Ana", "ana@example.com", "hashed:old-secret")
    users = FakeUserRepository([user])
    tokens = FakeTokenRepository()
    token_service = FakeTokenService()
    raw_token = await RequestPasswordReset(users, tokens, token_service, 30).execute(user.email)

    assert raw_token is not None
    await ResetPassword(users, tokens, token_service, FakePasswordHasher()).execute(
        raw_token, "new-secret"
    )

    assert user.hashed_password == "hashed:new-secret"
    assert tokens.reset_tokens == {}
    assert tokens.revoked_users == [user.id]

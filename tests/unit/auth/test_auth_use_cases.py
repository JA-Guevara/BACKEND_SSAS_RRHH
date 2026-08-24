from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

from ssas.auth.application.use_cases.login_user import LoginUser
from ssas.auth.application.use_cases.request_password_reset import RequestPasswordReset
from ssas.auth.application.use_cases.reset_password import ResetPassword
from ssas.auth.domain.entities.auth_token import StoredToken
from ssas.auth.domain.entities.user import User
from ssas.auth.domain.exceptions import InvalidCredentialsError

EMPRESA_ID = "empresa-id"
EMPRESA_SLUG = "empresa-a"


class FakeUserRepository:
    def __init__(self, users: list[User] | None = None):
        self.users = {user.id: user for user in users or []}

    async def get_by_email(self, email: str, empresa_id: str) -> User | None:
        return next(
            (
                user
                for user in self.users.values()
                if user.email == email and user.empresa_id == empresa_id
            ),
            None,
        )

    async def get_by_username(self, username: str, empresa_id: str) -> User | None:
        return next(
            (
                user
                for user in self.users.values()
                if user.username == username and user.empresa_id == empresa_id
            ),
            None,
        )

    async def get_by_login(self, login: str, empresa_slug: str) -> User | None:
        if empresa_slug != EMPRESA_SLUG:
            return None
        return next(
            (
                user
                for user in self.users.values()
                if user.email == login or user.username == login
            ),
            None,
        )

    async def get_by_id(self, user_id: str, empresa_id: str) -> User | None:
        user = self.users.get(user_id)
        return user if user and user.empresa_id == empresa_id else None

    async def update_password(
        self, user_id: str, empresa_id: str, hashed_password: str
    ) -> None:
        user = await self.get_by_id(user_id, empresa_id)
        assert user is not None
        user.hashed_password = hashed_password


class FakePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        return hashed_password == self.hash(password)


class FakeTokenService:
    def create_access_token(
        self, subject: str, empresa_id: str, roles: list[str] | None = None
    ) -> str:
        return f"access:{empresa_id}:{subject}"

    def create_refresh_token(self, subject: str, empresa_id: str):
        return (
            f"refresh:{empresa_id}:{subject}",
            "refresh-id",
            datetime.now(UTC) + timedelta(days=7),
        )

    def fingerprint(self, token: str) -> str:
        return sha256(token.encode()).hexdigest()


class FakeTokenRepository:
    def __init__(self):
        self.refresh_tokens: dict[str, StoredToken] = {}
        self.reset_tokens: dict[str, StoredToken] = {}
        self.revoked_users: list[tuple[str, str]] = []

    async def save_refresh_token(
        self, user_id, empresa_id, token_id, token_hash, expires_at
    ) -> None:
        self.refresh_tokens[token_id] = StoredToken(
            id=token_id,
            user_id=user_id,
            empresa_id=empresa_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    async def save_password_reset_token(
        self, user_id, empresa_id, token_id, token_hash, expires_at
    ) -> None:
        self.reset_tokens[token_hash] = StoredToken(
            id=token_id,
            user_id=user_id,
            empresa_id=empresa_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    async def get_active_password_reset_token(self, token_hash):
        return self.reset_tokens.get(token_hash)

    async def consume_password_reset_token(self, token_id) -> None:
        self.reset_tokens = {
            key: value for key, value in self.reset_tokens.items() if value.id != token_id
        }

    async def revoke_password_reset_tokens(self, user_id, empresa_id) -> None:
        self.reset_tokens = {
            key: value
            for key, value in self.reset_tokens.items()
            if (value.user_id, value.empresa_id) != (user_id, empresa_id)
        }

    async def revoke_all_refresh_tokens(self, user_id, empresa_id) -> None:
        self.revoked_users.append((user_id, empresa_id))


def make_user() -> User:
    return User(
        id="user-id",
        name="Ana",
        email="ana@example.com",
        username="ana",
        hashed_password="hashed:secret123",
        empresa_id=EMPRESA_ID,
        roles=["Administrador de Empresa"],
    )


@pytest.mark.asyncio
async def test_login_returns_and_persists_tenant_token_pair() -> None:
    user = make_user()
    token_repository = FakeTokenRepository()

    result = await LoginUser(
        FakeUserRepository([user]),
        FakePasswordHasher(),
        FakeTokenService(),
        token_repository,
    ).execute(password="secret123", email=user.email, empresa_slug=EMPRESA_SLUG)

    assert result["access_token"] == f"access:{EMPRESA_ID}:user-id"
    assert result["refresh_token"] == f"refresh:{EMPRESA_ID}:user-id"
    assert token_repository.refresh_tokens["refresh-id"].empresa_id == EMPRESA_ID


@pytest.mark.asyncio
async def test_login_does_not_cross_company_boundary() -> None:
    user = make_user()

    with pytest.raises(InvalidCredentialsError):
        await LoginUser(
            FakeUserRepository([user]),
            FakePasswordHasher(),
            FakeTokenService(),
            FakeTokenRepository(),
        ).execute(password="secret123", email=user.email, empresa_slug="otra-empresa")


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    user = make_user()

    with pytest.raises(InvalidCredentialsError):
        await LoginUser(
            FakeUserRepository([user]),
            FakePasswordHasher(),
            FakeTokenService(),
            FakeTokenRepository(),
        ).execute(password="incorrecta", email=user.email, empresa_slug=EMPRESA_SLUG)


@pytest.mark.asyncio
async def test_password_reset_is_scoped_to_company_and_revokes_sessions() -> None:
    user = make_user()
    users = FakeUserRepository([user])
    tokens = FakeTokenRepository()
    token_service = FakeTokenService()
    raw_token = await RequestPasswordReset(users, tokens, token_service, 30).execute(
        user.email, EMPRESA_SLUG
    )

    assert raw_token is not None
    await ResetPassword(users, tokens, token_service, FakePasswordHasher()).execute(
        raw_token, "new-secret"
    )

    assert user.hashed_password == "hashed:new-secret"
    assert tokens.reset_tokens == {}
    assert tokens.revoked_users == [(user.id, EMPRESA_ID)]

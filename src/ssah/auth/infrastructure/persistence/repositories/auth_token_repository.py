from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssah.auth.domain.entities.auth_token import StoredToken
from ssah.auth.infrastructure.persistence.models.password_reset_token import PasswordResetTokenModel
from ssah.auth.infrastructure.persistence.models.refresh_token import RefreshTokenModel
from ssah.auth.ports.outgoing.auth_token_repository import AuthTokenRepository


class SqlAlchemyAuthTokenRepository(AuthTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_refresh_token(
        self,
        user_id: str,
        empresa_id: str,
        token_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        self.session.add(
            RefreshTokenModel(
                id=token_id,
                empresa_id=empresa_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await self.session.flush()

    async def get_active_refresh_token(self, token_id: str) -> StoredToken | None:
        result = await self.session.execute(
            select(RefreshTokenModel)
            .where(
                RefreshTokenModel.id == token_id,
                RefreshTokenModel.revoked_at.is_(None),
                RefreshTokenModel.expires_at > datetime.now(UTC),
            )
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        return self._refresh_to_entity(model) if model else None

    async def revoke_refresh_token(self, token_id: str) -> None:
        await self.session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.id == token_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self.session.flush()

    async def revoke_all_refresh_tokens(self, user_id: str) -> None:
        await self.session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id, RefreshTokenModel.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self.session.flush()

    async def save_password_reset_token(
        self,
        user_id: str,
        empresa_id: str,
        token_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        self.session.add(
            PasswordResetTokenModel(
                id=token_id,
                empresa_id=empresa_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await self.session.flush()

    async def get_active_password_reset_token(self, token_hash: str) -> StoredToken | None:
        result = await self.session.execute(
            select(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.token_hash == token_hash,
                PasswordResetTokenModel.used_at.is_(None),
                PasswordResetTokenModel.expires_at > datetime.now(UTC),
            )
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        return self._reset_to_entity(model) if model else None

    async def consume_password_reset_token(self, token_id: str) -> None:
        await self.session.execute(
            update(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.id == token_id)
            .values(used_at=datetime.now(UTC))
        )
        await self.session.flush()

    async def revoke_password_reset_tokens(self, user_id: str) -> None:
        await self.session.execute(
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.user_id == user_id,
                PasswordResetTokenModel.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        )
        await self.session.flush()

    @staticmethod
    def _refresh_to_entity(model: RefreshTokenModel) -> StoredToken:
        return StoredToken(
            id=model.id,
            user_id=model.user_id,
            empresa_id=model.empresa_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            revoked_at=model.revoked_at,
        )

    @staticmethod
    def _reset_to_entity(model: PasswordResetTokenModel) -> StoredToken:
        return StoredToken(
            id=model.id,
            user_id=model.user_id,
            empresa_id=model.empresa_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            revoked_at=model.used_at,
        )
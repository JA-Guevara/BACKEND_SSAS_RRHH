from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ssas.auth.domain.entities.user import User
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.auth.ports.outgoing.user_repository import UserRepository
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str, empresa_id: str) -> User | None:
        result = await self.session.execute(
            self._base_query().where(
                UserModel.empresa_id == empresa_id,
                func.lower(UserModel.email) == email.strip().lower(),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str, empresa_id: str) -> User | None:
        result = await self.session.execute(
            self._base_query().where(
                UserModel.empresa_id == empresa_id,
                func.lower(UserModel.username) == username.strip().lower(),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_login(self, login: str, empresa_slug: str) -> User | None:
        normalized_login = login.strip().lower()
        identifier_filter = (
            func.lower(UserModel.email) == normalized_login
            if "@" in normalized_login
            else func.lower(UserModel.username) == normalized_login
        )
        result = await self.session.execute(
            self._base_query()
            .join(EmpresaModel, EmpresaModel.id == UserModel.empresa_id)
            .where(
                func.lower(EmpresaModel.slug) == empresa_slug.strip().lower(),
                EmpresaModel.activo.is_(True),
                identifier_filter,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, user_id: str, empresa_id: str) -> User | None:
        result = await self.session.execute(
            self._base_query().where(
                UserModel.id == user_id,
                UserModel.empresa_id == empresa_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update_password(
        self, user_id: str, empresa_id: str, hashed_password: str, must_change: bool = False
    ) -> None:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.empresa_id == empresa_id)
            .values(hashed_password=hashed_password, debe_cambiar_password=must_change)
        )
        await self.session.flush()

    async def record_failed_login(
        self, user_id: str, empresa_id: str, max_attempts: int, lock_minutes: int
    ) -> None:
        now = datetime.now(UTC)
        next_attempts = case(
            (
                UserModel.bloqueado_hasta.is_not(None)
                & (UserModel.bloqueado_hasta <= now),
                1,
            ),
            else_=UserModel.intentos_fallidos + 1,
        )
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.empresa_id == empresa_id)
            .values(
                intentos_fallidos=next_attempts,
                ultimo_intento_fallido=now,
                bloqueado_hasta=case(
                    (next_attempts >= max_attempts, now + timedelta(minutes=lock_minutes)),
                    else_=UserModel.bloqueado_hasta,
                ),
            )
        )
        await self.session.flush()

    async def record_successful_login(self, user_id: str, empresa_id: str) -> None:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.empresa_id == empresa_id)
            .values(
                intentos_fallidos=0,
                bloqueado_hasta=None,
                ultimo_intento_fallido=None,
                ultimo_acceso=datetime.now(UTC),
            )
        )
        await self.session.flush()

    async def mark_email_verified(self, user_id: str, empresa_id: str) -> None:
        await self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.empresa_id == empresa_id)
            .values(email_verified=True)
        )
        await self.session.flush()

    @staticmethod
    def _base_query():
        return select(UserModel).options(
            selectinload(UserModel.empresa),
            selectinload(UserModel.roles),
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        roles = [role.name for role in model.roles if role.is_active]
        return User(
            id=model.id,
            empresa_id=model.empresa_id,
            name=model.name,
            email=model.email,
            username=model.username,
            hashed_password=model.hashed_password,
            roles=roles,
            empresa_is_active=bool(model.empresa and model.empresa.activo),
            is_active=model.is_active,
            email_verified=model.email_verified,
            must_change_password=model.debe_cambiar_password,
            failed_login_attempts=model.intentos_fallidos,
            locked_until=model.bloqueado_hasta,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

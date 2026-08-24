from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ssah.auth.domain.entities.user import User
from ssah.auth.domain.exceptions import UserAlreadyExistsError
from ssah.auth.infrastructure.persistence.models.user import UserModel
from ssah.auth.ports.outgoing.user_repository import UserRepository


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            self._base_query().where(func.lower(UserModel.email) == email.strip().lower())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            self._base_query().where(func.lower(UserModel.username) == username.strip().lower())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(self._base_query().where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, user: User) -> User:
        self.session.add(
            UserModel(
                id=user.id,
                empresa_id=user.empresa_id,
                name=user.name,
                email=user.email,
                username=user.username or user.email,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                email_verified=user.email_verified,
            )
        )
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            raise UserAlreadyExistsError("El usuario ya existe") from exc
        return user

    async def update_password(self, user_id: str, hashed_password: str) -> None:
        await self.session.execute(
            update(UserModel).where(UserModel.id == user_id).values(hashed_password=hashed_password)
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
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
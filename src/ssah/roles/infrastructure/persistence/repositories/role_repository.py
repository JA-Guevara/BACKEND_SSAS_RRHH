from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ssah.roles.domain.entities.role import Role
from ssah.roles.infrastructure.persistence.models.role import RoleModel


class SqlAlchemyRoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, role: Role) -> Role:
        model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
        )
        self.session.add(model)
        await self.session.commit()
        return role

    async def list(self) -> list[Role]:
        result = await self.session.execute(
            select(RoleModel).options(selectinload(RoleModel.permissions)).order_by(RoleModel.name)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def get_by_id(self, role_id: str) -> Role | None:
        result = await self.session.execute(
            select(RoleModel)
            .options(selectinload(RoleModel.permissions))
            .where(RoleModel.id == role_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(RoleModel).where(RoleModel.name == name))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, role_id: str, values: dict) -> Role:
        model = await self.session.get(RoleModel, role_id)
        for field, value in values.items():
            setattr(model, field, value)
        await self.session.commit()
        return self._to_entity(model)

    async def delete(self, role_id: str) -> None:
        await self.session.execute(delete(RoleModel).where(RoleModel.id == role_id))
        await self.session.commit()

    async def assign_permissions(self, role_id: str, permissions: list) -> Role:
        model = await self.session.get(RoleModel, role_id, options=[selectinload(RoleModel.permissions)])
        model.permissions = [
            permission_model
            for permission_model in permissions
        ]
        await self.session.commit()
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: RoleModel) -> Role:
        from ssah.roles.infrastructure.persistence.repositories.permission_repository import (
            PermissionRepository,
        )

        return Role(
            id=model.id,
            name=model.name,
            description=model.description,
            is_active=model.is_active,
            permissions=[PermissionRepository.to_entity(permission) for permission in model.permissions],
        )
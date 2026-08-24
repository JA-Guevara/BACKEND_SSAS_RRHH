from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssah.roles.domain.entities.permission import Permission
from ssah.roles.infrastructure.persistence.models.permission import PermissionModel


class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_ids(self, permission_ids: list[str]) -> list[PermissionModel]:
        result = await self.session.execute(
            select(PermissionModel).where(PermissionModel.id.in_(permission_ids))
        )
        return list(result.scalars().all())

    @staticmethod
    def to_entity(model: PermissionModel) -> Permission:
        return Permission(
            id=model.id,
            name=model.name,
            resource=model.resource,
            action=model.action,
            description=model.description,
        )
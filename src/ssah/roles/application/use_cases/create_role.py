from uuid import uuid4

from ssah.roles.domain.entities.role import Role
from ssah.roles.domain.exceptions import DuplicateRoleError


class CreateRole:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, name: str, description: str | None = None):
        if await self.repository.get_by_name(name):
            raise DuplicateRoleError("El rol ya existe")
        role = Role(id=str(uuid4()), name=name, description=description)
        return await self.repository.create(role)
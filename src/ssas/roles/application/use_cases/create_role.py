from uuid import uuid4

from ssas.roles.domain.entities.role import Role
from ssas.roles.domain.exceptions import DuplicateRoleError


class CreateRole:
    def __init__(self, repository):
        self.repository = repository

    async def execute(
        self,
        empresa_id: str,
        name: str,
        codigo: str,
        description: str | None = None,
    ):
        normalized_code = codigo.strip().upper()
        if await self.repository.get_by_name(name) or await self.repository.get_by_code(
            normalized_code
        ):
            raise DuplicateRoleError("El rol ya existe")
        role = Role(
            id=str(uuid4()),
            empresa_id=empresa_id,
            name=name.strip(),
            codigo=normalized_code,
            description=description.strip() if description else None,
        )
        return await self.repository.create(role)

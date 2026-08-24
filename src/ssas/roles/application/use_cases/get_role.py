from ssas.roles.domain.exceptions import RoleNotFoundError


class GetRole:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, role_id: str):
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError("Rol no encontrado")
        return role
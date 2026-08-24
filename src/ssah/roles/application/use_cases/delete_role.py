from ssah.roles.domain.exceptions import RoleNotFoundError


class DeleteRole:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, role_id: str):
        if not await self.repository.get_by_id(role_id):
            raise RoleNotFoundError("Rol no encontrado")
        await self.repository.delete(role_id)
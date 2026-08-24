from ssah.roles.domain.exceptions import DuplicateRoleError, RoleNotFoundError


class UpdateRole:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, role_id: str, values: dict):
        role = await self.repository.get_by_id(role_id)
        if not role:
            raise RoleNotFoundError("Rol no encontrado")
        name = values.get("name")
        if name and name != role.name and await self.repository.get_by_name(name):
            raise DuplicateRoleError("El rol ya existe")
        return await self.repository.update(role_id, values)
from ssas.roles.domain.exceptions import PermissionNotFoundError, RoleNotFoundError


class AssignPermissions:
    def __init__(self, role_repository, permission_repository):
        self.role_repository = role_repository
        self.permission_repository = permission_repository

    async def execute(self, role_id: str, permission_ids: list[str]):
        if not await self.role_repository.get_by_id(role_id):
            raise RoleNotFoundError("Rol no encontrado")
        permissions = await self.permission_repository.get_by_ids(permission_ids)
        if len(permissions) != len(set(permission_ids)):
            raise PermissionNotFoundError("Una o más permisos no existen")
        return await self.role_repository.assign_permissions(role_id, permissions)
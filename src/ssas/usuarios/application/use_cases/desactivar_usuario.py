from ssas.usuarios.domain.entities.usuario import Usuario
from ssas.usuarios.domain.exceptions import LastAdminCannotBeDisabledError, UsuarioNotFoundError
from ssas.usuarios.ports.outgoing.usuario_repository import UsuarioRepository


class DesactivarUsuario:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    async def execute(self, user_id: str, empresa_id: str) -> Usuario:
        if await self.usuario_repository.get_by_id(user_id, empresa_id) is None:
            raise UsuarioNotFoundError("Usuario no encontrado")
        if await self.usuario_repository.user_has_admin_role(user_id, empresa_id):
            active_admins = await self.usuario_repository.count_active_admins(empresa_id)
            if active_admins <= 1:
                raise LastAdminCannotBeDisabledError(
                    "No se puede desactivar al último administrador activo de la empresa"
                )
        return await self.usuario_repository.deactivate_usuario(user_id, empresa_id)

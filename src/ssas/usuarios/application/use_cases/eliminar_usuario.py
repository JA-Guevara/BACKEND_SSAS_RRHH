from ssas.auth.ports.outgoing.auth_token_repository import AuthTokenRepository
from ssas.usuarios.domain.entities.usuario import Usuario
from ssas.usuarios.domain.exceptions import (
    CannotDeleteSelfError,
    LastAdminCannotBeDisabledError,
    UsuarioNotFoundError,
)
from ssas.usuarios.ports.outgoing.usuario_repository import UsuarioRepository


class EliminarUsuario:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
        token_repository: AuthTokenRepository,
    ):
        self.usuario_repository = usuario_repository
        self.token_repository = token_repository

    async def execute(
        self,
        user_id: str,
        empresa_id: str | None,
        actor_id: str,
    ) -> Usuario:
        if user_id == actor_id:
            raise CannotDeleteSelfError("No puede eliminar su propia cuenta")
        user = await self.usuario_repository.get_by_id(user_id, empresa_id)
        if user is None:
            raise UsuarioNotFoundError("Usuario no encontrado")
        if (
            await self.usuario_repository.user_has_admin_role(user_id, empresa_id)
            and await self.usuario_repository.count_active_admins(empresa_id) <= 1
        ):
            raise LastAdminCannotBeDisabledError(
                "No se puede eliminar al último administrador activo del alcance"
            )
        deleted = await self.usuario_repository.soft_delete_usuario(
            user_id, empresa_id, actor_id
        )
        await self.token_repository.revoke_all_refresh_tokens(user_id, empresa_id)
        await self.token_repository.revoke_password_reset_tokens(user_id, empresa_id)
        await self.token_repository.revoke_email_verification_tokens(user_id, empresa_id)
        return deleted

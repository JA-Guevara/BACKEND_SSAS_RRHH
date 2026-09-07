from ssas.usuarios.domain.entities.usuario import Usuario
from ssas.usuarios.domain.exceptions import UsuarioNotDeletedError, UsuarioNotFoundError
from ssas.usuarios.ports.outgoing.usuario_repository import UsuarioRepository


class RestaurarUsuario:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    async def execute(self, user_id: str, empresa_id: str | None) -> Usuario:
        user = await self.usuario_repository.get_by_id(
            user_id, empresa_id, include_deleted=True
        )
        if user is None:
            raise UsuarioNotFoundError("Usuario no encontrado")
        if not user.is_deleted:
            raise UsuarioNotDeletedError("El usuario no está eliminado")
        return await self.usuario_repository.restore_usuario(user_id, empresa_id)

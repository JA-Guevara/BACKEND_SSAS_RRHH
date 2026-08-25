from ssas.usuarios.domain.entities.usuario import Usuario
from ssas.usuarios.domain.exceptions import UsuarioNotFoundError
from ssas.usuarios.ports.outgoing.usuario_repository import UsuarioRepository


class ActivarUsuario:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    async def execute(self, user_id: str, empresa_id: str) -> Usuario:
        if await self.usuario_repository.get_by_id(user_id, empresa_id) is None:
            raise UsuarioNotFoundError("Usuario no encontrado")
        return await self.usuario_repository.activate_usuario(user_id, empresa_id)

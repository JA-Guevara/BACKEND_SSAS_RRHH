from ssas.usuarios.domain.exceptions import UsuarioNotFoundError


class DesbloquearUsuario:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, user_id: str, empresa_id: str):
        if not await self.repository.get_by_id(user_id, empresa_id):
            raise UsuarioNotFoundError("Usuario no encontrado")
        return await self.repository.unlock_usuario(user_id, empresa_id)

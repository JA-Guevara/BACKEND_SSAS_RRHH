from ssas.usuarios.domain.exceptions import UsuarioNotFoundError


class ObtenerUsuario:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, user_id: str, empresa_id: str):
        user = await self.repository.get_by_id(user_id, empresa_id)
        if not user:
            raise UsuarioNotFoundError("Usuario no encontrado")
        return user

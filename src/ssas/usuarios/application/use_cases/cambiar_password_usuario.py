from ssas.auth.domain.password_policy import validate_password
from ssas.usuarios.domain.exceptions import UsuarioNotFoundError


class CambiarPasswordUsuario:
    def __init__(self, repository, token_repository, password_hasher):
        self.repository = repository
        self.token_repository = token_repository
        self.password_hasher = password_hasher

    async def execute(self, user_id: str, empresa_id: str, new_password: str, must_change: bool = True):
        user = await self.repository.get_by_id(user_id, empresa_id)
        if not user:
            raise UsuarioNotFoundError("Usuario no encontrado")
        validate_password(new_password, user.username, user.email)
        updated = await self.repository.set_password(user_id, empresa_id, self.password_hasher.hash(new_password), must_change)
        await self.token_repository.revoke_all_refresh_tokens(user_id, empresa_id)
        return updated

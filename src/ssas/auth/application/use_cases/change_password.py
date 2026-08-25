from ssas.auth.domain.exceptions import InvalidPasswordError, UserNotFoundError
from ssas.auth.domain.password_policy import validate_password


class ChangePassword:
    def __init__(self, user_repository, token_repository, password_hasher):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.password_hasher = password_hasher

    async def execute(self, user_id: str, empresa_id: str, current_password: str, new_password: str) -> None:
        user = await self.user_repository.get_by_id(user_id, empresa_id)
        if not user:
            raise UserNotFoundError("Usuario no encontrado")
        if not self.password_hasher.verify(current_password, user.hashed_password):
            raise InvalidPasswordError("La contraseña actual es incorrecta")
        if self.password_hasher.verify(new_password, user.hashed_password):
            raise InvalidPasswordError("La contraseña nueva debe ser diferente a la actual")
        validate_password(new_password, user.username, user.email)
        await self.user_repository.update_password(user_id, empresa_id, self.password_hasher.hash(new_password), False)
        await self.token_repository.revoke_all_refresh_tokens(user_id, empresa_id)

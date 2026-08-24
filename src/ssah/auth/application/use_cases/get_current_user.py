from ssah.auth.domain.entities.user import User
from ssah.auth.domain.exceptions import InactiveUserError, UserNotFoundError


class GetCurrentUser:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self, user_id: str) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("Usuario no encontrado")
        if not user.is_active:
            raise InactiveUserError("El usuario está inactivo")
        return user

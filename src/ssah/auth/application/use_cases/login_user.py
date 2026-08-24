from ssah.auth.domain.exceptions import InactiveUserError, InvalidCredentialsError


class LoginUser:
    def __init__(self, user_repository, password_hasher, token_service, token_repository):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.token_repository = token_repository

    async def execute(self, email: str, password: str) -> dict[str, str]:
        user = await self.user_repository.get_by_email(email.strip().lower())
        if not user or not self.password_hasher.verify(password, user.hashed_password):
            raise InvalidCredentialsError("Credenciales inválidas")
        if not user.is_active:
            raise InactiveUserError("El usuario está inactivo")

        access_token = self.token_service.create_access_token(str(user.id))
        refresh_token, token_id, expires_at = self.token_service.create_refresh_token(str(user.id))
        await self.token_repository.save_refresh_token(
            user_id=user.id,
            token_id=token_id,
            token_hash=self.token_service.fingerprint(refresh_token),
            expires_at=expires_at,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

from ssas.auth.domain.exceptions import InvalidCredentialsError
from ssas.config.settings import settings


class LoginUser:
    def __init__(self, user_repository, password_hasher, token_service, token_repository):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.token_repository = token_repository

    async def execute(
        self,
        password: str,
        empresa_slug: str,
        email: str | None = None,
        username: str | None = None,
    ) -> dict[str, object]:
        login = (email or username or "").strip()
        if not login:
            raise InvalidCredentialsError("Credenciales inválidas")

        user = await self.user_repository.get_by_login(login, empresa_slug)
        if not user or not self.password_hasher.verify(password, user.hashed_password):
            raise InvalidCredentialsError("Credenciales inválidas")
        if not user.is_active or not user.empresa_is_active or not user.empresa_id or not user.roles:
            raise InvalidCredentialsError("Credenciales inválidas")

        access_token = self.token_service.create_access_token(
            subject=str(user.id),
            empresa_id=user.empresa_id,
            roles=user.roles,
        )
        refresh_token, token_id, expires_at = self.token_service.create_refresh_token(
            subject=str(user.id),
            empresa_id=user.empresa_id,
        )
        await self.token_repository.save_refresh_token(
            user_id=user.id,
            empresa_id=user.empresa_id,
            token_id=token_id,
            token_hash=self.token_service.fingerprint(refresh_token),
            expires_at=expires_at,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.app_access_token_expire_minutes * 60,
        }

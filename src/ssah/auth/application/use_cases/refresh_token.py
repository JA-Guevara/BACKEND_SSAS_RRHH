from hmac import compare_digest

from ssah.auth.domain.exceptions import InvalidTokenError


class RefreshToken:
    def __init__(self, token_service, token_repository, user_repository):
        self.token_service = token_service
        self.token_repository = token_repository
        self.user_repository = user_repository

    async def execute(self, refresh_token: str) -> dict[str, str]:
        payload = self.token_service.decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        token_id = payload.get("jti")
        if not isinstance(user_id, str) or not isinstance(token_id, str):
            raise InvalidTokenError("Token inválido")

        stored_token = await self.token_repository.get_active_refresh_token(token_id)
        if not stored_token or not compare_digest(
            stored_token.token_hash, self.token_service.fingerprint(refresh_token)
        ):
            raise InvalidTokenError("El refresh token fue revocado o no existe")

        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidTokenError("El usuario del token no está disponible")

        await self.token_repository.revoke_refresh_token(token_id)
        new_refresh, new_token_id, expires_at = self.token_service.create_refresh_token(user_id)
        await self.token_repository.save_refresh_token(
            user_id=user_id,
            token_id=new_token_id,
            token_hash=self.token_service.fingerprint(new_refresh),
            expires_at=expires_at,
        )

        return {
            "access_token": self.token_service.create_access_token(user_id),
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }

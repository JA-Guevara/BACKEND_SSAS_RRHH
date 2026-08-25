from datetime import UTC, datetime
from hmac import compare_digest

from ssas.auth.domain.exceptions import InvalidTokenError
from ssas.config.settings import settings


class RefreshToken:
    def __init__(self, token_service, token_repository, user_repository):
        self.token_service = token_service
        self.token_repository = token_repository
        self.user_repository = user_repository

    async def execute(self, refresh_token: str) -> dict[str, object]:
        payload = self.token_service.decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        empresa_id = payload.get("tid")
        token_id = payload.get("jti")
        if not isinstance(user_id, str) or not isinstance(empresa_id, str) or not isinstance(token_id, str):
            raise InvalidTokenError("Token inválido")

        stored_token = await self.token_repository.get_active_refresh_token(token_id)
        if (
            not stored_token
            or stored_token.empresa_id != empresa_id
            or not compare_digest(stored_token.token_hash, self.token_service.fingerprint(refresh_token))
        ):
            raise InvalidTokenError("El refresh token fue revocado o no existe")

        user = await self.user_repository.get_by_id(user_id, empresa_id)
        if (
            not user
            or not user.is_active
            or not user.empresa_is_active
            or user.empresa_id != empresa_id
            or not user.roles
            or not user.email_verified
            or (user.locked_until is not None and user.locked_until > datetime.now(UTC))
        ):
            raise InvalidTokenError("El usuario del token no está disponible")

        await self.token_repository.revoke_refresh_token(token_id)
        new_refresh, new_token_id, expires_at = self.token_service.create_refresh_token(
            subject=user_id,
            empresa_id=empresa_id,
        )
        await self.token_repository.save_refresh_token(
            user_id=user_id,
            empresa_id=empresa_id,
            token_id=new_token_id,
            token_hash=self.token_service.fingerprint(new_refresh),
            expires_at=expires_at,
        )

        return {
            "access_token": self.token_service.create_access_token(
                subject=user_id,
                empresa_id=empresa_id,
                roles=user.roles,
                must_change_password=user.must_change_password,
            ),
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": settings.app_access_token_expire_minutes * 60,
        }

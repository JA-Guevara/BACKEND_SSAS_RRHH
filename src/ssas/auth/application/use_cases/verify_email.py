from ssas.auth.domain.exceptions import InvalidTokenError


class VerifyEmail:
    def __init__(self, user_repository, token_repository, token_service):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.token_service = token_service

    async def execute(self, raw_token: str) -> None:
        token = await self.token_repository.get_active_email_verification_token(
            self.token_service.fingerprint(raw_token)
        )
        if not token:
            raise InvalidTokenError("El token de verificación es inválido o expiró")
        await self.user_repository.mark_email_verified(token.user_id, token.empresa_id)
        await self.token_repository.consume_email_verification_token(token.id)

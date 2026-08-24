from ssas.auth.domain.exceptions import InvalidTokenError


class ResetPassword:
    def __init__(self, user_repository, token_repository, token_service, password_hasher):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.token_service = token_service
        self.password_hasher = password_hasher

    async def execute(self, token: str, new_password: str) -> None:
        stored_token = await self.token_repository.get_active_password_reset_token(
            self.token_service.fingerprint(token)
        )
        if not stored_token:
            raise InvalidTokenError("El token de recuperación es inválido o expiró")

        hashed_password = self.password_hasher.hash(new_password)
        await self.user_repository.update_password(
            stored_token.user_id,
            stored_token.empresa_id,
            hashed_password,
        )
        await self.token_repository.consume_password_reset_token(stored_token.id)
        await self.token_repository.revoke_all_refresh_tokens(
            stored_token.user_id,
            stored_token.empresa_id,
        )

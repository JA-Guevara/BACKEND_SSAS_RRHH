from ssas.auth.domain.exceptions import InvalidTokenError


class LogoutUser:
    def __init__(self, token_service, token_repository):
        self.token_service = token_service
        self.token_repository = token_repository

    async def execute(self, refresh_token: str, user_id: str, empresa_id: str | None) -> None:
        payload = self.token_service.decode_token(refresh_token, expected_type="refresh")
        token_id = payload.get("jti")
        if (
            not isinstance(token_id, str)
            or payload.get("sub") != user_id
            or payload.get("tid") != empresa_id
        ):
            raise InvalidTokenError("Token inválido")
        await self.token_repository.revoke_refresh_token(token_id)

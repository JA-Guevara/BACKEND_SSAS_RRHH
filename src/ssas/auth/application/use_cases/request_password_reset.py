import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4


class RequestPasswordReset:
    def __init__(self, user_repository, token_repository, token_service, expire_minutes: int):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.token_service = token_service
        self.expire_minutes = expire_minutes

    async def execute(self, email: str, empresa_slug: str) -> str | None:
        user = await self.user_repository.get_by_login(email.strip().lower(), empresa_slug)
        if not user or not user.is_active or not user.empresa_id:
            return None

        await self.token_repository.revoke_password_reset_tokens(user.id, user.empresa_id)
        raw_token = secrets.token_urlsafe(32)
        await self.token_repository.save_password_reset_token(
            user_id=user.id,
            empresa_id=user.empresa_id,
            token_id=str(uuid4()),
            token_hash=self.token_service.fingerprint(raw_token),
            expires_at=datetime.now(UTC) + timedelta(minutes=self.expire_minutes),
        )
        return raw_token

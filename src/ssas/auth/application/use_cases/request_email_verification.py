import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4


class RequestEmailVerification:
    def __init__(self, user_repository, token_repository, token_service, expire_minutes: int):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.token_service = token_service
        self.expire_minutes = expire_minutes

    async def execute(self, email: str, empresa_slug: str) -> tuple[str, str] | None:
        user = await self.user_repository.get_by_login(email.strip().lower(), empresa_slug)
        if not user or not user.is_active or user.email_verified:
            return None
        await self.token_repository.revoke_email_verification_tokens(user.id, user.empresa_id)
        raw_token = secrets.token_urlsafe(32)
        await self.token_repository.save_email_verification_token(
            user.id,
            user.empresa_id,
            str(uuid4()),
            self.token_service.fingerprint(raw_token),
            datetime.now(UTC) + timedelta(minutes=self.expire_minutes),
        )
        return user.email, raw_token

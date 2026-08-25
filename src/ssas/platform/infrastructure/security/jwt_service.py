from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import jwt
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError as PyJWTInvalidTokenError

from ssas.auth.domain.exceptions import InvalidTokenError, TokenExpiredError
from ssas.config.settings import settings


class PlatformJWTService:
    def create_access_token(self, admin_id: str) -> tuple[str, int]:
        expires_in = settings.app_access_token_expire_minutes * 60
        return self._encode(admin_id, "access", datetime.now(UTC) + timedelta(seconds=expires_in)), expires_in

    def create_refresh_token(self, admin_id: str) -> tuple[str, str, datetime]:
        token_id = str(uuid4())
        expires_at = datetime.now(UTC) + timedelta(days=settings.app_refresh_token_expire_days)
        return self._encode(admin_id, "refresh", expires_at, token_id), token_id, expires_at

    def decode(self, token: str, expected_type: str) -> dict[str, object]:
        try:
            payload = jwt.decode(token, settings.app_secret_key, algorithms=[settings.app_algorithm])
        except ExpiredSignatureError as exc:
            raise TokenExpiredError("El token expiró") from exc
        except PyJWTInvalidTokenError as exc:
            raise InvalidTokenError("Token inválido") from exc
        if payload.get("scope") != "platform" or payload.get("type") != expected_type or not payload.get("sub"):
            raise InvalidTokenError("Token de plataforma inválido")
        return payload

    @staticmethod
    def fingerprint(token: str) -> str:
        return sha256(token.encode()).hexdigest()

    @staticmethod
    def _base_payload(admin_id: str, token_type: str, token_id: str, expires_at: datetime) -> dict[str, object]:
        return {
            "sub": admin_id,
            "scope": "platform",
            "roles": ["SUPER_ADMIN"],
            "type": token_type,
            "jti": token_id,
            "iat": datetime.now(UTC),
            "exp": expires_at,
        }

    def _encode(self, admin_id: str, token_type: str, expires_at: datetime, token_id: str | None = None) -> str:
        payload = self._base_payload(admin_id, token_type, token_id or str(uuid4()), expires_at)
        return jwt.encode(payload, settings.app_secret_key, algorithm=settings.app_algorithm)

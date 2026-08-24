from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError as PyJWTInvalidTokenError

from ssah.auth.domain.exceptions import InvalidTokenError, TokenExpiredError
from ssah.auth.ports.outgoing.token_service import TokenService
from ssah.config.settings import settings


class JWTService(TokenService):
    def create_access_token(
        self,
        subject: str,
        empresa_id: str,
        roles: list[str] | None = None,
    ) -> str:
        expires_delta = timedelta(minutes=settings.app_access_token_expire_minutes)
        return self._create_token(subject, empresa_id, "access", expires_delta, roles=roles)

    def create_refresh_token(
        self,
        subject: str,
        empresa_id: str,
    ) -> tuple[str, str, datetime]:
        expires_delta = timedelta(days=settings.app_refresh_token_expire_days)
        token_id = str(uuid4())
        expires_at = datetime.now(UTC) + expires_delta
        token = self._encode(subject, empresa_id, "refresh", token_id, expires_at)
        return token, token_id, expires_at

    def decode_token(self, token: str, expected_type: str) -> dict[str, object]:
        try:
            payload = jwt.decode(
                token,
                settings.app_secret_key,
                algorithms=[settings.app_algorithm],
            )
        except ExpiredSignatureError as exc:
            raise TokenExpiredError("El token expiró") from exc
        except PyJWTInvalidTokenError as exc:
            raise InvalidTokenError("Token inválido") from exc

        if payload.get("type") != expected_type or not payload.get("sub"):
            raise InvalidTokenError("El tipo de token no es válido")
        return payload

    def fingerprint(self, token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    def _create_token(
        self,
        subject: str,
        empresa_id: str,
        token_type: str,
        expires_delta: timedelta,
        roles: list[str] | None = None,
    ) -> str:
        return self._encode(
            subject=subject,
            empresa_id=empresa_id,
            token_type=token_type,
            token_id=str(uuid4()),
            expires_at=datetime.now(UTC) + expires_delta,
            roles=roles,
        )

    def _encode(
        self,
        subject: str,
        empresa_id: str,
        token_type: str,
        token_id: str,
        expires_at: datetime,
        roles: list[str] | None = None,
    ) -> str:
        now = datetime.now(UTC)
        payload: dict[str, object] = {
            "sub": subject,
            "tid": empresa_id,
            "type": token_type,
            "jti": token_id,
            "iat": now,
            "exp": expires_at,
        }
        if roles is not None:
            payload["roles"] = roles
        return jwt.encode(payload, settings.app_secret_key, algorithm=settings.app_algorithm)
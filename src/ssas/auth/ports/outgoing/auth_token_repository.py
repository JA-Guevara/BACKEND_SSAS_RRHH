from abc import ABC, abstractmethod
from datetime import datetime

from ssas.auth.domain.entities.auth_token import StoredToken


class AuthTokenRepository(ABC):
    @abstractmethod
    async def save_refresh_token(
        self,
        user_id: str,
        empresa_id: str,
        token_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_refresh_token(self, token_id: str) -> StoredToken | None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_refresh_token(self, token_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_all_refresh_tokens(self, user_id: str, empresa_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def save_password_reset_token(
        self,
        user_id: str,
        empresa_id: str,
        token_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_password_reset_token(self, token_hash: str) -> StoredToken | None:
        raise NotImplementedError

    @abstractmethod
    async def consume_password_reset_token(self, token_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_password_reset_tokens(self, user_id: str, empresa_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def save_email_verification_token(self, user_id: str, empresa_id: str, token_id: str, token_hash: str, expires_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_email_verification_token(self, token_hash: str) -> StoredToken | None:
        raise NotImplementedError

    @abstractmethod
    async def consume_email_verification_token(self, token_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_email_verification_tokens(self, user_id: str, empresa_id: str) -> None:
        raise NotImplementedError

from abc import ABC, abstractmethod
from datetime import datetime


class TokenService(ABC):
    @abstractmethod
    def create_access_token(self, subject: str, tenant_id: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_refresh_token(
        self,
        subject: str,
        tenant_id: str | None = None,
    ) -> tuple[str, str, datetime]:
        raise NotImplementedError

    @abstractmethod
    def decode_token(self, token: str, expected_type: str) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def fingerprint(self, token: str) -> str:
        raise NotImplementedError
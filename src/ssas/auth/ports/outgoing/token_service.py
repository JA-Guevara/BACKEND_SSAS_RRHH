from abc import ABC, abstractmethod
from datetime import datetime


class TokenService(ABC):
    @abstractmethod
    def create_access_token(
        self,
        subject: str,
        empresa_id: str | None,
        roles: list[str] | None = None,
        must_change_password: bool = False,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_refresh_token(
        self,
        subject: str,
        empresa_id: str | None,
    ) -> tuple[str, str, datetime]:
        raise NotImplementedError

    @abstractmethod
    def decode_token(self, token: str, expected_type: str) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def fingerprint(self, token: str) -> str:
        raise NotImplementedError

from abc import ABC, abstractmethod

from ssas.auth.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str, empresa_id: str | None) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, username: str, empresa_id: str | None) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_login(self, login: str, empresa_slug: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: str, empresa_id: str | None) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def update_password(
        self, user_id: str, empresa_id: str | None, hashed_password: str, must_change: bool = False
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def record_failed_login(
        self, user_id: str, empresa_id: str | None, max_attempts: int, lock_minutes: int
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def record_successful_login(self, user_id: str, empresa_id: str | None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_email_verified(self, user_id: str, empresa_id: str | None) -> None:
        raise NotImplementedError

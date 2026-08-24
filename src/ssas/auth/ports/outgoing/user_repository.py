from abc import ABC, abstractmethod

from ssas.auth.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str, empresa_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, username: str, empresa_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_login(self, login: str, empresa_slug: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: str, empresa_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def update_password(
        self, user_id: str, empresa_id: str, hashed_password: str
    ) -> None:
        raise NotImplementedError

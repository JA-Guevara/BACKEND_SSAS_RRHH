from abc import ABC, abstractmethod

from ssah.auth.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    async def get_by_login(self, login: str) -> User | None:
        normalized = login.strip().lower()
        if "@" in normalized:
            return await self.get_by_email(normalized)
        return await self.get_by_username(normalized)

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def update_password(self, user_id: str, hashed_password: str) -> None:
        raise NotImplementedError
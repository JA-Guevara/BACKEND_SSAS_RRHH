from abc import ABC, abstractmethod


class RoleRepository(ABC):
    @abstractmethod
    async def create(self, role):
        raise NotImplementedError

    @abstractmethod
    async def list(self):
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, role_id: str):
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, name: str):
        raise NotImplementedError

    @abstractmethod
    async def get_by_code(self, code: str):
        raise NotImplementedError

    @abstractmethod
    async def update(self, role_id: str, values: dict):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, role_id: str):
        raise NotImplementedError

    @abstractmethod
    async def assign_permissions(self, role_id: str, permissions: list):
        raise NotImplementedError

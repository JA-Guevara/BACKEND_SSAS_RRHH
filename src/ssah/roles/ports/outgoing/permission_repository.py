from abc import ABC, abstractmethod


class PermissionRepository(ABC):
    @abstractmethod
    async def get_by_ids(self, permission_ids: list[str]):
        raise NotImplementedError
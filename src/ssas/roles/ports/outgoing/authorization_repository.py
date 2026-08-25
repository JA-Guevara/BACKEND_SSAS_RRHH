from abc import ABC, abstractmethod


class AuthorizationRepository(ABC):
    @abstractmethod
    async def get_user_permission_codes(self, user_id: str, empresa_id: str | None) -> set[str]:
        raise NotImplementedError

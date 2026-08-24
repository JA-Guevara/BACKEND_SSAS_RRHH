from ssas.roles.domain.exceptions import PermissionDeniedError
from ssas.roles.ports.outgoing.authorization_repository import AuthorizationRepository


class CheckPermission:
    def __init__(self, authorization_repository: AuthorizationRepository):
        self.authorization_repository = authorization_repository

    async def execute(self, user_id: str, empresa_id: str, required_permission: str) -> None:
        permission_codes = await self.authorization_repository.get_user_permission_codes(
            user_id=user_id,
            empresa_id=empresa_id,
        )
        if required_permission not in permission_codes:
            raise PermissionDeniedError("No tiene permisos para realizar esta acción")
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.domain.exceptions import AuthError
from ssas.core.security.jwt import JWTService
from ssas.core.tenancy.context import require_empresa_context
from ssas.infrastructure.database.session import get_session
from ssas.roles.application.use_cases.check_permission import CheckPermission
from ssas.roles.domain.exceptions import PermissionDeniedError
from ssas.roles.infrastructure.persistence.repositories.authorization_repository import (
    SqlAlchemyAuthorizationRepository,
)

bearer_scheme = HTTPBearer(auto_error=False)
token_service = JWTService()


@dataclass(frozen=True)
class CurrentUser:
    id: str
    empresa_id: str
    roles: list[str] = field(default_factory=list)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida",
        )

    try:
        payload = token_service.decode_token(credentials.credentials, expected_type="access")
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        ) from exc

    user_id = payload.get("sub")
    empresa_id = payload.get("tid")
    roles = payload.get("roles", [])
    current_empresa_id = require_empresa_context()

    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    if not isinstance(empresa_id, str) or not empresa_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token no contiene una empresa válida",
        )
    if empresa_id != current_empresa_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La empresa del token no coincide con el contexto de la petición",
        )
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    return CurrentUser(id=user_id, empresa_id=empresa_id, roles=roles)


def require_permission(required_permission: str) -> Callable:
    async def dependency(
        current_user: CurrentUser = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> CurrentUser:
        empresa_id = require_empresa_context()
        try:
            await CheckPermission(SqlAlchemyAuthorizationRepository(session)).execute(
                user_id=current_user.id,
                empresa_id=empresa_id,
                required_permission=required_permission,
            )
        except PermissionDeniedError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
        return current_user

    return dependency
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.domain.exceptions import AuthError
from ssas.infrastructure.database.session import get_session
from ssas.platform.infrastructure.persistence.repositories.platform_repository import (
    PlatformRepository,
)
from ssas.platform.infrastructure.security.jwt_service import PlatformJWTService

bearer = HTTPBearer(auto_error=False)
tokens = PlatformJWTService()


@dataclass(frozen=True)
class CurrentPlatformAdmin:
    id: str
    email: str
    username: str


async def get_current_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> CurrentPlatformAdmin:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticación de plataforma requerida")
    try:
        payload = tokens.decode(credentials.credentials, "access")
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de plataforma inválido") from exc
    admin_id = payload.get("sub")
    if not isinstance(admin_id, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de plataforma inválido")
    admin = await PlatformRepository(session).get_admin(admin_id)
    if not admin or not admin.activo or not admin.email_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Administrador no disponible")
    if admin.bloqueado_hasta and admin.bloqueado_hasta > datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Cuenta de plataforma bloqueada temporalmente")
    return CurrentPlatformAdmin(id=admin.id, email=admin.email, username=admin.username)

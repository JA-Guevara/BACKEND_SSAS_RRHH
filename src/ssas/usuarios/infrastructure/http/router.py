from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.domain.exceptions import AuthError
from ssas.auth.infrastructure.persistence.repositories.auth_token_repository import (
    SqlAlchemyAuthTokenRepository,
)
from ssas.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssas.bitacora.application.events.user_events import UserEvents
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.core.security.dependencies import CurrentUser, require_permission
from ssas.infrastructure.database.session import get_session
from ssas.usuarios.application.use_cases.activar_usuario import ActivarUsuario
from ssas.usuarios.application.use_cases.actualizar_usuario import ActualizarUsuario
from ssas.usuarios.application.use_cases.cambiar_password_usuario import CambiarPasswordUsuario
from ssas.usuarios.application.use_cases.crear_usuario import CrearUsuario
from ssas.usuarios.application.use_cases.desactivar_usuario import DesactivarUsuario
from ssas.usuarios.application.use_cases.desbloquear_usuario import DesbloquearUsuario
from ssas.usuarios.application.use_cases.listar_usuarios import ListarUsuarios
from ssas.usuarios.application.use_cases.obtener_usuario import ObtenerUsuario
from ssas.usuarios.domain.exceptions import (
    InvalidRoleForEmpresaError,
    LastAdminCannotBeDisabledError,
    UsuarioAlreadyExistsError,
    UsuarioError,
    UsuarioNotFoundError,
    UsuarioWithoutRoleError,
)
from ssas.usuarios.infrastructure.http.schemas import (
    ActualizarUsuarioRequest,
    CambiarPasswordUsuarioRequest,
    CrearUsuarioRequest,
    UsuarioPageResponse,
    UsuarioResponse,
)
from ssas.usuarios.infrastructure.persistence.repositories.usuario_repository import (
    SqlAlchemyUsuarioRepository,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
password_hasher = Argon2PasswordHasher()


def _repository(session: AsyncSession) -> SqlAlchemyUsuarioRepository:
    return SqlAlchemyUsuarioRepository(session)


def _events(session: AsyncSession) -> UserEvents:
    return UserEvents(RegisterAuditEvent(SqlAlchemyAuditLogRepository(session)))


def _audit_context(request: Request, current_user: CurrentUser) -> dict[str, str | None]:
    return {
        "empresa_id": current_user.empresa_id,
        "user_id": current_user.id,
        "source_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def _raise_http_usuario_error(exc: UsuarioError) -> None:
    if isinstance(exc, UsuarioNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, UsuarioAlreadyExistsError):
        code = status.HTTP_409_CONFLICT
    elif isinstance(
        exc,
        (UsuarioWithoutRoleError, InvalidRoleForEmpresaError, LastAdminCannotBeDisabledError),
    ):
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("", response_model=UsuarioPageResponse)
async def listar_usuarios(
    search: str | None = Query(default=None, max_length=120),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("usuarios:ver")),
    session: AsyncSession = Depends(get_session),
):
    return await ListarUsuarios(_repository(session)).execute(
        current_user.empresa_id, search, is_active, page, per_page
    )


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    request: CrearUsuarioRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("usuarios:crear")),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await CrearUsuario(_repository(session), password_hasher).execute(
            empresa_id=current_user.empresa_id,
            **request.model_dump(),
        )
        await _events(session).created(
            record_id=user.id,
            new_data={"email": user.email, "username": user.username},
            **_audit_context(http_request, current_user),
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: str,
    request: ActualizarUsuarioRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("usuarios:editar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        data = request.model_dump(exclude_unset=True)
        role_ids = data.pop("role_ids", None)
        user = await ActualizarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=current_user.empresa_id,
            values=data,
            role_ids=role_ids,
        )
        await _events(session).updated(
            record_id=user.id,
            new_data=data,
            **_audit_context(http_request, current_user),
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch("/{usuario_id}/activar", response_model=UsuarioResponse)
async def activar_usuario(
    usuario_id: str,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("usuarios:editar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await ActivarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=current_user.empresa_id,
        )
        await _events(session).activated(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch("/{usuario_id}/desactivar", response_model=UsuarioResponse)
async def desactivar_usuario(
    usuario_id: str,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("usuarios:editar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await DesactivarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=current_user.empresa_id,
        )
        await _events(session).deactivated(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: str,
    current_user: CurrentUser = Depends(require_permission("usuarios:ver")),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await ObtenerUsuario(_repository(session)).execute(
            usuario_id, current_user.empresa_id
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.put("/{usuario_id}/password", response_model=UsuarioResponse)
async def cambiar_password_usuario(
    usuario_id: str,
    request: CambiarPasswordUsuarioRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("usuarios:cambiar_password")),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await CambiarPasswordUsuario(
            _repository(session), SqlAlchemyAuthTokenRepository(session), password_hasher
        ).execute(
            usuario_id,
            current_user.empresa_id,
            request.new_password,
            request.must_change,
        )
        await _events(session).password_changed(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except (UsuarioError, AuthError) as exc:
        if isinstance(exc, UsuarioError):
            _raise_http_usuario_error(exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{usuario_id}/desbloquear", response_model=UsuarioResponse)
async def desbloquear_usuario(
    usuario_id: str,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("usuarios:desbloquear")),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await DesbloquearUsuario(_repository(session)).execute(
            usuario_id, current_user.empresa_id
        )
        await _events(session).unlocked(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)

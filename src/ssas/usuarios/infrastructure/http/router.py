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
from ssas.core.api.openapi import (
    AUTHENTICATED_RESPONSES,
    EMPRESA_SCOPE_DESCRIPTION,
    TAG_USERS,
)
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
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

router = APIRouter(prefix="/usuarios", tags=[TAG_USERS], responses=AUTHENTICATED_RESPONSES)
password_hasher = Argon2PasswordHasher()


def _target_empresa(current_user: CurrentUser, requested: str | None) -> str | None:
    if current_user.es_plataforma:
        return requested
    if requested is not None and requested != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No puedes operar sobre otra empresa")
    return current_user.empresa_id


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


@router.get(
    "",
    response_model=UsuarioPageResponse,
    summary="Listar usuarios",
    description=(
        "Lista usuarios con búsqueda, estado y paginación. Permisos: `usuarios:ver` para "
        "empresa o `platform:usuarios:gestionar` para plataforma."
    ),
    responses={409: {"description": "El correo o nombre de usuario ya está registrado."}},
)
async def listar_usuarios(
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    search: str | None = Query(
        default=None, max_length=120, description="Busca por nombre, usuario o correo."
    ),
    is_active: bool | None = Query(default=None, description="Filtra por estado activo."),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:ver", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    return await ListarUsuarios(_repository(session)).execute(
        _target_empresa(current_user, empresa_id), search, is_active, page, per_page
    )


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description=(
        "Crea una cuenta y asigna sus roles. Un administrador empresarial crea usuarios "
        "solo en su empresa; plataforma puede crear usuarios globales o indicar "
        "`empresa_id`. Permisos: `usuarios:crear` o `platform:usuarios:gestionar`."
    ),
    responses={
        404: {"description": "Usuario no encontrado dentro del alcance."},
        409: {"description": "El correo o nombre de usuario ya está registrado."},
    },
)
async def crear_usuario(
    request: CrearUsuarioRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:crear", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        data = request.model_dump()
        target_empresa = _target_empresa(current_user, data.pop("empresa_id", None))
        user = await CrearUsuario(_repository(session), password_hasher).execute(
            empresa_id=target_empresa, **data
        )
        await _events(session).created(
            record_id=user.id,
            new_data={"email": user.email, "username": user.username},
            **_audit_context(http_request, current_user),
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Actualizar usuario",
    description=(
        "Actualiza únicamente los campos enviados y, cuando corresponda, reemplaza sus "
        "roles. Permisos: `usuarios:editar` o `platform:usuarios:gestionar`."
    ),
    responses={404: {"description": "Usuario no encontrado dentro del alcance."}},
)
async def actualizar_usuario(
    usuario_id: str,
    request: ActualizarUsuarioRequest,
    http_request: Request,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:editar", "platform:usuarios:gestionar")
    ),
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


@router.patch(
    "/{usuario_id}/activar",
    response_model=UsuarioResponse,
    summary="Activar usuario",
    description=(
        "Habilita el acceso de una cuenta dentro del alcance autorizado. Permisos: "
        "`usuarios:editar` o `platform:usuarios:gestionar`."
    ),
    responses={404: {"description": "Usuario no encontrado dentro del alcance."}},
)
async def activar_usuario(
    usuario_id: str,
    http_request: Request,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:editar", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await ActivarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=_target_empresa(current_user, empresa_id),
        )
        await _events(session).activated(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch(
    "/{usuario_id}/desactivar",
    response_model=UsuarioResponse,
    summary="Desactivar usuario",
    description=(
        "Deshabilita el acceso sin eliminar la cuenta. No permite desactivar al último "
        "administrador del alcance. Permisos: `usuarios:editar` o "
        "`platform:usuarios:gestionar`."
    ),
    responses={404: {"description": "Usuario no encontrado dentro del alcance."}},
)
async def desactivar_usuario(
    usuario_id: str,
    http_request: Request,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:editar", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await DesactivarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=_target_empresa(current_user, empresa_id),
        )
        await _events(session).deactivated(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Consultar usuario",
    description=(
        "Obtiene una cuenta por identificador dentro del alcance autorizado. Permisos: "
        "`usuarios:ver` o `platform:usuarios:gestionar`."
    ),
    responses={404: {"description": "Usuario no encontrado dentro del alcance."}},
)
async def obtener_usuario(
    usuario_id: str,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:ver", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await ObtenerUsuario(_repository(session)).execute(
            usuario_id, _target_empresa(current_user, empresa_id)
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.put(
    "/{usuario_id}/password",
    response_model=UsuarioResponse,
    summary="Asignar contraseña administrativa",
    description=(
        "Establece una contraseña nueva, permite exigir cambio en el siguiente acceso y "
        "revoca sesiones existentes. Permisos: `usuarios:cambiar_password` o "
        "`platform:usuarios:gestionar`."
    ),
    responses={404: {"description": "Usuario no encontrado dentro del alcance."}},
)
async def cambiar_password_usuario(
    usuario_id: str,
    request: CambiarPasswordUsuarioRequest,
    http_request: Request,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:cambiar_password", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await CambiarPasswordUsuario(
            _repository(session), SqlAlchemyAuthTokenRepository(session), password_hasher
        ).execute(
            usuario_id,
            _target_empresa(current_user, empresa_id),
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


@router.patch(
    "/{usuario_id}/desbloquear",
    response_model=UsuarioResponse,
    summary="Desbloquear usuario",
    description=(
        "Restablece los intentos fallidos y elimina el bloqueo temporal. Permisos: "
        "`usuarios:desbloquear` o `platform:usuarios:gestionar`."
    ),
)
async def desbloquear_usuario(
    usuario_id: str,
    http_request: Request,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:desbloquear", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await DesbloquearUsuario(_repository(session)).execute(
            usuario_id, _target_empresa(current_user, empresa_id)
        )
        await _events(session).unlocked(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)

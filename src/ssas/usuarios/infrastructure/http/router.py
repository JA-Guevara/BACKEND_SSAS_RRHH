import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.domain.exceptions import AuthError
from ssas.auth.infrastructure.persistence.models.refresh_token import RefreshTokenModel
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.auth.infrastructure.persistence.repositories.auth_token_repository import (
    SqlAlchemyAuthTokenRepository,
)
from ssas.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssas.bitacora.application.events.user_events import UserEvents
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.crypto import AuditEncryptionError
from ssas.bitacora.infrastructure.persistence.models.audit_log import AuditLogModel
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.config.settings import settings
from ssas.core.api.openapi import (
    AUTHENTICATED_RESPONSES,
    EMPRESA_SCOPE_DESCRIPTION,
    TAG_USERS,
)
from ssas.core.api.request_metadata import get_client_ip
from ssas.core.security.dependencies import (
    CurrentUser,
    get_current_user,
    require_scoped_permission,
)
from ssas.infrastructure.database.session import get_session
from ssas.suscripciones.application.policy import SubscriptionPolicy, SubscriptionPolicyError
from ssas.usuarios.application.use_cases.activar_usuario import ActivarUsuario
from ssas.usuarios.application.use_cases.actualizar_usuario import ActualizarUsuario
from ssas.usuarios.application.use_cases.cambiar_password_usuario import CambiarPasswordUsuario
from ssas.usuarios.application.use_cases.crear_usuario import CrearUsuario
from ssas.usuarios.application.use_cases.desactivar_usuario import DesactivarUsuario
from ssas.usuarios.application.use_cases.desbloquear_usuario import DesbloquearUsuario
from ssas.usuarios.application.use_cases.eliminar_usuario import EliminarUsuario
from ssas.usuarios.application.use_cases.listar_usuarios import ListarUsuarios
from ssas.usuarios.application.use_cases.obtener_usuario import ObtenerUsuario
from ssas.usuarios.application.use_cases.restaurar_usuario import RestaurarUsuario
from ssas.usuarios.domain.exceptions import (
    CannotDeleteSelfError,
    InvalidRoleForEmpresaError,
    LastAdminCannotBeDisabledError,
    UsuarioAlreadyExistsError,
    UsuarioDeletedError,
    UsuarioError,
    UsuarioNotDeletedError,
    UsuarioNotFoundError,
    UsuarioWithoutRoleError,
)
from ssas.usuarios.infrastructure.http.schemas import (
    ActividadResponse,
    ActualizarMiPerfilRequest,
    ActualizarUsuarioRequest,
    CambiarPasswordUsuarioRequest,
    CrearUsuarioRequest,
    FotoPerfilResponse,
    MensajeResponse,
    SesionResponse,
    UsuarioPageResponse,
    UsuarioResponse,
)
from ssas.usuarios.infrastructure.persistence.repositories.usuario_repository import (
    SqlAlchemyUsuarioRepository,
)
from ssas.usuarios.infrastructure.storage.avatar_storage import (
    delete_avatar_file,
    get_avatar_path,
    process_and_save_avatar,
)

logger = logging.getLogger(__name__)

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
        "source_ip": get_client_ip(request),
        "user_agent": request.headers.get("user-agent"),
    }


def _raise_http_usuario_error(exc: UsuarioError) -> None:
    if isinstance(exc, UsuarioNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(
        exc,
        (
            UsuarioAlreadyExistsError,
            UsuarioDeletedError,
            UsuarioNotDeletedError,
            CannotDeleteSelfError,
        ),
    ):
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
    incluir_eliminados: bool = Query(
        default=False,
        description="Incluye cuentas eliminadas lógicamente. Requiere el mismo alcance autorizado.",
    ),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:ver", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    return await ListarUsuarios(_repository(session)).execute(
        _target_empresa(current_user, empresa_id),
        search,
        is_active,
        page,
        per_page,
        incluir_eliminados,
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
        if target_empresa is not None:
            await SubscriptionPolicy(
                session, settings.subscription_grace_days
            ).require_user_capacity(target_empresa)
        user = await CrearUsuario(_repository(session), password_hasher).execute(
            empresa_id=target_empresa, **data
        )
        await _events(session).created(
            record_id=user.id,
            new_data={"email": user.email, "username": user.username},
            **_audit_context(http_request, current_user),
        )
        return user
    except SubscriptionPolicyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Consultar mi perfil",
    description=(
        "Devuelve la información completa del usuario autenticado dentro de su alcance. "
        "Complementa a `/auth/me` (identidad) con los datos editables del perfil."
    ),
)
async def obtener_mi_perfil(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await ObtenerUsuario(_repository(session)).execute(
            user_id=current_user.id,
            empresa_id=current_user.empresa_id,
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch(
    "/me",
    response_model=UsuarioResponse,
    summary="Actualizar mi perfil",
    description=(
        "Actualiza solo la información básica del usuario autenticado (nombre, apellido, "
        "teléfono). No permite cambiar correo, usuario, roles ni estado: son privilegios "
        "administrativos. La operación queda registrada en bitácora."
    ),
)
async def actualizar_mi_perfil(
    request: ActualizarMiPerfilRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        data = request.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            raise HTTPException(status_code=422, detail="No se enviaron campos para actualizar")
        user = await ActualizarUsuario(_repository(session)).execute(
            user_id=current_user.id,
            empresa_id=current_user.empresa_id,
            values=data,
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)
    await _events(session).updated(
        record_id=user.id,
        new_data=data,
        **_audit_context(http_request, current_user),
    )
    return user


@router.post(
    "/me/foto",
    response_model=FotoPerfilResponse,
    summary="Subir foto de perfil",
    description=(
        "Sube una foto de perfil (JPEG, PNG o WebP, máx 2 MB). La imagen se valida con Pillow, "
        "se recorta en proporción 1:1, se redimensiona a 512x512 y se almacena en el volumen persistente."
    ),
)
async def subir_foto_perfil(
    http_request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    content = await file.read()
    try:
        url = process_and_save_avatar(current_user.id, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Actualizar la URL en la base de datos
    await session.execute(
        update(UserModel)
        .where(UserModel.id == current_user.id)
        .values(foto_url=url)
    )
    await session.commit()

    await _events(session).updated(
        record_id=current_user.id,
        new_data={"foto_url": url},
        **_audit_context(http_request, current_user),
    )
    return FotoPerfilResponse(foto_url=url, mensaje="Foto de perfil actualizada correctamente")


@router.delete(
    "/me/foto",
    response_model=MensajeResponse,
    summary="Eliminar foto de perfil",
    description="Elimina la foto de perfil y restablece el avatar a las iniciales calculadas.",
)
async def eliminar_foto_perfil(
    http_request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    delete_avatar_file(current_user.id)
    await session.execute(
        update(UserModel)
        .where(UserModel.id == current_user.id)
        .values(foto_url=None)
    )
    await session.commit()

    await _events(session).updated(
        record_id=current_user.id,
        new_data={"foto_url": None},
        **_audit_context(http_request, current_user),
    )
    return MensajeResponse(mensaje="Foto de perfil eliminada correctamente")


@router.get(
    "/me/sesiones",
    response_model=list[SesionResponse],
    summary="Listar sesiones activas",
    description="Devuelve la lista de sesiones y dispositivos conectados del usuario actual.",
)
async def listar_mis_sesiones(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now(UTC)
    result = await session.execute(
        select(RefreshTokenModel)
        .where(
            RefreshTokenModel.user_id == current_user.id,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > now,
        )
        .order_by(RefreshTokenModel.created_at.desc())
    )
    tokens = result.scalars().all()
    sesiones: list[SesionResponse] = []
    for idx, token in enumerate(tokens):
        dispositivo = token.user_agent or "Navegador web"
        ip = token.ip_origen or "127.0.0.1"
        sesiones.append(
            SesionResponse(
                id=token.id,
                dispositivo=dispositivo,
                ip=ip,
                inicio=token.created_at,
                expira_en=token.expires_at,
                es_actual=(idx == 0),
            )
        )
    return sesiones


@router.delete(
    "/me/sesiones/{sesion_id}",
    response_model=MensajeResponse,
    summary="Cerrar una sesión",
    description="Cierra una sesión activa específica revocando su refresh token.",
)
async def cerrar_sesion_individual(
    sesion_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        update(RefreshTokenModel)
        .where(
            RefreshTokenModel.id == sesion_id,
            RefreshTokenModel.user_id == current_user.id,
            RefreshTokenModel.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o ya finalizada.")
    return MensajeResponse(mensaje="Sesión cerrada correctamente")


@router.delete(
    "/me/sesiones",
    response_model=MensajeResponse,
    summary="Cerrar todas las sesiones",
    description="Cierra todas las sesiones activas del usuario actual.",
)
async def cerrar_todas_las_sesiones(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await session.execute(
        update(RefreshTokenModel)
        .where(
            RefreshTokenModel.user_id == current_user.id,
            RefreshTokenModel.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
    return MensajeResponse(mensaje="Todas las sesiones fueron cerradas correctamente")


@router.get(
    "/me/actividad",
    response_model=list[ActividadResponse],
    summary="Mi actividad reciente",
    description="Devuelve las últimas 50 acciones del usuario autenticado registradas en la bitácora.",
)
async def obtener_mi_actividad(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(AuditLogModel)
        .where(AuditLogModel.user_id == current_user.id)
        .order_by(AuditLogModel.fecha.desc())
        .limit(50)
    )
    models = result.scalars().all()
    actividades: list[ActividadResponse] = []
    for model in models:
        try:
            detail = SqlAlchemyAuditLogRepository._to_detail(model)
            descripcion = detail.description
            ip = detail.source_ip
        except (AuditEncryptionError, AttributeError, KeyError, TypeError, ValueError):
            logger.debug("Actividad %s sin detalle descifrable; se usa la descripción cruda", model.id)
            descripcion = model.description or "Registro de actividad"
            ip = str(model.ip_origen) if model.ip_origen else None
        actividades.append(
            ActividadResponse(
                id=model.id,
                modulo=model.module,
                accion=model.action,
                descripcion=descripcion,
                ip_origen=ip,
                fecha=model.fecha,
            )
        )
    return actividades


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
            empresa_id=_target_empresa(current_user, empresa_id),
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
        target_empresa = _target_empresa(current_user, empresa_id)
        if target_empresa is not None:
            await SubscriptionPolicy(
                session, settings.subscription_grace_days
            ).require_user_capacity(target_empresa)
        user = await ActivarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=target_empresa,
        )
        await _events(session).activated(
            record_id=user.id, **_audit_context(http_request, current_user)
        )
        return user
    except SubscriptionPolicyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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


@router.delete(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Eliminar usuario",
    description=(
        "Elimina lógicamente la cuenta, desactiva su acceso y revoca sus sesiones sin "
        "borrar roles ni bitácora. No permite autoeliminación ni eliminar al último "
        "administrador activo. Permisos: `usuarios:eliminar` o "
        "`platform:usuarios:gestionar`."
    ),
    responses={409: {"description": "La cuenta no puede eliminarse en su estado actual."}},
)
async def eliminar_usuario(
    usuario_id: str,
    http_request: Request,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:eliminar", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        target_empresa = _target_empresa(current_user, empresa_id)
        user = await EliminarUsuario(
            _repository(session), SqlAlchemyAuthTokenRepository(session)
        ).execute(usuario_id, target_empresa, current_user.id)
        await _events(session).deleted(
            record_id=user.id,
            previous_data={"is_active": True},
            new_data={"is_active": False, "eliminado_at": str(user.eliminado_at)},
            **_audit_context(http_request, current_user),
        )
        return user
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch(
    "/{usuario_id}/restaurar",
    response_model=UsuarioResponse,
    summary="Restaurar usuario",
    description=(
        "Recupera una cuenta eliminada y la mantiene inactiva. Después debe usarse "
        "`/activar` para habilitar su acceso. Permisos: `usuarios:restaurar` o "
        "`platform:usuarios:gestionar`."
    ),
    responses={409: {"description": "La cuenta no está eliminada."}},
)
async def restaurar_usuario(
    usuario_id: str,
    http_request: Request,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("usuarios:restaurar", "platform:usuarios:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        user = await RestaurarUsuario(_repository(session)).execute(
            usuario_id, _target_empresa(current_user, empresa_id)
        )
        await _events(session).restored(
            record_id=user.id,
            new_data={"is_active": False, "eliminado_at": None},
            **_audit_context(http_request, current_user),
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


@router.get(
    "/{usuario_id}/foto",
    summary="Obtener foto de perfil",
    description="Retorna el archivo binario de la imagen de perfil del usuario o 404 si no existe.",
    responses={
        200: {"content": {"image/jpeg": {}}},
        404: {"description": "El usuario no tiene foto de perfil."},
    },
)
async def obtener_foto_usuario(usuario_id: str):
    path = get_avatar_path(usuario_id)
    if not path:
        raise HTTPException(status_code=404, detail="El usuario no tiene foto de perfil.")
    return FileResponse(path, media_type="image/jpeg")


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

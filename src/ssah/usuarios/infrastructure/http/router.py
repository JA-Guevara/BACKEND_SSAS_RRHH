from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ssah.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssah.core.security.dependencies import CurrentUser, require_permission
from ssah.infrastructure.database.session import get_session
from ssah.usuarios.application.use_cases.activar_usuario import ActivarUsuario
from ssah.usuarios.application.use_cases.actualizar_usuario import ActualizarUsuario
from ssah.usuarios.application.use_cases.crear_usuario import CrearUsuario
from ssah.usuarios.application.use_cases.desactivar_usuario import DesactivarUsuario
from ssah.usuarios.domain.exceptions import (
    InvalidRoleForEmpresaError,
    LastAdminCannotBeDisabledError,
    UsuarioAlreadyExistsError,
    UsuarioError,
    UsuarioNotFoundError,
    UsuarioWithoutRoleError,
)
from ssah.usuarios.infrastructure.http.schemas import (
    ActualizarUsuarioRequest,
    CrearUsuarioRequest,
    UsuarioResponse,
)
from ssah.usuarios.infrastructure.persistence.repositories.usuario_repository import (
    SqlAlchemyUsuarioRepository,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])
password_hasher = Argon2PasswordHasher()


def _repository(session: AsyncSession) -> SqlAlchemyUsuarioRepository:
    return SqlAlchemyUsuarioRepository(session)


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


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    request: CrearUsuarioRequest,
    current_user: CurrentUser = Depends(require_permission("usuarios:crear")),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await CrearUsuario(_repository(session), password_hasher).execute(
            empresa_id=current_user.empresa_id,
            **request.model_dump(),
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: str,
    request: ActualizarUsuarioRequest,
    current_user: CurrentUser = Depends(require_permission("usuarios:editar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        data = request.model_dump(exclude_unset=True)
        role_ids = data.pop("role_ids", None)
        return await ActualizarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=current_user.empresa_id,
            values=data,
            role_ids=role_ids,
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch("/{usuario_id}/activar", response_model=UsuarioResponse)
async def activar_usuario(
    usuario_id: str,
    current_user: CurrentUser = Depends(require_permission("usuarios:editar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await ActivarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=current_user.empresa_id,
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)


@router.patch("/{usuario_id}/desactivar", response_model=UsuarioResponse)
async def desactivar_usuario(
    usuario_id: str,
    current_user: CurrentUser = Depends(require_permission("usuarios:editar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await DesactivarUsuario(_repository(session)).execute(
            user_id=usuario_id,
            empresa_id=current_user.empresa_id,
        )
    except UsuarioError as exc:
        _raise_http_usuario_error(exc)
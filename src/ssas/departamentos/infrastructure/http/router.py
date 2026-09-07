from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.core.api.openapi import AUTHENTICATED_RESPONSES, EMPRESA_SCOPE_DESCRIPTION
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.departamentos.application.use_cases.actualizar_departamento import (
    ActualizarDepartamento,
)
from ssas.departamentos.application.use_cases.crear_departamento import CrearDepartamento
from ssas.departamentos.application.use_cases.eliminar_departamento import EliminarDepartamento
from ssas.departamentos.application.use_cases.listar_departamentos import ListarDepartamentos
from ssas.departamentos.domain.exceptions import (
    DepartamentoAlreadyExistsError,
    DepartamentoError,
    DepartamentoInUseError,
    DepartamentoNotFoundError,
)
from ssas.departamentos.infrastructure.http.schemas import (
    ActualizarDepartamentoRequest,
    CrearDepartamentoRequest,
    DepartamentoResponse,
)
from ssas.departamentos.infrastructure.persistence.repositories.departamento_repository import (
    SqlAlchemyDepartamentoRepository,
)
from ssas.infrastructure.database.session import get_session

TAG_DEPARTAMENTOS = "Departamentos"

router = APIRouter(
    prefix="/departamentos",
    tags=[TAG_DEPARTAMENTOS],
    responses=AUTHENTICATED_RESPONSES,
)


def _target_empresa(current_user: CurrentUser, requested: str | None) -> str:
    if current_user.es_plataforma:
        if requested is None:
            raise HTTPException(status_code=422, detail="Debe indicar empresa_id")
        return requested
    if requested is not None and requested != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No puedes operar sobre otra empresa")
    if current_user.empresa_id is None:
        raise HTTPException(status_code=403, detail="No tienes una empresa asignada")
    return current_user.empresa_id


def _repository(session: AsyncSession) -> SqlAlchemyDepartamentoRepository:
    return SqlAlchemyDepartamentoRepository(session)


def _raise_http_departamento_error(exc: DepartamentoError) -> None:
    if isinstance(exc, DepartamentoNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (DepartamentoAlreadyExistsError, DepartamentoInUseError)):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[DepartamentoResponse],
    summary="Listar departamentos",
    description=(
        "Lista departamentos del alcance autorizado. Permisos: `departamentos:ver` "
        "o `platform:organizacion:gestionar`."
    ),
)
async def listar_departamentos(
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    activo: bool | None = Query(default=None, description="Filtra por estado activo."),
    current_user: CurrentUser = Depends(
        require_scoped_permission("departamentos:ver", "platform:organizacion:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    return await ListarDepartamentos(_repository(session)).execute(
        _target_empresa(current_user, empresa_id), activo
    )


@router.post(
    "",
    response_model=DepartamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear departamento",
    description=(
        "Crea un departamento dentro de la empresa autorizada. Requiere "
        "`departamentos:crear` o `platform:organizacion:gestionar`."
    ),
    responses={409: {"description": "Ya existe un departamento con ese nombre."}},
)
async def crear_departamento(
    request: CrearDepartamentoRequest,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("departamentos:crear", "platform:organizacion:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await CrearDepartamento(_repository(session)).execute(
            empresa_id=_target_empresa(current_user, empresa_id),
            **request.model_dump(),
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="El departamento ya existe") from exc
    except DepartamentoError as exc:
        _raise_http_departamento_error(exc)


@router.put(
    "/{departamento_id}",
    response_model=DepartamentoResponse,
    summary="Actualizar departamento",
    description=(
        "Actualiza un departamento de la empresa autorizada. Requiere "
        "`departamentos:editar` o `platform:organizacion:gestionar`."
    ),
    responses={
        404: {"description": "Departamento no encontrado."},
        409: {"description": "Ya existe un departamento con ese nombre."},
    },
)
async def actualizar_departamento(
    departamento_id: str,
    request: ActualizarDepartamentoRequest,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("departamentos:editar", "platform:organizacion:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await ActualizarDepartamento(_repository(session)).execute(
            departamento_id,
            _target_empresa(current_user, empresa_id),
            request.model_dump(exclude_unset=True),
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="El departamento ya existe") from exc
    except DepartamentoError as exc:
        _raise_http_departamento_error(exc)


@router.delete(
    "/{departamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar departamento",
    description=(
        "Elimina un departamento sin dependencias dentro de la empresa autorizada. "
        "Requiere `departamentos:eliminar` o `platform:organizacion:gestionar`."
    ),
    responses={
        404: {"description": "Departamento no encontrado."},
        409: {"description": "El departamento tiene dependencias."},
    },
)
async def eliminar_departamento(
    departamento_id: str,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("departamentos:eliminar", "platform:organizacion:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        await EliminarDepartamento(_repository(session)).execute(
            departamento_id, _target_empresa(current_user, empresa_id)
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="El departamento tiene dependencias") from exc
    except DepartamentoError as exc:
        _raise_http_departamento_error(exc)

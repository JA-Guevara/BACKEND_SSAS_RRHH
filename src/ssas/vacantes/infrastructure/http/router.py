from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.core.api.openapi import EMPRESA_SCOPE_DESCRIPTION, TAG_VACANTES
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.infrastructure.database.session import get_session
from ssas.vacantes.application.use_cases.gestionar_vacantes import GestionarVacantes
from ssas.vacantes.domain.exceptions import (
    VacanteError,
    VacanteInvalidStateError,
    VacanteNotFoundError,
    VacanteReferenceError,
)
from ssas.vacantes.infrastructure.http.schemas import (
    ActualizarVacanteRequest,
    CrearVacanteRequest,
    VacantePublicaResponse,
    VacanteResponse,
)
from ssas.vacantes.infrastructure.persistence.repositories.vacante_repository import (
    SqlAlchemyVacanteRepository,
)

router = APIRouter(prefix="/vacantes", tags=[TAG_VACANTES])
public_router = APIRouter(prefix="/publico", tags=["Portal público"])


def _empresa(current_user: CurrentUser, requested: str | None) -> str:
    if current_user.es_plataforma:
        if requested is None:
            raise HTTPException(status_code=422, detail="Debe indicar empresa_id")
        return requested
    if current_user.empresa_id is None:
        raise HTTPException(status_code=403, detail="No tienes una empresa asignada")
    if requested is not None and requested != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No puedes operar sobre otra empresa")
    return current_user.empresa_id


def _service(session: AsyncSession) -> GestionarVacantes:
    return GestionarVacantes(SqlAlchemyVacanteRepository(session))


def _raise(exc: VacanteError) -> None:
    if isinstance(exc, VacanteNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (VacanteInvalidStateError, VacanteReferenceError)):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[VacanteResponse],
    summary="Listar vacantes",
    description="Lista las vacantes del alcance autorizado.",
)
async def listar_vacantes(
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    estado: str | None = Query(default=None),
    current_user: CurrentUser = Depends(
        require_scoped_permission("vacantes:ver", "platform:vacantes:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    return await _service(session).listar(_empresa(current_user, empresa_id), estado)


@router.post(
    "",
    response_model=VacanteResponse,
    status_code=status.HTTP_201_CREATED,
    description="Crea una vacante en la empresa autorizada.",
)
async def crear_vacante(
    request: CrearVacanteRequest,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("vacantes:crear", "platform:vacantes:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await _service(session).crear(
            _empresa(current_user, empresa_id), current_user.id, request.model_dump()
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="No se pudo crear la vacante") from exc
    except VacanteError as exc:
        _raise(exc)


@router.get(
    "/{vacante_id}",
    response_model=VacanteResponse,
    description="Obtiene una vacante de la empresa autorizada.",
)
async def obtener_vacante(
    vacante_id: str,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("vacantes:ver", "platform:vacantes:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await _service(session).obtener(vacante_id, _empresa(current_user, empresa_id))
    except VacanteError as exc:
        _raise(exc)


@router.put(
    "/{vacante_id}",
    response_model=VacanteResponse,
    description="Actualiza una vacante que todavía está en borrador.",
)
async def actualizar_vacante(
    vacante_id: str,
    request: ActualizarVacanteRequest,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("vacantes:editar", "platform:vacantes:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await _service(session).actualizar(
            vacante_id,
            _empresa(current_user, empresa_id),
            request.model_dump(exclude_unset=True),
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="No se pudo actualizar la vacante") from exc
    except VacanteError as exc:
        _raise(exc)


@router.patch(
    "/{vacante_id}/publicar",
    response_model=VacanteResponse,
    description="Publica una vacante en el portal público.",
)
async def publicar_vacante(
    vacante_id: str,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("vacantes:publicar", "platform:vacantes:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await _service(session).publicar(vacante_id, _empresa(current_user, empresa_id))
    except VacanteError as exc:
        _raise(exc)


@router.delete(
    "/{vacante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Elimina una vacante que todavía no tiene publicaciones activas.",
)
async def eliminar_vacante(
    vacante_id: str,
    empresa_id: str | None = Query(default=None, description=EMPRESA_SCOPE_DESCRIPTION),
    current_user: CurrentUser = Depends(
        require_scoped_permission("vacantes:eliminar", "platform:vacantes:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        await _service(session).eliminar(vacante_id, _empresa(current_user, empresa_id))
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="La vacante tiene postulaciones") from exc
    except VacanteError as exc:
        _raise(exc)


@public_router.get(
    "/{empresa_slug}/vacantes",
    response_model=list[VacantePublicaResponse],
    summary="Listar vacantes públicas",
    description="Lista vacantes publicadas y vigentes de una empresa.",
)
async def listar_vacantes_publicas(
    empresa_slug: str,
    ubicacion: str | None = Query(default=None),
    modalidad: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    return await _service(session).listar_publicas(empresa_slug, ubicacion, modalidad)


@public_router.get(
    "/{empresa_slug}/vacantes/{vacante_id}",
    response_model=VacantePublicaResponse,
    summary="Consultar vacante pública",
    description="Obtiene el detalle público de una vacante vigente.",
)
async def obtener_vacante_publica(
    empresa_slug: str,
    vacante_id: str,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await _service(session).obtener_publica(empresa_slug, vacante_id)
    except VacanteNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Vacante no encontrada") from exc

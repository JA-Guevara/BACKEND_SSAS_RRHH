from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.core.api.openapi import TAG_VACANTES
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.habilidades.infrastructure.persistence.models.habilidad import HabilidadModel
from ssas.infrastructure.database.session import get_session

router = APIRouter(prefix="/habilidades", tags=[TAG_VACANTES])


class HabilidadRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    categoria: str | None = Field(default=None, max_length=120)
    descripcion: str | None = None
    activo: bool = True


class HabilidadResponse(HabilidadRequest):
    id: str
    empresa_id: str


def _empresa(user: CurrentUser, requested: str | None) -> str:
    if user.es_plataforma:
        if requested is None:
            raise HTTPException(status_code=422, detail="Debe indicar empresa_id")
        return requested
    if user.empresa_id is None:
        raise HTTPException(status_code=403, detail="No tienes una empresa asignada")
    if requested and requested != user.empresa_id:
        raise HTTPException(status_code=403, detail="No puedes operar sobre otra empresa")
    return user.empresa_id


@router.get("", response_model=list[HabilidadResponse], description="Lista las habilidades de la empresa.")
async def listar_habilidades(
    empresa_id: str | None = Query(default=None),
    activo: bool | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("habilidades:ver", "platform:habilidades:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    conditions = [HabilidadModel.empresa_id == _empresa(user, empresa_id)]
    if activo is not None:
        conditions.append(HabilidadModel.activo.is_(activo))
    result = await session.execute(select(HabilidadModel).where(*conditions).order_by(HabilidadModel.nombre))
    return result.scalars().all()


@router.post(
    "",
    response_model=HabilidadResponse,
    status_code=status.HTTP_201_CREATED,
    description="Crea una habilidad para la empresa autorizada.",
)
async def crear_habilidad(
    request: HabilidadRequest,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("habilidades:gestionar", "platform:habilidades:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    model = HabilidadModel(empresa_id=_empresa(user, empresa_id), **request.model_dump())
    session.add(model)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="La habilidad ya existe") from exc
    return model


@router.put(
    "/{habilidad_id}",
    response_model=HabilidadResponse,
    summary="Actualizar habilidad",
    description="Actualiza una habilidad de la empresa autorizada.",
    responses={
        404: {"description": "La habilidad no existe en la empresa autorizada."},
        409: {"description": "Ya existe otra habilidad con ese nombre en la empresa."},
    },
)
async def actualizar_habilidad(
    habilidad_id: str,
    request: HabilidadRequest,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("habilidades:gestionar", "platform:habilidades:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    model = await session.scalar(
        select(HabilidadModel).where(
            HabilidadModel.id == habilidad_id,
            HabilidadModel.empresa_id == _empresa(user, empresa_id),
        )
    )
    if model is None:
        raise HTTPException(status_code=404, detail="Habilidad no encontrada")
    for campo, valor in request.model_dump().items():
        setattr(model, campo, valor)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="La habilidad ya existe") from exc
    return model


@router.delete(
    "/{habilidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Elimina una habilidad de la empresa autorizada.",
)
async def eliminar_habilidad(
    habilidad_id: str,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("habilidades:gestionar", "platform:habilidades:gestionar")
    ),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        delete(HabilidadModel).where(
            HabilidadModel.id == habilidad_id,
            HabilidadModel.empresa_id == _empresa(user, empresa_id),
        )
    )
    await session.flush()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Habilidad no encontrada")

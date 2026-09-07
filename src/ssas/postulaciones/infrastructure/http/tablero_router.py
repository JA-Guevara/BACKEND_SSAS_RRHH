from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.infrastructure.database.session import get_session
from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
    EtapaReclutamientoModel,
)
from ssas.postulaciones.infrastructure.persistence.models.motivo_rechazo import MotivoRechazoModel
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel

router = APIRouter(tags=["Postulaciones"])


class TableroItem(BaseModel):
    id: str
    vacante_id: str
    postulante_id: str
    postulante: str
    email: str
    etapa: str
    etapa_id: str
    estado: str
    motivo_rechazo: str | None
    codigo_seguimiento: str
    fecha_postulacion: datetime


class EtapaResponse(BaseModel):
    id: str
    nombre: str
    orden: int
    color: str | None
    es_inicial: bool
    es_contratado: bool
    es_rechazado: bool


class MotivoResponse(BaseModel):
    id: str
    nombre: str
    descripcion: str | None
    activo: bool


class CambiarEtapaRequest(BaseModel):
    etapa_id: str


class RechazarRequest(BaseModel):
    motivo_rechazo_id: str


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


async def _items(
    session: AsyncSession,
    empresa_id: str,
    vacante_id: str | None = None,
    postulacion_id: str | None = None,
):
    conditions = [VacanteModel.empresa_id == empresa_id]
    if vacante_id:
        conditions.append(VacanteModel.id == vacante_id)
    if postulacion_id:
        conditions.append(PostulacionModel.id == postulacion_id)
    result = await session.execute(
        select(PostulacionModel, PostulanteModel, EtapaReclutamientoModel, MotivoRechazoModel)
        .join(VacanteModel, VacanteModel.id == PostulacionModel.vacante_id)
        .join(PostulanteModel, PostulanteModel.id == PostulacionModel.postulante_id)
        .join(EtapaReclutamientoModel, EtapaReclutamientoModel.id == PostulacionModel.etapa_id)
        .outerjoin(MotivoRechazoModel, MotivoRechazoModel.id == PostulacionModel.motivo_rechazo_id)
        .where(*conditions)
        .order_by(PostulacionModel.fecha_postulacion.desc())
    )
    return [
        TableroItem(
            id=postulacion.id,
            vacante_id=postulacion.vacante_id,
            postulante_id=postulante.id,
            postulante=f"{postulante.nombres} {postulante.apellidos}",
            email=postulante.email,
            etapa=etapa.nombre,
            etapa_id=etapa.id,
            estado=postulacion.estado,
            motivo_rechazo=motivo.nombre if motivo else None,
            codigo_seguimiento=postulacion.codigo_seguimiento,
            fecha_postulacion=postulacion.fecha_postulacion,
        )
        for postulacion, postulante, etapa, motivo in result.all()
    ]


@router.get("/vacantes/{vacante_id}/tablero", response_model=list[TableroItem], description="Lista candidatos de una vacante dentro de la empresa autorizada.")
async def tablero(
    vacante_id: str,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:ver", "platform:postulaciones:ver")),
    session: AsyncSession = Depends(get_session),
):
    empresa = _empresa(user, empresa_id)
    exists = await session.scalar(select(VacanteModel.id).where(VacanteModel.id == vacante_id, VacanteModel.empresa_id == empresa))
    if exists is None:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")
    return await _items(session, empresa, vacante_id)


@router.get("/postulaciones", response_model=list[TableroItem], description="Lista postulaciones de la empresa autorizada.")
async def postulaciones(
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:ver", "platform:postulaciones:ver")),
    session: AsyncSession = Depends(get_session),
):
    return await _items(session, _empresa(user, empresa_id))


@router.get("/etapas-reclutamiento", response_model=list[EtapaResponse], description="Lista las etapas de reclutamiento de la empresa.")
async def etapas(
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:ver", "platform:postulaciones:ver")),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(EtapaReclutamientoModel).where(EtapaReclutamientoModel.empresa_id == _empresa(user, empresa_id)).order_by(EtapaReclutamientoModel.orden))
    return result.scalars().all()


@router.get("/motivos-rechazo", response_model=list[MotivoResponse], description="Lista los motivos de rechazo de la empresa.")
async def motivos(
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:ver", "platform:postulaciones:ver")),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(MotivoRechazoModel).where(MotivoRechazoModel.empresa_id == _empresa(user, empresa_id), MotivoRechazoModel.activo.is_(True)).order_by(MotivoRechazoModel.nombre))
    return result.scalars().all()


@router.patch("/postulaciones/{postulacion_id}/etapa", response_model=TableroItem, description="Mueve una postulación a otra etapa de la empresa.")
async def cambiar_etapa(
    postulacion_id: str,
    request: CambiarEtapaRequest,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:gestionar", "platform:postulaciones:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    empresa = _empresa(user, empresa_id)
    valid = await session.scalar(select(EtapaReclutamientoModel.id).where(EtapaReclutamientoModel.id == request.etapa_id, EtapaReclutamientoModel.empresa_id == empresa))
    if valid is None:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    result = await session.execute(update(PostulacionModel).where(PostulacionModel.id == postulacion_id, PostulacionModel.vacante_id.in_(select(VacanteModel.id).where(VacanteModel.empresa_id == empresa))).values(etapa_id=request.etapa_id, fecha_ultimo_cambio=datetime.now(UTC)))
    await session.flush()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Postulacion no encontrada")
    return (await _items(session, empresa, postulacion_id=postulacion_id))[0]


@router.patch("/postulaciones/{postulacion_id}/rechazar", response_model=TableroItem, description="Rechaza una postulación con un motivo de la empresa.")
async def rechazar(
    postulacion_id: str,
    request: RechazarRequest,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:gestionar", "platform:postulaciones:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    empresa = _empresa(user, empresa_id)
    valid = await session.scalar(select(MotivoRechazoModel.id).where(MotivoRechazoModel.id == request.motivo_rechazo_id, MotivoRechazoModel.empresa_id == empresa))
    if valid is None:
        raise HTTPException(status_code=404, detail="Motivo de rechazo no encontrado")
    result = await session.execute(update(PostulacionModel).where(PostulacionModel.id == postulacion_id, PostulacionModel.vacante_id.in_(select(VacanteModel.id).where(VacanteModel.empresa_id == empresa))).values(motivo_rechazo_id=request.motivo_rechazo_id, estado="DESCARTADA", fecha_ultimo_cambio=datetime.now(UTC)))
    await session.flush()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Postulacion no encontrada")
    return (await _items(session, empresa, postulacion_id=postulacion_id))[0]

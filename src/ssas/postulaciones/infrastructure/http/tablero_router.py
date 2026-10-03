from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.bitacora.application.events.postulacion_events import PostulacionEvents
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.core.api.request_metadata import get_client_ip
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.infrastructure.database.session import get_session
from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
    EtapaReclutamientoModel,
)
from ssas.postulaciones.infrastructure.persistence.models.motivo_rechazo import MotivoRechazoModel
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulaciones.infrastructure.persistence.models.postulacion_nota import (
    PostulacionNotaModel,
)
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
    puntaje_manual: Decimal | None
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


class PuntajeRequest(BaseModel):
    puntaje: Decimal = Field(ge=0, le=100, description="Puntaje manual de 0 a 100.")


class NotaRequest(BaseModel):
    contenido: str = Field(min_length=1, max_length=4000)


class NotaResponse(BaseModel):
    id: str
    postulacion_id: str
    usuario_id: str
    autor: str
    contenido: str
    created_at: datetime


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


def _audit_context(request: Request, user: CurrentUser) -> dict[str, str | None]:
    return {
        "empresa_id": user.empresa_id,
        "user_id": user.id,
        "source_ip": get_client_ip(request),
        "user_agent": request.headers.get("user-agent"),
    }


def _events(session: AsyncSession) -> PostulacionEvents:
    repository = SqlAlchemyAuditLogRepository(session)
    return PostulacionEvents(RegisterAuditEvent(repository))


async def _verificar_postulacion(
    session: AsyncSession, postulacion_id: str, empresa_id: str
) -> None:
    """Confirma que la postulación pertenece a la empresa autorizada.

    ``postulacion`` no tiene ``empresa_id``: la pertenencia se resuelve siempre por
    ``vacante.empresa_id``. Sin esta comprobación, cualquier usuario podría leer o
    escribir notas de otra empresa conociendo un identificador.
    """
    encontrada = await session.scalar(
        select(PostulacionModel.id)
        .join(VacanteModel, VacanteModel.id == PostulacionModel.vacante_id)
        .where(PostulacionModel.id == postulacion_id, VacanteModel.empresa_id == empresa_id)
    )
    if encontrada is None:
        raise HTTPException(status_code=404, detail="Postulacion no encontrada")


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
            puntaje_manual=postulacion.puntaje_manual,
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
    http_request: Request,
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
    item = (await _items(session, empresa, postulacion_id=postulacion_id))[0]
    await _events(session).etapa_cambiada(
        record_id=postulacion_id,
        new_data={"etapa_id": request.etapa_id},
        **_audit_context(http_request, user),
    )
    return item


@router.patch("/postulaciones/{postulacion_id}/rechazar", response_model=TableroItem, description="Rechaza una postulación con un motivo de la empresa.")
async def rechazar(
    postulacion_id: str,
    request: RechazarRequest,
    http_request: Request,
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
    item = (await _items(session, empresa, postulacion_id=postulacion_id))[0]
    await _events(session).rechazada(
        record_id=postulacion_id,
        new_data={"motivo_rechazo_id": request.motivo_rechazo_id},
        **_audit_context(http_request, user),
    )
    return item


@router.patch(
    "/postulaciones/{postulacion_id}/puntaje",
    response_model=TableroItem,
    summary="Registrar puntaje de postulación",
    description="Registra el puntaje manual (0 a 100) de una postulación de la empresa autorizada.",
    responses={404: {"description": "La postulación no existe en la empresa autorizada."}},
)
async def registrar_puntaje(
    postulacion_id: str,
    request: PuntajeRequest,
    http_request: Request,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:gestionar", "platform:postulaciones:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    empresa = _empresa(user, empresa_id)
    result = await session.execute(update(PostulacionModel).where(PostulacionModel.id == postulacion_id, PostulacionModel.vacante_id.in_(select(VacanteModel.id).where(VacanteModel.empresa_id == empresa))).values(puntaje_manual=request.puntaje, fecha_ultimo_cambio=datetime.now(UTC)))
    await session.flush()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Postulacion no encontrada")
    item = (await _items(session, empresa, postulacion_id=postulacion_id))[0]
    await _events(session).puntaje_asignado(
        record_id=postulacion_id,
        new_data={"puntaje": float(request.puntaje)},
        **_audit_context(http_request, user),
    )
    return item


@router.get(
    "/postulaciones/{postulacion_id}/notas",
    response_model=list[NotaResponse],
    summary="Listar notas internas",
    description="Lista las notas internas de una postulación de la empresa autorizada.",
    responses={404: {"description": "La postulación no existe en la empresa autorizada."}},
)
async def listar_notas(
    postulacion_id: str,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:ver", "platform:postulaciones:ver")),
    session: AsyncSession = Depends(get_session),
):
    await _verificar_postulacion(session, postulacion_id, _empresa(user, empresa_id))
    result = await session.execute(
        select(PostulacionNotaModel, UserModel.name, UserModel.apellido)
        .join(UserModel, UserModel.id == PostulacionNotaModel.usuario_id)
        .where(PostulacionNotaModel.postulacion_id == postulacion_id)
        .order_by(PostulacionNotaModel.created_at.desc())
    )
    return [
        NotaResponse(
            id=nota.id,
            postulacion_id=nota.postulacion_id,
            usuario_id=nota.usuario_id,
            autor=f"{nombre} {apellido}".strip(),
            contenido=nota.contenido,
            created_at=nota.created_at,
        )
        for nota, nombre, apellido in result.all()
    ]


@router.post(
    "/postulaciones/{postulacion_id}/notas",
    response_model=NotaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar nota interna",
    description="Agrega una nota interna a una postulación de la empresa autorizada.",
    responses={404: {"description": "La postulación no existe en la empresa autorizada."}},
)
async def crear_nota(
    postulacion_id: str,
    request: NotaRequest,
    http_request: Request,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(require_scoped_permission("postulaciones:gestionar", "platform:postulaciones:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    await _verificar_postulacion(session, postulacion_id, _empresa(user, empresa_id))
    nota = PostulacionNotaModel(
        postulacion_id=postulacion_id,
        usuario_id=user.id,
        contenido=request.contenido.strip(),
    )
    session.add(nota)
    await session.flush()
    autor = await session.execute(
        select(UserModel.name, UserModel.apellido).where(UserModel.id == user.id)
    )
    nombre, apellido = autor.one()
    await _events(session).nota_creada(
        record_id=nota.id,
        new_data={"postulacion_id": postulacion_id},
        **_audit_context(http_request, user),
    )
    return NotaResponse(
        id=nota.id,
        postulacion_id=nota.postulacion_id,
        usuario_id=nota.usuario_id,
        autor=f"{nombre} {apellido}".strip(),
        contenido=nota.contenido,
        created_at=nota.created_at,
    )

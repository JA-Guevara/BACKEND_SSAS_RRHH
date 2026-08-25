from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ssas.core.security.dependencies import CurrentUser, require_permission
from ssas.empresas.application.use_cases.actualizar_parametro_empresa import (
    ActualizarParametroEmpresa,
)
from ssas.empresas.application.use_cases.listar_parametros_empresa import ListarParametrosEmpresa
from ssas.empresas.domain.exceptions import EmpresaError
from ssas.empresas.infrastructure.http.schemas import (
    ActualizarParametroEmpresaRequest,
    MiEmpresaUpdateRequest,
    ParametroEmpresaResponse,
)
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.empresas.infrastructure.persistence.models.suscripcion import SuscripcionModel
from ssas.empresas.infrastructure.persistence.repositories.parametro_repository import (
    SqlAlchemyParametroRepository,
)
from ssas.infrastructure.database.session import get_session
from ssas.platform.application.services import empresa_payload, subscription_payload
from ssas.platform.infrastructure.http.schemas import EmpresaResponse, SubscriptionResponse

router = APIRouter(prefix="/mi-empresa", tags=["mi-empresa"])


async def _get_empresa(session: AsyncSession, empresa_id: str):
    query = select(EmpresaModel).options(selectinload(EmpresaModel.suscripciones).selectinload(SuscripcionModel.plan)).where(EmpresaModel.id == empresa_id)
    return (await session.execute(query)).scalar_one_or_none()


@router.get("", response_model=EmpresaResponse)
async def get_my_empresa(current: CurrentUser = Depends(require_permission("empresa:ver")), session: AsyncSession = Depends(get_session)):
    empresa = await _get_empresa(session, current.empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa_payload(empresa)


@router.patch("", response_model=EmpresaResponse)
async def update_my_empresa(body: MiEmpresaUpdateRequest, current: CurrentUser = Depends(require_permission("empresa:editar")), session: AsyncSession = Depends(get_session)):
    values = body.model_dump(exclude_unset=True)
    await session.execute(update(EmpresaModel).where(EmpresaModel.id == current.empresa_id).values(**values))
    await session.flush()
    empresa = await _get_empresa(session, current.empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa_payload(empresa)


@router.get("/suscripcion", response_model=SubscriptionResponse)
async def get_my_subscription(current: CurrentUser = Depends(require_permission("empresa:ver")), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(SuscripcionModel).options(selectinload(SuscripcionModel.plan), selectinload(SuscripcionModel.empresa)).where(SuscripcionModel.empresa_id == current.empresa_id, SuscripcionModel.activo.is_(True)).order_by(SuscripcionModel.fecha_inicio.desc()))
    subscription = result.scalars().first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción activa no encontrada")
    return subscription_payload(subscription)


@router.get("/parametros", response_model=list[ParametroEmpresaResponse])
async def list_my_parameters(current: CurrentUser = Depends(require_permission("parametros:ver")), session: AsyncSession = Depends(get_session)):
    return await ListarParametrosEmpresa(SqlAlchemyParametroRepository(session)).execute(current.empresa_id)


@router.put("/parametros/{codigo}", response_model=ParametroEmpresaResponse)
async def update_my_parameter(codigo: str, body: ActualizarParametroEmpresaRequest, current: CurrentUser = Depends(require_permission("parametros:editar")), session: AsyncSession = Depends(get_session)):
    try:
        return await ActualizarParametroEmpresa(SqlAlchemyParametroRepository(session)).execute(empresa_id=current.empresa_id, codigo=codigo, **body.model_dump())
    except EmpresaError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

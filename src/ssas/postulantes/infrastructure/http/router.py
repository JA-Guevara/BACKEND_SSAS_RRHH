from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.infrastructure.database.session import get_session
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel

router = APIRouter(prefix="/postulantes", tags=["Postulaciones"])


class PostulanteResponse(BaseModel):
    id: str
    empresa_id: str
    nombres: str
    apellidos: str
    ci: str
    email: str
    telefono: str
    ciudad: str
    cv_url: str | None
    linkedin: str | None
    nivel_educativo: str
    anios_experiencia: int
    fuente: str
    en_banco_talento: bool


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


@router.get("", response_model=list[PostulanteResponse], description="Lista postulantes de la empresa autorizada.")
async def listar_postulantes(
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("postulantes:ver", "platform:postulantes:ver")
    ),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(PostulanteModel)
        .where(PostulanteModel.empresa_id == _empresa(user, empresa_id))
        .order_by(PostulanteModel.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{postulante_id}", response_model=PostulanteResponse, description="Obtiene un postulante sin salir de su empresa.")
async def obtener_postulante(
    postulante_id: str,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("postulantes:ver", "platform:postulantes:ver")
    ),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(PostulanteModel).where(
            PostulanteModel.id == postulante_id,
            PostulanteModel.empresa_id == _empresa(user, empresa_id),
        )
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Postulante no encontrado")
    return model

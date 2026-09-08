from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.infrastructure.database.session import get_session
from ssas.postulaciones.infrastructure.storage.local_cv_storage import LocalCvStorage
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel

router = APIRouter(prefix="/postulantes", tags=["Postulaciones"])

NivelEducativo = Literal["SECUNDARIA", "TECNICO", "LICENCIATURA", "MAESTRIA", "DOCTORADO"]
Fuente = Literal["PORTAL_WEB", "APP_MOVIL", "LINKEDIN", "REFERIDO", "FERIA", "OTRO"]


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


class CrearPostulanteRequest(BaseModel):
    """Alta manual en el banco de talento: los mismos datos del portal, sin CV obligatorio."""

    nombres: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=120)
    ci: str = Field(min_length=1, max_length=30)
    email: EmailStr
    telefono: str = Field(min_length=1, max_length=40)
    ciudad: str = Field(min_length=1, max_length=100)
    nivel_educativo: NivelEducativo
    anios_experiencia: int = Field(default=0, ge=0)
    linkedin: str | None = None
    cv_url: str | None = None
    fuente: Fuente = "OTRO"


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


@router.post(
    "",
    response_model=PostulanteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar postulante manualmente",
    description=(
        "Da de alta un postulante en el banco de talento de la empresa autorizada. "
        "El CV es opcional porque el registro suele venir de una feria o un referido."
    ),
    responses={409: {"description": "Ya existe un postulante con ese CI en la empresa."}},
)
async def crear_postulante(
    request: CrearPostulanteRequest,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("postulantes:gestionar", "platform:postulantes:ver")
    ),
    session: AsyncSession = Depends(get_session),
):
    datos = request.model_dump()
    datos["email"] = str(datos["email"])
    model = PostulanteModel(
        empresa_id=_empresa(user, empresa_id),
        en_banco_talento=True,
        **datos,
    )
    session.add(model)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Ya existe un postulante con ese CI en la empresa"
        ) from exc
    return model


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


@router.get(
    "/{postulante_id}/cv",
    response_class=FileResponse,
    summary="Descargar CV del postulante",
    description=(
        "Descarga el archivo de hoja de vida almacenado para un postulante de la "
        "empresa autorizada."
    ),
    responses={
        200: {"description": "Archivo de CV.", "content": {"application/pdf": {}}},
        404: {"description": "El postulante no existe o no tiene un CV disponible."},
    },
)
async def descargar_cv(
    postulante_id: str,
    empresa_id: str | None = Query(default=None),
    user: CurrentUser = Depends(
        require_scoped_permission("postulantes:ver", "platform:postulantes:ver")
    ),
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    result = await session.execute(
        select(PostulanteModel.cv_url).where(
            PostulanteModel.id == postulante_id,
            PostulanteModel.empresa_id == _empresa(user, empresa_id),
        )
    )
    fila = result.one_or_none()
    if fila is None:
        raise HTTPException(status_code=404, detail="Postulante no encontrado")
    if fila.cv_url is None:
        raise HTTPException(status_code=404, detail="El postulante no tiene un CV registrado")
    cv_url = fila.cv_url

    almacen = LocalCvStorage()
    archivo = almacen.resolve_cv(cv_url)
    if archivo is None:
        raise HTTPException(
            status_code=404, detail="El archivo de CV ya no está disponible en el almacenamiento"
        )
    return FileResponse(
        path=archivo,
        media_type=almacen.content_type(archivo),
        filename=archivo.name,
    )

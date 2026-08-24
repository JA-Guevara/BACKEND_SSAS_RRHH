from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ssah.core.security.dependencies import CurrentUser, require_permission
from ssah.empresas.application.use_cases.actualizar_parametro_empresa import (
    ActualizarParametroEmpresa,
)
from ssah.empresas.application.use_cases.listar_parametros_empresa import ListarParametrosEmpresa
from ssah.empresas.domain.exceptions import (
    EmpresaError,
    ParametroLegalNotFoundError,
    ParametroValorInvalidoError,
    ParametroVigenciaInvalidaError,
)
from ssah.empresas.infrastructure.http.schemas import (
    ActualizarParametroEmpresaRequest,
    ParametroEmpresaResponse,
)
from ssah.empresas.infrastructure.persistence.repositories.parametro_repository import (
    SqlAlchemyParametroRepository,
)
from ssah.infrastructure.database.session import get_session

router = APIRouter(prefix="/empresa", tags=["empresa"])


def _repository(session: AsyncSession) -> SqlAlchemyParametroRepository:
    return SqlAlchemyParametroRepository(session)


def _raise_http_empresa_error(exc: EmpresaError) -> None:
    if isinstance(exc, ParametroLegalNotFoundError):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (ParametroValorInvalidoError, ParametroVigenciaInvalidaError)):
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("/parametros", response_model=list[ParametroEmpresaResponse])
async def listar_parametros_empresa(
    current_user: CurrentUser = Depends(require_permission("parametros:ver")),
    session: AsyncSession = Depends(get_session),
):
    return await ListarParametrosEmpresa(_repository(session)).execute(current_user.empresa_id)


@router.put("/parametros/{codigo}", response_model=ParametroEmpresaResponse)
async def actualizar_parametro_empresa(
    codigo: str,
    request: ActualizarParametroEmpresaRequest,
    current_user: CurrentUser = Depends(require_permission("parametros:editar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await ActualizarParametroEmpresa(_repository(session)).execute(
            empresa_id=current_user.empresa_id,
            codigo=codigo,
            **request.model_dump(),
        )
    except EmpresaError as exc:
        _raise_http_empresa_error(exc)
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.application.services.auth_email_service import AuthEmailService
from ssas.auth.domain.exceptions import EmailDeliveryError
from ssas.auth.infrastructure.email.smtp_sender import SMTPEmailSender
from ssas.config.settings import settings
from ssas.core.security.dependencies import CurrentUser, require_empresa_permission
from ssas.infrastructure.database.session import get_session
from ssas.platform.application.services import empresa_payload, page_payload
from ssas.platform.application.use_cases.provision_empresa import ProvisionEmpresa
from ssas.platform.domain.exceptions import (
    PlatformConflictError,
    PlatformError,
    PlatformNotFoundError,
)
from ssas.platform.infrastructure.http.dependencies import (
    CurrentPlatformAdmin,
    require_platform_permission,
)
from ssas.platform.infrastructure.http.schemas import (
    EmpresaPageResponse,
    EmpresaResponse,
    EmpresaUpdateRequest,
    ProvisionEmpresaRequest,
    ProvisionEmpresaResponse,
)
from ssas.platform.infrastructure.persistence.repositories.platform_repository import (
    PlatformRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/empresas", tags=["empresas"])
email_service = AuthEmailService(SMTPEmailSender(), settings.app_frontend_url)


def _repo(session: AsyncSession) -> PlatformRepository:
    return PlatformRepository(session)


def _request_data(request: Request) -> dict[str, str | None]:
    return {
        "ip_origen": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


async def _audit(
    session: AsyncSession,
    request: Request,
    admin: CurrentPlatformAdmin | None,
    *,
    module: str,
    action: str,
    description: str,
    table: str | None = None,
    record_id: str | None = None,
    previous: dict | None = None,
    new: dict | None = None,
) -> None:
    await _repo(session).add_audit(
        admin_id=admin.id if admin else None,
        actor_etiqueta=admin.id if admin else None,
        modulo=module,
        accion=action,
        nivel="WARNING" if action in {"LOGIN_FAILED", "SUSPEND", "DELETE"} else "INFO",
        descripcion=description,
        tabla_afectada=table,
        registro_id=record_id,
        datos_previos=previous,
        datos_nuevos=new,
        **_request_data(request),
    )


def _raise_platform(exc: PlatformError) -> None:
    code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(exc, PlatformNotFoundError)
        else status.HTTP_409_CONFLICT
        if isinstance(exc, PlatformConflictError)
        else status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("", response_model=EmpresaPageResponse)
async def list_empresas(
    search: str | None = Query(default=None, max_length=150),
    activo: bool | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    _: CurrentPlatformAdmin = Depends(require_platform_permission("platform:empresas:ver")),
    session: AsyncSession = Depends(get_session),
):
    items, total = await _repo(session).list_empresas(search, activo, page, per_page)
    return page_payload([empresa_payload(item) for item in items], total, page, per_page)


@router.post("", response_model=ProvisionEmpresaResponse, status_code=201)
async def provision_empresa(
    body: ProvisionEmpresaRequest,
    request: Request,
    current: CurrentPlatformAdmin = Depends(require_platform_permission("platform:empresas:crear")),
    session: AsyncSession = Depends(get_session),
):
    try:
        empresa, admin, raw_token = await ProvisionEmpresa(session).execute(body)
        sent = True
        try:
            await email_service.send_email_verification(admin.email, raw_token)
        except EmailDeliveryError:
            sent = False
            logger.exception("Empresa creada, pero no se pudo enviar la verificación")
        await _audit(
            session,
            request,
            current,
            module="EMPRESAS",
            action="CREATE",
            description="Empresa aprovisionada",
            table="empresa",
            record_id=empresa.id,
            new={"slug": empresa.slug, "admin_email": admin.email},
        )
        return {
            "empresa": empresa_payload(empresa),
            "administrador_id": admin.id,
            "administrador_email": admin.email,
            "verification_email_sent": sent,
        }
    except PlatformError as exc:
        _raise_platform(exc)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="La empresa o su administrador ya existe"
        ) from exc


@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def get_empresa(
    empresa_id: str,
    _: CurrentUser = Depends(require_empresa_permission("empresa:ver", "platform:empresas:ver")),
    session: AsyncSession = Depends(get_session),
):
    empresa = await _repo(session).get_empresa(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa_payload(empresa)


@router.patch("/{empresa_id}", response_model=EmpresaResponse)
async def update_empresa(
    empresa_id: str,
    body: EmpresaUpdateRequest,
    request: Request,
    current: CurrentUser = Depends(
        require_empresa_permission("empresa:editar", "platform:empresas:editar")
    ),
    session: AsyncSession = Depends(get_session),
):
    repository = _repo(session)
    existing = await repository.get_empresa(empresa_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    values = body.model_dump(exclude_unset=True)
    if "email" in values and values["email"] is not None:
        values["email"] = str(values["email"])
    if values.get("slug"):
        values["slug"] = values["slug"].lower()
    try:
        empresa = await repository.update_empresa(empresa_id, values)
        await _audit(
            session,
            request,
            current,
            module="EMPRESAS",
            action="UPDATE",
            description="Empresa actualizada",
            table="empresa",
            record_id=empresa_id,
            new=values,
        )
        return empresa_payload(empresa)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="NIT o slug ya utilizado") from exc


async def _set_empresa_status(
    empresa_id: str,
    active: bool,
    request: Request,
    current: CurrentPlatformAdmin,
    session: AsyncSession,
):
    repository = _repo(session)
    if not await repository.get_empresa(empresa_id):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    empresa = await repository.update_empresa(empresa_id, {"activo": active})
    action = "ACTIVATE" if active else "SUSPEND"
    await _audit(
        session,
        request,
        current,
        module="EMPRESAS",
        action=action,
        description="Empresa activada" if active else "Empresa suspendida",
        table="empresa",
        record_id=empresa_id,
    )
    return empresa_payload(empresa)


@router.patch("/{empresa_id}/activar", response_model=EmpresaResponse)
async def activate_empresa(
    empresa_id: str,
    request: Request,
    current: CurrentPlatformAdmin = Depends(
        require_platform_permission("platform:empresas:suspender")
    ),
    session: AsyncSession = Depends(get_session),
):
    return await _set_empresa_status(empresa_id, True, request, current, session)


@router.patch("/{empresa_id}/suspender", response_model=EmpresaResponse)
async def suspend_empresa(
    empresa_id: str,
    request: Request,
    current: CurrentPlatformAdmin = Depends(
        require_platform_permission("platform:empresas:suspender")
    ),
    session: AsyncSession = Depends(get_session),
):
    return await _set_empresa_status(empresa_id, False, request, current, session)

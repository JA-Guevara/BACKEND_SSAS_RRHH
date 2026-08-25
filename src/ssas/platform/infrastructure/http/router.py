import logging
from datetime import UTC, datetime
from hmac import compare_digest

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.auth.application.services.auth_email_service import AuthEmailService
from ssas.auth.domain.exceptions import EmailDeliveryError, InvalidPasswordError
from ssas.auth.domain.password_policy import validate_password
from ssas.auth.infrastructure.email.smtp_sender import SMTPEmailSender
from ssas.auth.infrastructure.security.password_hasher import Argon2PasswordHasher
from ssas.config.settings import settings
from ssas.infrastructure.database.session import AsyncSessionLocal, get_session
from ssas.platform.application.services import empresa_payload, page_payload, subscription_payload
from ssas.platform.application.use_cases.provision_empresa import ProvisionEmpresa
from ssas.platform.domain.exceptions import (
    PlatformConflictError,
    PlatformError,
    PlatformNotFoundError,
)
from ssas.platform.infrastructure.http.dependencies import (
    CurrentPlatformAdmin,
    get_current_platform_admin,
)
from ssas.platform.infrastructure.http.schemas import (
    EmpresaPageResponse,
    EmpresaResponse,
    EmpresaUpdateRequest,
    MessageResponse,
    PlanCreateRequest,
    PlanResponse,
    PlanUpdateRequest,
    PlatformAdminResponse,
    PlatformAuditPageResponse,
    PlatformAuditResponse,
    PlatformChangePasswordRequest,
    PlatformLoginRequest,
    PlatformRefreshRequest,
    PlatformTokenResponse,
    ProvisionEmpresaRequest,
    ProvisionEmpresaResponse,
    SubscriptionPageResponse,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)
from ssas.platform.infrastructure.persistence.repositories.platform_repository import (
    PlatformRepository,
)
from ssas.platform.infrastructure.security.jwt_service import PlatformJWTService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/platform", tags=["platform"])
tokens = PlatformJWTService()
password_hasher = Argon2PasswordHasher()
email_service = AuthEmailService(SMTPEmailSender(), settings.app_frontend_url)


def _repo(session: AsyncSession) -> PlatformRepository:
    return PlatformRepository(session)


def _request_data(request: Request) -> dict[str, str | None]:
    return {
        "ip_origen": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


async def _audit(session: AsyncSession, request: Request, admin: CurrentPlatformAdmin | None, *, module: str, action: str, description: str, table: str | None = None, record_id: str | None = None, previous: dict | None = None, new: dict | None = None) -> None:
    await _repo(session).add_audit(
        admin_id=admin.id if admin else None,
        actor_etiqueta=admin.email if admin else None,
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
    code = status.HTTP_404_NOT_FOUND if isinstance(exc, PlatformNotFoundError) else status.HTTP_409_CONFLICT if isinstance(exc, PlatformConflictError) else status.HTTP_422_UNPROCESSABLE_ENTITY
    raise HTTPException(status_code=code, detail=str(exc)) from exc


async def _issue_tokens(repository: PlatformRepository, admin_id: str) -> dict:
    access, expires_in = tokens.create_access_token(admin_id)
    refresh, token_id, expires_at = tokens.create_refresh_token(admin_id)
    await repository.save_refresh_token(admin_id, token_id, tokens.fingerprint(refresh), expires_at)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "expires_in": expires_in}


@router.post("/auth/login", response_model=PlatformTokenResponse)
async def platform_login(body: PlatformLoginRequest, request: Request, session: AsyncSession = Depends(get_session)):
    repository = _repo(session)
    admin = await repository.get_admin_by_login(body.login)
    if not admin:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if admin.bloqueado_hasta and admin.bloqueado_hasta > datetime.now(UTC):
        raise HTTPException(status_code=423, detail="Cuenta bloqueada temporalmente")
    if not password_hasher.verify(body.password, admin.password_hash):
        async with AsyncSessionLocal() as failure_session:
            failure_repo = _repo(failure_session)
            await failure_repo.record_failed_login(admin.id, settings.app_max_login_attempts, settings.app_login_lock_minutes)
            await _audit(failure_session, request, None, module="AUTH_PLATFORM", action="LOGIN_FAILED", description="Intento fallido de acceso a plataforma")
            await failure_session.commit()
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not admin.activo or not admin.email_verified:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    await repository.record_successful_login(admin.id)
    result = await _issue_tokens(repository, admin.id)
    current = CurrentPlatformAdmin(admin.id, admin.email, admin.username)
    await _audit(session, request, current, module="AUTH_PLATFORM", action="LOGIN", description="Inicio de sesión de plataforma")
    return result


@router.post("/auth/refresh", response_model=PlatformTokenResponse)
async def platform_refresh(body: PlatformRefreshRequest, session: AsyncSession = Depends(get_session)):
    try:
        payload = tokens.decode(body.refresh_token, "refresh")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Refresh token inválido") from exc
    admin_id, token_id = payload.get("sub"), payload.get("jti")
    if not isinstance(admin_id, str) or not isinstance(token_id, str):
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    repository = _repo(session)
    stored = await repository.get_refresh_token(token_id)
    admin = await repository.get_admin(admin_id)
    if (
        not stored
        or stored.admin_id != admin_id
        or not compare_digest(stored.token_hash, tokens.fingerprint(body.refresh_token))
        or not admin
        or not admin.activo
        or not admin.email_verified
        or (admin.bloqueado_hasta is not None and admin.bloqueado_hasta > datetime.now(UTC))
    ):
        raise HTTPException(status_code=401, detail="Refresh token revocado o inválido")
    await repository.revoke_refresh_token(token_id)
    return await _issue_tokens(repository, admin_id)


@router.post("/auth/logout", response_model=MessageResponse)
async def platform_logout(body: PlatformRefreshRequest, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    try:
        payload = tokens.decode(body.refresh_token, "refresh")
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Refresh token inválido") from exc
    if payload.get("sub") != current.id or not isinstance(payload.get("jti"), str):
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    await _repo(session).revoke_refresh_token(payload["jti"])
    await _audit(session, request, current, module="AUTH_PLATFORM", action="LOGOUT", description="Cierre de sesión de plataforma")
    return {"message": "Sesión de plataforma cerrada"}


@router.get("/auth/me", response_model=PlatformAdminResponse)
async def platform_me(current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    return await _repo(session).get_admin(current.id)


@router.post("/auth/password/change", response_model=MessageResponse)
async def platform_change_password(body: PlatformChangePasswordRequest, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    repository = _repo(session)
    admin = await repository.get_admin(current.id)
    if not admin or not password_hasher.verify(body.current_password, admin.password_hash):
        raise HTTPException(status_code=422, detail="La contraseña actual es incorrecta")
    if password_hasher.verify(body.new_password, admin.password_hash):
        raise HTTPException(status_code=422, detail="La contraseña nueva debe ser diferente")
    try:
        validate_password(body.new_password, admin.username, admin.email)
    except InvalidPasswordError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await repository.change_admin_password(admin.id, password_hasher.hash(body.new_password))
    await _audit(session, request, current, module="AUTH_PLATFORM", action="UPDATE", description="Contraseña de plataforma actualizada", table="administrador_plataforma", record_id=admin.id)
    return {"message": "Contraseña actualizada; vuelve a iniciar sesión"}


@router.get("/empresas", response_model=EmpresaPageResponse)
async def list_empresas(search: str | None = Query(default=None, max_length=150), activo: bool | None = None, page: int = Query(default=1, ge=1), per_page: int = Query(default=20, ge=1, le=100), _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    items, total = await _repo(session).list_empresas(search, activo, page, per_page)
    return page_payload([empresa_payload(item) for item in items], total, page, per_page)


@router.post("/empresas", response_model=ProvisionEmpresaResponse, status_code=201)
async def provision_empresa(body: ProvisionEmpresaRequest, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    try:
        empresa, admin, raw_token = await ProvisionEmpresa(session).execute(body)
        sent = True
        try:
            await email_service.send_email_verification(admin.email, raw_token)
        except EmailDeliveryError:
            sent = False
            logger.exception("Empresa creada, pero no se pudo enviar la verificación")
        await _audit(session, request, current, module="EMPRESAS", action="CREATE", description="Empresa aprovisionada", table="empresa", record_id=empresa.id, new={"slug": empresa.slug, "plan_id": body.plan_id, "admin_email": admin.email})
        return {"empresa": empresa_payload(empresa), "administrador_id": admin.id, "administrador_email": admin.email, "verification_email_sent": sent}
    except PlatformError as exc:
        _raise_platform(exc)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="La empresa o su administrador ya existe") from exc


@router.get("/empresas/{empresa_id}", response_model=EmpresaResponse)
async def get_empresa(empresa_id: str, _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    empresa = await _repo(session).get_empresa(empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return empresa_payload(empresa)


@router.patch("/empresas/{empresa_id}", response_model=EmpresaResponse)
async def update_empresa(empresa_id: str, body: EmpresaUpdateRequest, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
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
        await _audit(session, request, current, module="EMPRESAS", action="UPDATE", description="Empresa actualizada", table="empresa", record_id=empresa_id, new=values)
        return empresa_payload(empresa)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="NIT o slug ya utilizado") from exc


async def _set_empresa_status(empresa_id: str, active: bool, request: Request, current: CurrentPlatformAdmin, session: AsyncSession):
    repository = _repo(session)
    if not await repository.get_empresa(empresa_id):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    empresa = await repository.update_empresa(empresa_id, {"activo": active})
    action = "ACTIVATE" if active else "SUSPEND"
    await _audit(session, request, current, module="EMPRESAS", action=action, description="Empresa activada" if active else "Empresa suspendida", table="empresa", record_id=empresa_id)
    return empresa_payload(empresa)


@router.patch("/empresas/{empresa_id}/activar", response_model=EmpresaResponse)
async def activate_empresa(empresa_id: str, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    return await _set_empresa_status(empresa_id, True, request, current, session)


@router.patch("/empresas/{empresa_id}/suspender", response_model=EmpresaResponse)
async def suspend_empresa(empresa_id: str, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    return await _set_empresa_status(empresa_id, False, request, current, session)


@router.get("/planes", response_model=list[PlanResponse])
async def list_planes(activo: bool | None = None, _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    return await _repo(session).list_planes(activo)


@router.post("/planes", response_model=PlanResponse, status_code=201)
async def create_plan(body: PlanCreateRequest, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    repository = _repo(session)
    if await repository.get_plan_by_name(body.nombre):
        raise HTTPException(status_code=409, detail="Ya existe un plan con ese nombre")
    plan = await repository.create_plan(**body.model_dump())
    await _audit(session, request, current, module="PLANES", action="CREATE", description="Plan creado", table="plan_suscripcion", record_id=plan.id, new=body.model_dump(mode="json"))
    return plan


@router.get("/planes/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    plan = await _repo(session).get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


@router.patch("/planes/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: str, body: PlanUpdateRequest, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    repository = _repo(session)
    if not await repository.get_plan(plan_id):
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    values = body.model_dump(exclude_unset=True)
    try:
        plan = await repository.update_plan(plan_id, values)
        await _audit(session, request, current, module="PLANES", action="UPDATE", description="Plan actualizado", table="plan_suscripcion", record_id=plan_id, new=body.model_dump(exclude_unset=True, mode="json"))
        return plan
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Ya existe un plan con ese nombre") from exc


@router.get("/suscripciones", response_model=SubscriptionPageResponse)
async def list_subscriptions(activo: bool | None = None, page: int = Query(default=1, ge=1), per_page: int = Query(default=20, ge=1, le=100), _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    items, total = await _repo(session).list_suscripciones(activo, page, per_page)
    return page_payload([subscription_payload(item) for item in items], total, page, per_page)


@router.get("/empresas/{empresa_id}/suscripcion", response_model=SubscriptionResponse)
async def get_subscription(empresa_id: str, _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    item = await _repo(session).get_active_subscription(empresa_id)
    if not item:
        raise HTTPException(status_code=404, detail="Suscripción activa no encontrada")
    return subscription_payload(item)


@router.put("/empresas/{empresa_id}/suscripcion", response_model=SubscriptionResponse)
async def replace_subscription(empresa_id: str, body: SubscriptionUpdateRequest, request: Request, current: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    repository = _repo(session)
    if not await repository.get_empresa(empresa_id):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    plan = await repository.get_plan(body.plan_id)
    if not plan or not plan.activo:
        raise HTTPException(status_code=404, detail="Plan no encontrado o inactivo")
    subscription = await repository.replace_subscription(empresa_id, body.plan_id, body.fecha_inicio, body.fecha_fin)
    await _audit(session, request, current, module="SUSCRIPCIONES", action="UPDATE", description="Suscripción reemplazada", table="suscripcion", record_id=subscription.id, new=body.model_dump(mode="json"))
    return subscription_payload(subscription)


@router.get("/bitacora", response_model=PlatformAuditPageResponse)
async def list_platform_audit(module: str | None = None, action: str | None = None, page: int = Query(default=1, ge=1), per_page: int = Query(default=50, ge=1, le=200), _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    items, total = await _repo(session).list_audit(module, action, page, per_page)
    return page_payload(items, total, page, per_page)


@router.get("/bitacora/{audit_id}", response_model=PlatformAuditResponse)
async def get_platform_audit(audit_id: str, _: CurrentPlatformAdmin = Depends(get_current_platform_admin), session: AsyncSession = Depends(get_session)):
    item = await _repo(session).get_audit(audit_id)
    if not item:
        raise HTTPException(status_code=404, detail="Evento global no encontrado")
    return item

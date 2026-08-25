from datetime import UTC, date, datetime, timedelta

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.empresas.infrastructure.persistence.models.plan_suscripcion import PlanSuscripcionModel
from ssas.empresas.infrastructure.persistence.models.suscripcion import SuscripcionModel
from ssas.platform.infrastructure.persistence.models.platform_admin import PlatformAdminModel
from ssas.platform.infrastructure.persistence.models.platform_audit_log import PlatformAuditLogModel
from ssas.platform.infrastructure.persistence.models.platform_refresh_token import (
    PlatformRefreshTokenModel,
)


class PlatformRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_admin_by_login(self, login: str, *, lock: bool = False) -> PlatformAdminModel | None:
        normalized = login.strip().lower()
        query = select(PlatformAdminModel).where(
            or_(func.lower(PlatformAdminModel.email) == normalized, func.lower(PlatformAdminModel.username) == normalized)
        )
        if lock:
            query = query.with_for_update()
        return (await self.session.execute(query)).scalar_one_or_none()

    async def get_admin(self, admin_id: str) -> PlatformAdminModel | None:
        return (await self.session.execute(select(PlatformAdminModel).where(PlatformAdminModel.id == admin_id))).scalar_one_or_none()

    async def create_admin(self, **values) -> PlatformAdminModel:
        admin = PlatformAdminModel(**values)
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def record_failed_login(self, admin_id: str, max_attempts: int, lock_minutes: int) -> None:
        now = datetime.now(UTC)
        attempts = case(
            (PlatformAdminModel.bloqueado_hasta.is_not(None) & (PlatformAdminModel.bloqueado_hasta <= now), 1),
            else_=PlatformAdminModel.intentos_fallidos + 1,
        )
        await self.session.execute(
            update(PlatformAdminModel).where(PlatformAdminModel.id == admin_id).values(
                intentos_fallidos=attempts,
                ultimo_intento_fallido=now,
                bloqueado_hasta=case((attempts >= max_attempts, now + timedelta(minutes=lock_minutes)), else_=PlatformAdminModel.bloqueado_hasta),
            )
        )
        await self.session.flush()

    async def record_successful_login(self, admin_id: str) -> None:
        await self.session.execute(update(PlatformAdminModel).where(PlatformAdminModel.id == admin_id).values(
            intentos_fallidos=0, bloqueado_hasta=None, ultimo_intento_fallido=None, ultimo_acceso=datetime.now(UTC)
        ))
        await self.session.flush()

    async def change_admin_password(self, admin_id: str, password_hash: str) -> None:
        await self.session.execute(update(PlatformAdminModel).where(PlatformAdminModel.id == admin_id).values(password_hash=password_hash))
        await self.revoke_all_refresh_tokens(admin_id)

    async def save_refresh_token(self, admin_id: str, token_id: str, token_hash: str, expires_at: datetime) -> None:
        self.session.add(PlatformRefreshTokenModel(id=token_id, admin_id=admin_id, token_hash=token_hash, expires_at=expires_at))
        await self.session.flush()

    async def get_refresh_token(self, token_id: str) -> PlatformRefreshTokenModel | None:
        return (await self.session.execute(select(PlatformRefreshTokenModel).where(
            PlatformRefreshTokenModel.id == token_id,
            PlatformRefreshTokenModel.revoked_at.is_(None),
            PlatformRefreshTokenModel.expires_at > datetime.now(UTC),
        ).with_for_update())).scalar_one_or_none()

    async def revoke_refresh_token(self, token_id: str) -> None:
        await self.session.execute(update(PlatformRefreshTokenModel).where(PlatformRefreshTokenModel.id == token_id, PlatformRefreshTokenModel.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
        await self.session.flush()

    async def revoke_all_refresh_tokens(self, admin_id: str) -> None:
        await self.session.execute(update(PlatformRefreshTokenModel).where(PlatformRefreshTokenModel.admin_id == admin_id, PlatformRefreshTokenModel.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
        await self.session.flush()

    async def list_empresas(self, search: str | None, activo: bool | None, page: int, per_page: int) -> tuple[list[EmpresaModel], int]:
        filters = []
        if activo is not None:
            filters.append(EmpresaModel.activo.is_(activo))
        if search:
            term = f"%{search.strip().lower()}%"
            filters.append(or_(func.lower(EmpresaModel.razon_social).like(term), func.lower(EmpresaModel.nombre_comercial).like(term), func.lower(EmpresaModel.slug).like(term), func.lower(func.coalesce(EmpresaModel.nit, "")).like(term)))
        total = (await self.session.execute(select(func.count(EmpresaModel.id)).where(*filters))).scalar_one()
        query = select(EmpresaModel).options(selectinload(EmpresaModel.suscripciones).selectinload(SuscripcionModel.plan)).where(*filters).order_by(EmpresaModel.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        return list((await self.session.execute(query)).scalars().unique().all()), total

    async def get_empresa(self, empresa_id: str, *, lock: bool = False) -> EmpresaModel | None:
        query = select(EmpresaModel).options(selectinload(EmpresaModel.suscripciones).selectinload(SuscripcionModel.plan)).where(EmpresaModel.id == empresa_id)
        if lock:
            query = query.with_for_update()
        return (await self.session.execute(query)).scalar_one_or_none()

    async def get_empresa_by_unique(self, nit: str | None, slug: str) -> EmpresaModel | None:
        conditions = [func.lower(EmpresaModel.slug) == slug.strip().lower()]
        if nit:
            conditions.append(EmpresaModel.nit == nit.strip())
        return (await self.session.execute(select(EmpresaModel).where(or_(*conditions)))).scalar_one_or_none()

    async def update_empresa(self, empresa_id: str, values: dict) -> EmpresaModel | None:
        await self.session.execute(update(EmpresaModel).where(EmpresaModel.id == empresa_id).values(**values))
        await self.session.flush()
        return await self.get_empresa(empresa_id)

    async def list_planes(self, activo: bool | None = None) -> list[PlanSuscripcionModel]:
        query = select(PlanSuscripcionModel)
        if activo is not None:
            query = query.where(PlanSuscripcionModel.activo.is_(activo))
        return list((await self.session.execute(query.order_by(PlanSuscripcionModel.precio_mensual))).scalars().all())

    async def get_plan(self, plan_id: str) -> PlanSuscripcionModel | None:
        return (await self.session.execute(select(PlanSuscripcionModel).where(PlanSuscripcionModel.id == plan_id))).scalar_one_or_none()

    async def get_plan_by_name(self, name: str) -> PlanSuscripcionModel | None:
        return (await self.session.execute(select(PlanSuscripcionModel).where(func.lower(PlanSuscripcionModel.nombre) == name.strip().lower()))).scalar_one_or_none()

    async def create_plan(self, **values) -> PlanSuscripcionModel:
        model = PlanSuscripcionModel(**values)
        self.session.add(model)
        await self.session.flush()
        return model

    async def update_plan(self, plan_id: str, values: dict) -> PlanSuscripcionModel | None:
        await self.session.execute(update(PlanSuscripcionModel).where(PlanSuscripcionModel.id == plan_id).values(**values))
        await self.session.flush()
        return await self.get_plan(plan_id)

    async def list_suscripciones(self, activo: bool | None, page: int, per_page: int) -> tuple[list[SuscripcionModel], int]:
        filters = [SuscripcionModel.activo.is_(activo)] if activo is not None else []
        total = (await self.session.execute(select(func.count(SuscripcionModel.id)).where(*filters))).scalar_one()
        query = select(SuscripcionModel).options(selectinload(SuscripcionModel.empresa), selectinload(SuscripcionModel.plan)).where(*filters).order_by(SuscripcionModel.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        return list((await self.session.execute(query)).scalars().all()), total

    async def get_active_subscription(self, empresa_id: str) -> SuscripcionModel | None:
        query = select(SuscripcionModel).options(selectinload(SuscripcionModel.plan), selectinload(SuscripcionModel.empresa)).where(SuscripcionModel.empresa_id == empresa_id, SuscripcionModel.activo.is_(True)).order_by(SuscripcionModel.fecha_inicio.desc())
        return (await self.session.execute(query)).scalars().first()

    async def replace_subscription(self, empresa_id: str, plan_id: str, start: date, end: date | None) -> SuscripcionModel:
        await self.session.execute(update(SuscripcionModel).where(SuscripcionModel.empresa_id == empresa_id, SuscripcionModel.activo.is_(True)).values(activo=False))
        model = SuscripcionModel(empresa_id=empresa_id, plan_id=plan_id, fecha_inicio=start, fecha_fin=end, activo=True)
        self.session.add(model)
        await self.session.flush()
        return (await self.session.execute(select(SuscripcionModel).options(selectinload(SuscripcionModel.plan), selectinload(SuscripcionModel.empresa)).where(SuscripcionModel.id == model.id))).scalar_one()

    async def add_audit(self, **values) -> PlatformAuditLogModel:
        event = PlatformAuditLogModel(**values)
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_audit(self, module: str | None, action: str | None, page: int, per_page: int) -> tuple[list[PlatformAuditLogModel], int]:
        filters = []
        if module:
            filters.append(PlatformAuditLogModel.modulo == module.upper())
        if action:
            filters.append(PlatformAuditLogModel.accion == action.upper())
        total = (await self.session.execute(select(func.count(PlatformAuditLogModel.id)).where(*filters))).scalar_one()
        query = select(PlatformAuditLogModel).where(*filters).order_by(PlatformAuditLogModel.fecha.desc()).offset((page - 1) * per_page).limit(per_page)
        return list((await self.session.execute(query)).scalars().all()), total

    async def get_audit(self, audit_id: str) -> PlatformAuditLogModel | None:
        return (await self.session.execute(select(PlatformAuditLogModel).where(PlatformAuditLogModel.id == audit_id))).scalar_one_or_none()

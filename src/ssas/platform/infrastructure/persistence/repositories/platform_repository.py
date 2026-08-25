from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.bitacora.infrastructure.persistence.models.audit_log import AuditLogModel
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class PlatformRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_empresas(
        self, search: str | None, activo: bool | None, page: int, per_page: int
    ) -> tuple[list[EmpresaModel], int]:
        filters = []
        if activo is not None:
            filters.append(EmpresaModel.activo.is_(activo))
        if search:
            term = f"%{search.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(EmpresaModel.razon_social).like(term),
                    func.lower(EmpresaModel.nombre_comercial).like(term),
                    func.lower(EmpresaModel.slug).like(term),
                    func.lower(func.coalesce(EmpresaModel.nit, "")).like(term),
                )
            )
        total = (
            await self.session.execute(select(func.count(EmpresaModel.id)).where(*filters))
        ).scalar_one()
        query = (
            select(EmpresaModel)
            .where(*filters)
            .order_by(EmpresaModel.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list((await self.session.execute(query)).scalars().unique().all()), total

    async def get_empresa(self, empresa_id: str, *, lock: bool = False) -> EmpresaModel | None:
        query = select(EmpresaModel).where(EmpresaModel.id == empresa_id)
        if lock:
            query = query.with_for_update()
        return (await self.session.execute(query)).scalar_one_or_none()

    async def get_empresa_by_unique(self, nit: str | None, slug: str) -> EmpresaModel | None:
        conditions = [func.lower(EmpresaModel.slug) == slug.strip().lower()]
        if nit:
            conditions.append(EmpresaModel.nit == nit.strip())
        return (
            await self.session.execute(select(EmpresaModel).where(or_(*conditions)))
        ).scalar_one_or_none()

    async def update_empresa(self, empresa_id: str, values: dict) -> EmpresaModel | None:
        await self.session.execute(
            update(EmpresaModel).where(EmpresaModel.id == empresa_id).values(**values)
        )
        await self.session.flush()
        return await self.get_empresa(empresa_id)

    # ── Bitácora ──────────────────────────────────────────────────────────────
    # Los eventos de plataforma son filas de 'bitacora' con empresa_id NULL. Antes
    # vivían en una tabla aparte, 'bitacora_plataforma', duplicando el modelo entero.

    async def add_audit(
        self,
        admin_id: str | None = None,
        actor_etiqueta: str | None = None,
        modulo: str = "PLATFORM",
        accion: str = "INFO",
        nivel: str = "INFO",
        descripcion: str = "",
        tabla_afectada: str | None = None,
        registro_id: str | None = None,
        datos_previos: dict | None = None,
        datos_nuevos: dict | None = None,
        ip_origen: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLogModel:
        evento = AuditLogModel(
            empresa_id=None,
            user_id=admin_id,
            actor_label=actor_etiqueta,
            module=modulo,
            action=accion,
            level=nivel,
            description=descripcion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            datos_previos_jsonb=datos_previos,
            datos_nuevos_jsonb=datos_nuevos,
            ip_origen=ip_origen,
            user_agent=user_agent,
        )
        self.session.add(evento)
        await self.session.flush()
        return evento

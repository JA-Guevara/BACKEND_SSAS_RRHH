from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule


class VacanteEvents:
    """Mapeo semántico de los eventos auditables del módulo de vacantes."""

    def __init__(self, recorder: RegisterAuditEvent):
        self.recorder = recorder

    async def created(self, **context):
        return await self.recorder.execute(
            module=AuditModule.RECLUTAMIENTO,
            action=AuditAction.CREATE,
            description="Vacante creada",
            affected_table="vacante",
            **context,
        )

    async def updated(self, **context):
        return await self.recorder.execute(
            module=AuditModule.RECLUTAMIENTO,
            action=AuditAction.UPDATE,
            description="Vacante actualizada",
            affected_table="vacante",
            **context,
        )

    async def published(self, **context):
        return await self.recorder.execute(
            module=AuditModule.RECLUTAMIENTO,
            action=AuditAction.UPDATE,
            description="Vacante publicada",
            affected_table="vacante",
            **context,
        )

    async def paused(self, **context):
        return await self.recorder.execute(
            module=AuditModule.RECLUTAMIENTO,
            action=AuditAction.UPDATE,
            description="Vacante pausada",
            affected_table="vacante",
            **context,
        )

    async def resumed(self, **context):
        return await self.recorder.execute(
            module=AuditModule.RECLUTAMIENTO,
            action=AuditAction.UPDATE,
            description="Vacante reanudada",
            affected_table="vacante",
            **context,
        )

    async def closed(self, **context):
        return await self.recorder.execute(
            module=AuditModule.RECLUTAMIENTO,
            action=AuditAction.UPDATE,
            description="Vacante cerrada",
            affected_table="vacante",
            **context,
        )

    async def deleted(self, **context):
        return await self.recorder.execute(
            module=AuditModule.RECLUTAMIENTO,
            action=AuditAction.DELETE,
            description="Vacante eliminada",
            affected_table="vacante",
            **context,
        )
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule


class OrganizacionEvents:
    def __init__(self, recorder: RegisterAuditEvent):
        self.recorder = recorder

    async def departamento_creado(self, **context):
        return await self._record(AuditAction.CREATE, "Departamento creado", "departamento", **context)

    async def departamento_actualizado(self, **context):
        return await self._record(AuditAction.UPDATE, "Departamento actualizado", "departamento", **context)

    async def departamento_eliminado(self, **context):
        return await self._record(AuditAction.DELETE, "Departamento eliminado", "departamento", **context)

    async def cargo_creado(self, **context):
        return await self._record(AuditAction.CREATE, "Cargo creado", "cargo", **context)

    async def cargo_actualizado(self, **context):
        return await self._record(AuditAction.UPDATE, "Cargo actualizado", "cargo", **context)

    async def cargo_eliminado(self, **context):
        return await self._record(AuditAction.DELETE, "Cargo eliminado", "cargo", **context)

    async def _record(self, action: AuditAction, description: str, affected_table: str, **context):
        return await self.recorder.execute(
            module=AuditModule.ORGANIZACION,
            action=action,
            description=description,
            affected_table=affected_table,
            **context,
        )
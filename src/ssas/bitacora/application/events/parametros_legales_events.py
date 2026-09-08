from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule


class ParametrosLegalesEvents:
    def __init__(self, recorder: RegisterAuditEvent):
        self.recorder = recorder

    async def periodo_creado(self, **context):
        return await self._record(
            AuditAction.CREATE, "Parámetros legales creados", "parametro_legal", **context
        )

    async def periodo_actualizado(self, **context):
        return await self._record(
            AuditAction.UPDATE,
            "Parámetros legales actualizados",
            "parametro_legal",
            **context,
        )

    async def _record(self, action: AuditAction, description: str, affected_table: str, **context):
        return await self.recorder.execute(
            module=AuditModule.CONFIGURACION,
            action=action,
            description=description,
            affected_table=affected_table,
            **context,
        )
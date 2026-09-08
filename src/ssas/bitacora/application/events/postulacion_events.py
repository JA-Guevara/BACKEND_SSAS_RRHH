from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule


class PostulacionEvents:
    """Mapeo semántico de los eventos auditables del proceso de selección."""

    def __init__(self, recorder: RegisterAuditEvent):
        self.recorder = recorder

    async def publica_creada(self, **context):
        return await self.recorder.execute(
            module=AuditModule.SELECCION,
            action=AuditAction.CREATE,
            description="Postulación registrada en el portal público",
            affected_table="postulacion",
            **context,
        )

    async def etapa_cambiada(self, **context):
        return await self.recorder.execute(
            module=AuditModule.SELECCION,
            action=AuditAction.UPDATE,
            description="Etapa de la postulación cambiada",
            affected_table="postulacion",
            **context,
        )

    async def rechazada(self, **context):
        return await self.recorder.execute(
            module=AuditModule.SELECCION,
            action=AuditAction.REJECT,
            description="Postulación rechazada",
            affected_table="postulacion",
            **context,
        )

    async def puntaje_asignado(self, **context):
        return await self.recorder.execute(
            module=AuditModule.SELECCION,
            action=AuditAction.UPDATE,
            description="Puntaje asignado a la postulación",
            affected_table="postulacion",
            **context,
        )

    async def nota_creada(self, **context):
        return await self.recorder.execute(
            module=AuditModule.SELECCION,
            action=AuditAction.CREATE,
            description="Nota interna agregada a la postulación",
            affected_table="postulacion_nota",
            **context,
        )
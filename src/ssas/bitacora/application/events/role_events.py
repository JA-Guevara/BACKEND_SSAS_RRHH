from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule


class RoleEvents:
    """Mapeo semántico de eventos del módulo de roles y permisos."""

    def __init__(self, recorder: RegisterAuditEvent):
        self.recorder = recorder

    async def created(self, **context):
        return await self.recorder.execute(
            module=AuditModule.ROLES,
            action=AuditAction.CREATE,
            description="Rol creado",
            affected_table="rol",
            **context,
        )

    async def updated(self, **context):
        return await self.recorder.execute(
            module=AuditModule.ROLES,
            action=AuditAction.UPDATE,
            description="Rol actualizado",
            affected_table="rol",
            **context,
        )

    async def deleted(self, **context):
        return await self.recorder.execute(
            module=AuditModule.ROLES,
            action=AuditAction.DELETE,
            description="Rol eliminado",
            affected_table="rol",
            **context,
        )

    async def permissions_assigned(self, **context):
        return await self.recorder.execute(
            module=AuditModule.ROLES,
            action=AuditAction.ASSIGN,
            description="Permisos asignados al rol",
            affected_table="rol_permiso",
            **context,
        )

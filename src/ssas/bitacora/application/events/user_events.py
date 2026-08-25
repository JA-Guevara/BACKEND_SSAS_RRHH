from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule


class UserEvents:
    def __init__(self, recorder: RegisterAuditEvent):
        self.recorder = recorder

    async def created(self, **context):
        return await self._record(AuditAction.CREATE, "Usuario creado", **context)

    async def updated(self, **context):
        return await self._record(AuditAction.UPDATE, "Usuario actualizado", **context)

    async def activated(self, **context):
        return await self._record(AuditAction.ACTIVATE, "Usuario activado", **context)

    async def deactivated(self, **context):
        return await self._record(AuditAction.DEACTIVATE, "Usuario desactivado", **context)

    async def password_changed(self, **context):
        return await self._record(AuditAction.UPDATE, "Contraseña temporal asignada", **context)

    async def unlocked(self, **context):
        return await self._record(AuditAction.ACTIVATE, "Usuario desbloqueado", **context)

    async def _record(self, action: AuditAction, description: str, **context):
        return await self.recorder.execute(
            module=AuditModule.USUARIOS,
            action=action,
            description=description,
            affected_table="usuario",
            **context,
        )

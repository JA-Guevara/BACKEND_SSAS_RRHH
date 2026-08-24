from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.domain.catalogs import AuditAction, AuditModule


class AuthEvents:
    """Mapeo semántico de los eventos auditables del módulo de autenticación."""

    def __init__(self, recorder: RegisterAuditEvent):
        self.recorder = recorder

    async def login_success(self, **context):
        return await self.recorder.execute(
            module=AuditModule.AUTH,
            action=AuditAction.LOGIN,
            description="Inicio de sesión exitoso",
            **context,
        )

    async def login_failed(self, **context):
        return await self.recorder.execute(
            module=AuditModule.AUTH,
            action=AuditAction.LOGIN_FAILED,
            description="Intento fallido de inicio de sesión",
            **context,
        )

    async def logout(self, **context):
        return await self.recorder.execute(
            module=AuditModule.AUTH,
            action=AuditAction.LOGOUT,
            description="Cierre de sesión",
            **context,
        )

    async def password_reset_completed(self, **context):
        return await self.recorder.execute(
            module=AuditModule.AUTH,
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            description="Contraseña restablecida",
            **context,
        )

    async def password_reset_requested(self, **context):
        return await self.recorder.execute(
            module=AuditModule.AUTH,
            action=AuditAction.PASSWORD_RESET_REQUESTED,
            description="Recuperación de contraseña solicitada",
            **context,
        )

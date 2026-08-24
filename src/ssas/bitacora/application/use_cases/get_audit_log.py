from ssas.bitacora.domain.exceptions import AuditLogNotFoundError


class GetAuditLog:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, audit_log_id: str, empresa_id: str):
        audit_log = await self.repository.get_by_id(audit_log_id, empresa_id)
        if audit_log is None:
            raise AuditLogNotFoundError("Evento de bitácora no encontrado")
        return audit_log

class AuditLogRepository:
    def add(self, audit_log):
        return audit_log

    def list(self, filters: dict | None = None):
        return []

    def get_by_id(self, audit_log_id: str):
        return {"id": audit_log_id, "action": "login", "description": "Registro de ejemplo"}

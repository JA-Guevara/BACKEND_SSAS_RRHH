class GetAuditLog:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, audit_log_id: str):
        return self.repository.get_by_id(audit_log_id)

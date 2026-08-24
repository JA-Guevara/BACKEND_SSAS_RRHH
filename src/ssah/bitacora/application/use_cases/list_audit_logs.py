class ListAuditLogs:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, filters: dict | None = None):
        return self.repository.list(filters)

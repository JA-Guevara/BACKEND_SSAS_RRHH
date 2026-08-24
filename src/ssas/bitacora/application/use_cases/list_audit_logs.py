from ssas.bitacora.application.dto.audit_log_filter import AuditLogFilter


class ListAuditLogs:
    def __init__(self, repository):
        self.repository = repository

    async def execute(self, filters: AuditLogFilter) -> dict:
        items, total = await self.repository.list(filters)
        return {
            "items": items,
            "total": total,
            "page": filters.page,
            "per_page": filters.per_page,
            "total_pages": max(1, (total + filters.per_page - 1) // filters.per_page),
        }

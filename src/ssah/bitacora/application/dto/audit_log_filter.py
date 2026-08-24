from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditLogFilter:
    user_id: str | None = None
    action: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
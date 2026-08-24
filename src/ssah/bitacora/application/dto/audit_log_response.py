from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditLogResponse:
    id: str
    action: str
    description: str
    user_id: str | None
    created_at: datetime
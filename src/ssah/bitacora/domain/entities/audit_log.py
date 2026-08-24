from dataclasses import dataclass


@dataclass
class AuditLog:
    id: str
    action: str
    description: str
    created_at: str
    user_id: str | None = None

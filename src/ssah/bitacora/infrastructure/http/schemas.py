from pydantic import BaseModel


class AuditLogSchema(BaseModel):
    action: str
    description: str
    user_id: str | None = None

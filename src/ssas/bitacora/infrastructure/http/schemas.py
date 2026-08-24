from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    empresa_id: str
    module: str
    action: str
    description: str
    level: str
    user_id: str | None = None
    actor_label: str | None = None
    affected_table: str | None = None
    record_id: str | None = None
    previous_data: dict[str, Any] | None = None
    new_data: dict[str, Any] | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    created_at: datetime


class AuditLogPageSchema(BaseModel):
    items: list[AuditLogSchema] = Field(default_factory=list)
    total: int
    page: int
    per_page: int
    total_pages: int

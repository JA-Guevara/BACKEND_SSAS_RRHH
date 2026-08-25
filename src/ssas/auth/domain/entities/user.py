from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    id: str
    name: str
    email: str
    hashed_password: str
    empresa_id: str
    username: str | None = None
    roles: list[str] = field(default_factory=list)
    empresa_is_active: bool = True
    is_active: bool = True
    email_verified: bool = False
    must_change_password: bool = False
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

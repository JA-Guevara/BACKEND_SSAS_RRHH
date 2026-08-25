from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Usuario:
    id: str
    empresa_id: str | None
    nombre: str
    apellido: str
    email: str
    username: str
    telefono: str | None = None
    is_active: bool = True
    email_verified: bool = False
    must_change_password: bool = False
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    roles: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

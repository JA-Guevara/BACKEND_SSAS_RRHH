from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    name: str
    email: str
    hashed_password: str
    is_active: bool = True
    email_verified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

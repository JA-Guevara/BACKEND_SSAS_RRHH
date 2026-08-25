from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StoredToken:
    id: str
    user_id: str
    empresa_id: str | None
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.now(self.expires_at.tzinfo)

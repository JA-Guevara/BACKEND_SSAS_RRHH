from dataclasses import dataclass, field

from ssah.roles.domain.entities.permission import Permission


@dataclass
class Role:
    id: str
    name: str
    description: str | None = None
    is_active: bool = True
    permissions: list[Permission] = field(default_factory=list)
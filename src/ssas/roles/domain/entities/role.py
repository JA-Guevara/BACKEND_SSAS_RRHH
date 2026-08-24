from dataclasses import dataclass, field

from ssas.roles.domain.entities.permission import Permission


@dataclass
class Role:
    id: str
    empresa_id: str
    name: str
    codigo: str
    description: str | None = None
    is_active: bool = True
    permissions: list[Permission] = field(default_factory=list)

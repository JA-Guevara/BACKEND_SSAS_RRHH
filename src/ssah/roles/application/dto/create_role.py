from dataclasses import dataclass


@dataclass(frozen=True)
class CreateRoleRequest:
    name: str
    description: str | None = None


@dataclass(frozen=True)
class RoleResponse:
    id: str
    name: str
    description: str | None = None
    is_active: bool = True
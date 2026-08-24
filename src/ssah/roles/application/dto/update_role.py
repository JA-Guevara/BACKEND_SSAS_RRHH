from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateRoleRequest:
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
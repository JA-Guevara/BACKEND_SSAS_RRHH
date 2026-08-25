from dataclasses import dataclass


@dataclass
class Permission:
    id: str
    name: str
    resource: str
    action: str
    description: str | None = None

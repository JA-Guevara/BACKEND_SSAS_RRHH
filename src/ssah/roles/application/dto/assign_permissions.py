from dataclasses import dataclass


@dataclass(frozen=True)
class AssignPermissionsRequest:
    permission_ids: list[str]
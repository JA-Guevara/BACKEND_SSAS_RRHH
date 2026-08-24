from ssah.infrastructure.database.base import Base
from ssah.roles.infrastructure.persistence.models.role import role_permissions_table


class RolePermissionModel(Base):
	__table__ = role_permissions_table
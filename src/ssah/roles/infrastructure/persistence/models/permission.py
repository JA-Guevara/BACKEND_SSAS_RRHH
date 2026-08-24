from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ssah.infrastructure.database.base import Base
from ssah.roles.infrastructure.persistence.models.role import role_permissions_table


class PermissionModel(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    roles = relationship(
        "RoleModel",
        secondary=role_permissions_table,
        back_populates="permissions",
    )
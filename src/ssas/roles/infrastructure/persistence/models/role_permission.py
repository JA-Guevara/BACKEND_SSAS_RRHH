from sqlalchemy import Column, DateTime, ForeignKey, Index, Table, func
from sqlalchemy.dialects.postgresql import UUID

from ssas.infrastructure.database.base import Base

rol_permiso_table = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", UUID(as_uuid=False), ForeignKey("rol.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", UUID(as_uuid=False), ForeignKey("permiso.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


class RolePermissionModel(Base):
    __table__ = rol_permiso_table


Index("idx_rol_permiso_rol_id", rol_permiso_table.c.rol_id)
Index("idx_rol_permiso_permiso_id", rol_permiso_table.c.permiso_id)

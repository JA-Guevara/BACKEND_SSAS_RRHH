from sqlalchemy import Column, DateTime, ForeignKey, Table, func
from sqlalchemy.dialects.postgresql import UUID

from ssah.infrastructure.database.base import Base

usuario_rol_table = Table(
    "usuario_rol",
    Base.metadata,
    Column("usuario_id", UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True),
    Column("rol_id", UUID(as_uuid=False), ForeignKey("rol.id", ondelete="CASCADE"), primary_key=True),
    Column("asignado_por_id", UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True),
    Column("fecha_asignacion", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


class UserRoleModel(Base):
    __table__ = usuario_rol_table
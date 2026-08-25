from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base
from ssas.roles.infrastructure.persistence.models.role_permission import rol_permiso_table


class PermissionModel(Base):
    __tablename__ = "permiso"
    __table_args__ = (
        UniqueConstraint(
            "modulo", "recurso", "operacion", name="uq_permiso_modulo_recurso_operacion"
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    name: Mapped[str] = mapped_column("codigo", String(120), unique=True, nullable=False)
    modulo: Mapped[str] = mapped_column(String(80), nullable=False)
    resource: Mapped[str] = mapped_column("recurso", String(80), nullable=False)
    action: Mapped[str] = mapped_column("operacion", String(80), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    roles = relationship("RoleModel", secondary=rol_permiso_table, back_populates="permissions")

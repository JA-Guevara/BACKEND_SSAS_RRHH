from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssah.infrastructure.database.base import Base
from ssah.roles.infrastructure.persistence.models.role_permission import rol_permiso_table

if TYPE_CHECKING:
    from ssah.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssah.roles.infrastructure.persistence.models.permission import PermissionModel


class RoleModel(Base):
    __tablename__ = "rol"
    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_rol_empresa_codigo"),
        UniqueConstraint("empresa_id", "nombre", name="uq_rol_empresa_nombre"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    empresa_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column("nombre", String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column("descripcion", Text, nullable=True)
    es_base: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="roles")
    permissions: Mapped[list["PermissionModel"]] = relationship(secondary=rol_permiso_table, back_populates="roles")
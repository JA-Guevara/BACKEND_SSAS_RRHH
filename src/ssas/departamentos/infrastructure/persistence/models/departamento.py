from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.auth.infrastructure.persistence.models.user import UserModel
    from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel


class DepartamentoModel(Base):
    __tablename__ = "departamento"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_departamento_empresa_nombre"),
        Index("idx_departamento_empresa_id", "empresa_id"),
        Index("idx_departamento_padre_id", "departamento_padre_id"),
        Index("idx_departamento_responsable_id", "responsable_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    departamento_padre_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("departamento.id", ondelete="RESTRICT"), nullable=True
    )
    responsable_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="departamentos")
    departamento_padre: Mapped["DepartamentoModel | None"] = relationship(
        remote_side=[id], back_populates="subdepartamentos"
    )
    subdepartamentos: Mapped[list["DepartamentoModel"]] = relationship(
        back_populates="departamento_padre"
    )
    responsable: Mapped["UserModel | None"] = relationship()
    cargos: Mapped[list["CargoModel"]] = relationship(back_populates="departamento")
    vacantes: Mapped[list["VacanteModel"]] = relationship(back_populates="departamento")


Index(
    "uq_departamento_empresa_nombre_ci",
    DepartamentoModel.empresa_id,
    func.lower(DepartamentoModel.nombre),
    unique=True,
)

Index(
    "uq_departamento_empresa_codigo_ci",
    DepartamentoModel.empresa_id,
    func.lower(DepartamentoModel.codigo),
    unique=True,
)

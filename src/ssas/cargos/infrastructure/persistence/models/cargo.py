from datetime import datetime
from typing import TYPE_CHECKING

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.departamentos.infrastructure.persistence.models.departamento import (
        DepartamentoModel,
    )
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel


class CargoModel(Base):
    __tablename__ = "cargo"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_cargo_empresa_nombre"),
        CheckConstraint(
            "salario_min IS NULL OR salario_min >= 0",
            name="ck_cargo_salario_min_no_negativo",
        ),
        CheckConstraint(
            "salario_max IS NULL OR salario_max >= 0",
            name="ck_cargo_salario_max_no_negativo",
        ),
        CheckConstraint(
            "salario_min IS NULL OR salario_max IS NULL OR salario_max >= salario_min",
            name="ck_cargo_rango_salario",
        ),
        Index("idx_cargo_empresa_id", "empresa_id"),
        Index("idx_cargo_departamento_id", "departamento_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    departamento_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("departamento.id", ondelete="RESTRICT"), nullable=True
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    nivel: Mapped[str | None] = mapped_column(String(80), nullable=True)
    salario_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salario_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="cargos")
    departamento: Mapped["DepartamentoModel | None"] = relationship(back_populates="cargos")
    vacantes: Mapped[list["VacanteModel"]] = relationship(back_populates="cargo")


Index(
    "uq_cargo_empresa_nombre_ci",
    CargoModel.empresa_id,
    func.lower(CargoModel.nombre),
    unique=True,
)

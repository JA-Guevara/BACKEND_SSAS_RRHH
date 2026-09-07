from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.auth.infrastructure.persistence.models.user import UserModel
    from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
    from ssas.departamentos.infrastructure.persistence.models.departamento import (
        DepartamentoModel,
    )
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
    from ssas.vacantes.infrastructure.persistence.models.vacante_habilidad import (
        VacanteHabilidadModel,
    )


class VacanteModel(Base):
    __tablename__ = "vacante"
    __table_args__ = (
        CheckConstraint("cantidad_vacantes > 0", name="ck_vacante_cantidad_positiva"),
        CheckConstraint("experiencia_min >= 0", name="ck_vacante_experiencia_no_negativa"),
        CheckConstraint(
            "salario_min IS NULL OR salario_min >= 0", name="ck_vacante_salario_min_no_negativo"
        ),
        CheckConstraint(
            "salario_max IS NULL OR salario_max >= 0", name="ck_vacante_salario_max_no_negativo"
        ),
        CheckConstraint(
            "salario_min IS NULL OR salario_max IS NULL OR salario_max >= salario_min",
            name="ck_vacante_rango_salario",
        ),
        CheckConstraint(
            "modalidad IN ('PRESENCIAL', 'REMOTO', 'HIBRIDO')",
            name="ck_vacante_modalidad",
        ),
        CheckConstraint(
            "estado IN ('BORRADOR', 'PUBLICADA', 'PAUSADA', 'CERRADA', 'CANCELADA')",
            name="ck_vacante_estado",
        ),
        CheckConstraint(
            "fecha_cierre IS NULL OR fecha_publicacion IS NULL "
            "OR fecha_cierre >= fecha_publicacion",
            name="ck_vacante_fechas",
        ),
        Index("idx_vacante_empresa_id", "empresa_id"),
        Index("idx_vacante_cargo_id", "cargo_id"),
        Index("idx_vacante_departamento_id", "departamento_id"),
        Index("idx_vacante_responsable_id", "responsable_id"),
        Index("idx_vacante_estado", "estado"),
        Index("idx_vacante_fecha_cierre", "fecha_cierre"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    cargo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("cargo.id", ondelete="RESTRICT"), nullable=False
    )
    departamento_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("departamento.id", ondelete="RESTRICT"), nullable=False
    )
    responsable_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    requisitos: Mapped[str | None] = mapped_column(Text, nullable=True)
    beneficios: Mapped[str | None] = mapped_column(Text, nullable=True)
    cantidad_vacantes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    salario_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salario_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    mostrar_salario: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    modalidad: Mapped[str] = mapped_column(String(20), nullable=False)
    ubicacion: Mapped[str | None] = mapped_column(String(160), nullable=True)
    experiencia_min: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    fecha_publicacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="BORRADOR")
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    empresa: Mapped[EmpresaModel] = relationship(back_populates="vacantes")
    cargo: Mapped[CargoModel] = relationship(back_populates="vacantes")
    departamento: Mapped[DepartamentoModel] = relationship(back_populates="vacantes")
    responsable: Mapped[UserModel] = relationship(back_populates="vacantes_responsables")
    habilidades_requeridas: Mapped[list[VacanteHabilidadModel]] = relationship(
        back_populates="vacante", cascade="all, delete-orphan"
    )
    postulaciones: Mapped[list[PostulacionModel]] = relationship(back_populates="vacante")

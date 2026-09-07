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
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.habilidades.infrastructure.persistence.models.habilidad import HabilidadModel
    from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel


class VacanteHabilidadModel(Base):
    __tablename__ = "vacante_habilidad"
    __table_args__ = (
        UniqueConstraint("vacante_id", "habilidad_id", name="uq_vacante_habilidad_pair"),
        CheckConstraint("peso > 0", name="ck_vacante_habilidad_peso_positivo"),
        Index("idx_vacante_habilidad_habilidad_id", "habilidad_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    vacante_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vacante.id", ondelete="CASCADE"),
        nullable=False,
    )
    habilidad_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("habilidad.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nivel_requerido: Mapped[str] = mapped_column(String(30), nullable=False)
    es_obligatorio: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    peso: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default="1.00")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    vacante: Mapped[VacanteModel] = relationship(back_populates="habilidades_requeridas")
    habilidad: Mapped[HabilidadModel] = relationship(back_populates="vacantes_requeridas")

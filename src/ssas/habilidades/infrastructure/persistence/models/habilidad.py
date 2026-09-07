from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.vacantes.infrastructure.persistence.models.vacante_habilidad import (
        VacanteHabilidadModel,
    )


class HabilidadModel(Base):
    __tablename__ = "habilidad"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_habilidad_empresa_nombre"),
        Index("idx_habilidad_empresa_id", "empresa_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(120), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    empresa: Mapped[EmpresaModel] = relationship(back_populates="habilidades")
    vacantes_requeridas: Mapped[list[VacanteHabilidadModel]] = relationship(
        back_populates="habilidad"
    )


Index(
    "uq_habilidad_empresa_nombre_ci",
    HabilidadModel.empresa_id,
    func.lower(HabilidadModel.nombre),
    unique=True,
)

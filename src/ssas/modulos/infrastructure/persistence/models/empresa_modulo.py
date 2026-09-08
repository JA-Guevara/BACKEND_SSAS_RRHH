from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base
from ssas.modulos.infrastructure.persistence.models.modulo import ModuloModel


class EmpresaModuloModel(Base):
    """Habilitación de un módulo para una empresa concreta."""

    __tablename__ = "empresa_modulo"
    __table_args__ = (Index("idx_empresa_modulo_empresa_id", "empresa_id"),)

    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("empresa.id", ondelete="CASCADE"),
        primary_key=True,
    )
    modulo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("modulo.id", ondelete="CASCADE"),
        primary_key=True,
    )
    habilitado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    fecha_habilitacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    habilitado_por_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    modulo: Mapped[ModuloModel] = relationship()

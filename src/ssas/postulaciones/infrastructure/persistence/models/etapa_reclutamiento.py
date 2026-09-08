from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel


class EtapaReclutamientoModel(Base):
    __tablename__ = "etapa_reclutamiento"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nombre", name="uq_etapa_reclutamiento_empresa_nombre"),
        UniqueConstraint("empresa_id", "orden", name="uq_etapa_reclutamiento_empresa_orden"),
        CheckConstraint("orden > 0", name="ck_etapa_reclutamiento_orden_positivo"),
        Index("idx_etapa_reclutamiento_empresa_id", "empresa_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    es_inicial: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    es_contratado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    es_rechazado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    empresa: Mapped[EmpresaModel] = relationship(back_populates="etapas_reclutamiento")
    postulaciones: Mapped[list[PostulacionModel]] = relationship(back_populates="etapa")

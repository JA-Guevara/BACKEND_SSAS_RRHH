from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
        EtapaReclutamientoModel,
    )
    from ssas.postulaciones.infrastructure.persistence.models.motivo_rechazo import (
        MotivoRechazoModel,
    )
    from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
    from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel


class PostulacionModel(Base):
    __tablename__ = "postulacion"
    __table_args__ = (
        UniqueConstraint("vacante_id", "postulante_id", name="uq_postulacion_vacante_postulante"),
        UniqueConstraint("codigo_seguimiento", name="uq_postulacion_codigo_seguimiento"),
        CheckConstraint(
            "puntaje_manual IS NULL OR (puntaje_manual >= 0 AND puntaje_manual <= 100)",
            name="ck_postulacion_puntaje_manual",
        ),
        CheckConstraint(
            "puntaje_ia IS NULL OR (puntaje_ia >= 0 AND puntaje_ia <= 100)",
            name="ck_postulacion_puntaje_ia",
        ),
        CheckConstraint(
            "estado IN ('ACTIVA', 'RETIRADA', 'DESCARTADA', 'CONTRATADA')",
            name="ck_postulacion_estado",
        ),
        Index("idx_postulacion_vacante_id", "vacante_id"),
        Index("idx_postulacion_postulante_id", "postulante_id"),
        Index("idx_postulacion_etapa_id", "etapa_id"),
        Index("idx_postulacion_motivo_rechazo_id", "motivo_rechazo_id"),
        Index("idx_postulacion_empleado_id", "empleado_id"),
        Index("idx_postulacion_estado", "estado"),
        Index("idx_postulacion_codigo_seguimiento", "codigo_seguimiento"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    vacante_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("vacante.id", ondelete="RESTRICT"), nullable=False
    )
    postulante_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("postulante.id", ondelete="RESTRICT"), nullable=False
    )
    etapa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("etapa_reclutamiento.id", ondelete="RESTRICT"),
        nullable=False,
    )
    motivo_rechazo_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("motivo_rechazo.id", ondelete="SET NULL"), nullable=True
    )
    empleado_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    puntaje_ia: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    puntaje_manual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    codigo_seguimiento: Mapped[str] = mapped_column(String(40), nullable=False)
    fecha_postulacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fecha_ultimo_cambio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVA")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    vacante: Mapped[VacanteModel] = relationship(back_populates="postulaciones")
    postulante: Mapped[PostulanteModel] = relationship(back_populates="postulaciones")
    etapa: Mapped[EtapaReclutamientoModel] = relationship(back_populates="postulaciones")
    motivo_rechazo: Mapped[MotivoRechazoModel | None] = relationship(
        back_populates="postulaciones"
    )

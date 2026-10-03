from __future__ import annotations

from datetime import datetime
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
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ssas.infrastructure.database.base import Base


class EvaluacionModel(Base):
    __tablename__ = "evaluacion"
    __table_args__ = (
        CheckConstraint(
            "puntaje_maximo > 0 AND puntaje >= 0 AND puntaje <= puntaje_maximo",
            name="ck_evaluacion_puntaje",
        ),
        Index("idx_evaluacion_postulacion_id_fecha", "postulacion_id", "fecha"),
        Index("idx_evaluacion_evaluador_id", "evaluador_id"),
        Index("idx_evaluacion_fecha", "fecha"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    postulacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("postulacion.id", ondelete="RESTRICT"), nullable=False
    )
    evaluador_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    puntaje: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    puntaje_maximo: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False)
    archivo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

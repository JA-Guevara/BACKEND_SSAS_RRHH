from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ssas.infrastructure.database.base import Base


class EntrevistaModel(Base):
    __tablename__ = "entrevista"
    __table_args__ = (
        CheckConstraint("duracion_min > 0", name="ck_entrevista_duracion"),
        CheckConstraint(
            "puntaje IS NULL OR (puntaje >= 0 AND puntaje <= 100)", name="ck_entrevista_puntaje"
        ),
        CheckConstraint(
            "estado IN ('PROGRAMADA', 'CONFIRMADA', 'REALIZADA', 'CANCELADA')",
            name="ck_entrevista_estado",
        ),
        CheckConstraint(
            "modalidad IN ('VIRTUAL', 'PRESENCIAL', 'TELEFONICA')", name="ck_entrevista_modalidad"
        ),
        CheckConstraint(
            "(modalidad = 'VIRTUAL' AND enlace_reunion IS NOT NULL AND length(trim(enlace_reunion)) > 0) OR (modalidad = 'PRESENCIAL' AND lugar IS NOT NULL AND length(trim(lugar)) > 0) OR modalidad = 'TELEFONICA'",
            name="ck_entrevista_ubicacion",
        ),
        Index("idx_entrevista_postulacion_id", "postulacion_id"),
        Index("idx_entrevista_entrevistador_id_fecha_hora", "entrevistador_id", "fecha_hora"),
        Index("idx_entrevista_fecha_hora", "fecha_hora"),
        Index("idx_entrevista_estado", "estado"),
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
    entrevistador_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duracion_min: Mapped[int] = mapped_column(Integer, nullable=False)
    modalidad: Mapped[str] = mapped_column(String(20), nullable=False)
    enlace_reunion: Mapped[str | None] = mapped_column(Text, nullable=True)
    lugar: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'PROGRAMADA'")
    )
    puntaje: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    recomendacion: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

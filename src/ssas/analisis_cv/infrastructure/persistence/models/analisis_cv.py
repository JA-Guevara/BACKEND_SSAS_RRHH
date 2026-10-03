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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ssas.infrastructure.database.base import Base


class AnalisisCvModel(Base):
    __tablename__ = "analisis_cv"
    __table_args__ = (
        CheckConstraint(
            "puntaje_afinidad >= 0 AND puntaje_afinidad <= 100", name="ck_analisis_cv_afinidad"
        ),
        CheckConstraint(
            "anios_experiencia_detectados IS NULL OR anios_experiencia_detectados >= 0",
            name="ck_analisis_cv_experiencia",
        ),
        CheckConstraint("tiempo_proceso_ms >= 0", name="ck_analisis_cv_tiempo"),
        CheckConstraint(
            "jsonb_typeof(habilidades_detectadas) = 'array'",
            name="ck_analisis_cv_habilidades_detectadas",
        ),
        CheckConstraint(
            "jsonb_typeof(habilidades_faltantes) = 'array'",
            name="ck_analisis_cv_habilidades_faltantes",
        ),
        CheckConstraint("jsonb_typeof(fortalezas) = 'array'", name="ck_analisis_cv_fortalezas"),
        Index("idx_analisis_cv_postulacion_id_fecha_analisis", "postulacion_id", "fecha_analisis"),
        Index("idx_analisis_cv_fecha_analisis", "fecha_analisis"),
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
    puntaje_afinidad: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    habilidades_detectadas: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    habilidades_faltantes: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    anios_experiencia_detectados: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    resumen_ia: Mapped[str] = mapped_column(Text, nullable=False)
    fortalezas: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    modelo_usado: Mapped[str] = mapped_column(String(120), nullable=False)
    tiempo_proceso_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_analisis: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ssas.infrastructure.database.base import Base


class PostulanteHabilidadModel(Base):
    __tablename__ = "postulante_habilidad"
    __table_args__ = (
        CheckConstraint("anios_experiencia >= 0", name="ck_postulante_habilidad_experiencia"),
        UniqueConstraint(
            "postulante_id", "habilidad_id", name="uq_postulante_habilidad_postulante_habilidad"
        ),
        Index("idx_postulante_habilidad_postulante_id", "postulante_id"),
        Index("idx_postulante_habilidad_habilidad_id", "habilidad_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    postulante_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("postulante.id", ondelete="RESTRICT"), nullable=False
    )
    habilidad_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("habilidad.id", ondelete="RESTRICT"), nullable=False
    )
    nivel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    anios_experiencia: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("0")
    )
    detectado_por_ia: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

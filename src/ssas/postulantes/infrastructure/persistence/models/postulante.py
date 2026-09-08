from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel


class PostulanteModel(Base):
    __tablename__ = "postulante"
    __table_args__ = (
        UniqueConstraint("empresa_id", "ci", name="uq_postulante_empresa_ci"),
        CheckConstraint(
            "nivel_educativo IN ('SECUNDARIA', 'TECNICO', 'LICENCIATURA', 'MAESTRIA', 'DOCTORADO')",
            name="ck_postulante_nivel_educativo",
        ),
        CheckConstraint(
            "fuente IN ('PORTAL_WEB', 'APP_MOVIL', 'LINKEDIN', 'REFERIDO', 'FERIA', 'OTRO')",
            name="ck_postulante_fuente",
        ),
        CheckConstraint(
            "anios_experiencia >= 0", name="ck_postulante_experiencia_no_negativa"
        ),
        Index("idx_postulante_empresa_id", "empresa_id"),
        Index("idx_postulante_email", "email"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    ci: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono: Mapped[str] = mapped_column(String(40), nullable=False)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    cv_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cv_texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin: Mapped[str | None] = mapped_column(Text, nullable=True)
    nivel_educativo: Mapped[str] = mapped_column(String(20), nullable=False)
    anios_experiencia: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    fuente: Mapped[str] = mapped_column(String(20), nullable=False)
    en_banco_talento: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    empresa: Mapped[EmpresaModel] = relationship(back_populates="postulantes")
    postulaciones: Mapped[list[PostulacionModel]] = relationship(back_populates="postulante")


Index(
    "uq_postulante_empresa_ci_ci",
    PostulanteModel.empresa_id,
    func.lower(PostulanteModel.ci),
    unique=True,
)

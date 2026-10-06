from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ssas.infrastructure.database.base import Base


class KnowledgeArticle(Base):
    __tablename__ = "conocimiento_articulo"
    __table_args__ = (Index("ix_conocimiento_articulo_empresa", "empresa_id"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id"), nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(160), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[str] = mapped_column(String(80), nullable=False, server_default="General")
    publico: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    publicado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KnowledgeChunk(Base):
    __tablename__ = "conocimiento_fragmento"
    __table_args__ = (Index("ix_conocimiento_fragmento_empresa", "empresa_id"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    articulo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("conocimiento_articulo.id", ondelete="CASCADE"),
        nullable=False,
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id"), nullable=False
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    vector: Mapped[list[float]] = mapped_column(JSONB, nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)

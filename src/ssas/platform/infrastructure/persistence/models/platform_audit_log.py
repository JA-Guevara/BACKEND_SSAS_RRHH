from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.platform.infrastructure.persistence.models.platform_admin import PlatformAdminModel


class PlatformAuditLogModel(Base):
    __tablename__ = "bitacora_plataforma"
    __table_args__ = (
        Index("idx_bitacora_plataforma_admin_id", "admin_id"),
        Index("idx_bitacora_plataforma_modulo", "modulo"),
        Index("idx_bitacora_plataforma_fecha", "fecha"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    admin_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("administrador_plataforma.id", ondelete="SET NULL"), nullable=True)
    actor_etiqueta: Mapped[str | None] = mapped_column(String(150), nullable=True)
    modulo: Mapped[str] = mapped_column(String(80), nullable=False)
    accion: Mapped[str] = mapped_column(String(100), nullable=False)
    nivel: Mapped[str] = mapped_column(String(16), nullable=False, server_default="INFO")
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    tabla_afectada: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registro_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    datos_previos: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    datos_nuevos: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_origen: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    admin: Mapped["PlatformAdminModel | None"] = relationship(back_populates="audit_logs")

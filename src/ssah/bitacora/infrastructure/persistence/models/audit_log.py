from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssah.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssah.auth.infrastructure.persistence.models.user import UserModel
    from ssah.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class AuditLogModel(Base):
    __tablename__ = "bitacora"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    empresa_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column("usuario_id", UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column("accion", String(100), nullable=False, index=True)
    tabla_afectada: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registro_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    datos_previos_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    datos_nuevos_jsonb: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_origen: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="bitacoras")
    user: Mapped["UserModel | None"] = relationship(back_populates="bitacoras")
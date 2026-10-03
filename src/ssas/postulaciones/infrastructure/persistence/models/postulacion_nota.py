from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.auth.infrastructure.persistence.models.user import UserModel
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel


class PostulacionNotaModel(Base):
    """Nota interna del equipo de reclutamiento sobre una postulación.

    No tiene ``empresa_id``: la empresa se deriva siempre de ``postulacion.vacante``,
    igual que en ``postulacion``. Es un registro de solo anexado (sin edición ni
    borrado) para que el historial de evaluación quede trazable.
    """

    __tablename__ = "postulacion_nota"
    __table_args__ = (
        Index("idx_postulacion_nota_postulacion_id", "postulacion_id"),
        Index("idx_postulacion_nota_usuario_id", "usuario_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    postulacion_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("postulacion.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    postulacion: Mapped[PostulacionModel] = relationship(back_populates="notas_internas")
    usuario: Mapped[UserModel] = relationship()

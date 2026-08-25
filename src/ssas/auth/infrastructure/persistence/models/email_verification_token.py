from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.auth.infrastructure.persistence.models.user import UserModel
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class EmailVerificationTokenModel(Base):
    __tablename__ = "email_verification_token"
    __table_args__ = (
        Index("idx_email_verification_token_usuario_id", "usuario_id"),
        Index("idx_email_verification_token_expires_at", "expires_at"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    # NULL cuando el token pertenece a un administrador de la plataforma.
    empresa_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(
        "usuario_id",
        UUID(as_uuid=False),
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    empresa: Mapped["EmpresaModel | None"] = relationship()
    user: Mapped["UserModel"] = relationship()

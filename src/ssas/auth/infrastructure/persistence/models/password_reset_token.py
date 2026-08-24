from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.auth.infrastructure.persistence.models.user import UserModel
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_token"
    __table_args__ = (
        Index("idx_password_reset_token_empresa_id", "empresa_id"),
        Index("idx_password_reset_token_usuario_id", "usuario_id"),
        Index("idx_password_reset_token_expires_at", "expires_at"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    empresa_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column("usuario_id", UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column("consumed_at", DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="password_reset_tokens")
    user: Mapped["UserModel"] = relationship(back_populates="password_reset_tokens")

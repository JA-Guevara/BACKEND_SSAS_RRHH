from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssah.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssah.auth.infrastructure.persistence.models.user import UserModel
    from ssah.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_token"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    empresa_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column("usuario_id", UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column("consumed_at", DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="password_reset_tokens")
    user: Mapped["UserModel"] = relationship(back_populates="password_reset_tokens")
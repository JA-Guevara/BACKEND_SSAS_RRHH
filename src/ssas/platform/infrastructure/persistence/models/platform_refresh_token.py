from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.platform.infrastructure.persistence.models.platform_admin import PlatformAdminModel


class PlatformRefreshTokenModel(Base):
    __tablename__ = "platform_refresh_token"
    __table_args__ = (
        Index("idx_platform_refresh_admin_id", "admin_id"),
        Index("idx_platform_refresh_expires_at", "expires_at"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    admin_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("administrador_plataforma.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    admin: Mapped["PlatformAdminModel"] = relationship(back_populates="refresh_tokens")

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.platform.infrastructure.persistence.models.platform_audit_log import (
        PlatformAuditLogModel,
    )
    from ssas.platform.infrastructure.persistence.models.platform_refresh_token import (
        PlatformRefreshTokenModel,
    )


class PlatformAdminModel(Base):
    __tablename__ = "administrador_plataforma"
    __table_args__ = (
        CheckConstraint("intentos_fallidos >= 0", name="ck_admin_plataforma_intentos_no_negativo"),
        Index("idx_admin_plataforma_bloqueado_hasta", "bloqueado_hasta"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultimo_intento_fallido: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    refresh_tokens: Mapped[list["PlatformRefreshTokenModel"]] = relationship(back_populates="admin", cascade="all, delete-orphan")
    audit_logs: Mapped[list["PlatformAuditLogModel"]] = relationship(back_populates="admin")


Index("uq_admin_plataforma_email_ci", func.lower(PlatformAdminModel.email), unique=True)
Index("uq_admin_plataforma_username_ci", func.lower(PlatformAdminModel.username), unique=True)

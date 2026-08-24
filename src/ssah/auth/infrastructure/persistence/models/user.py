from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssah.infrastructure.database.base import Base
from ssah.roles.infrastructure.persistence.models.role import RoleModel
from ssah.roles.infrastructure.persistence.models.user_role import usuario_rol_table

if TYPE_CHECKING:
    from ssah.auth.infrastructure.persistence.models.password_reset_token import PasswordResetTokenModel
    from ssah.auth.infrastructure.persistence.models.refresh_token import RefreshTokenModel
    from ssah.bitacora.infrastructure.persistence.models.audit_log import AuditLogModel
    from ssah.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class UserModel(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        UniqueConstraint("empresa_id", "email", name="uq_usuario_empresa_email"),
        UniqueConstraint("empresa_id", "username", name="uq_usuario_empresa_username"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    empresa_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column("nombre", String(120), nullable=False)
    apellido: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    email: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    hashed_password: Mapped[str] = mapped_column("password_hash", String, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, server_default="true")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="usuarios")
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary=usuario_rol_table,
        primaryjoin=lambda: UserModel.id == usuario_rol_table.c.usuario_id,
        secondaryjoin=lambda: RoleModel.id == usuario_rol_table.c.rol_id,
        viewonly=True,
    )
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens: Mapped[list["PasswordResetTokenModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bitacoras: Mapped[list["AuditLogModel"]] = relationship(back_populates="user")
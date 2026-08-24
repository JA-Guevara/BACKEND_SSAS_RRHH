from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.empresas.infrastructure.persistence.models.parametro_valor import ParametroValorModel


class ParametroLegalModel(Base):
    __tablename__ = "parametro_legal"
    __table_args__ = (UniqueConstraint("pais", "codigo", name="uq_parametro_legal_pais_codigo"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    pais: Mapped[str] = mapped_column(String(80), nullable=False, server_default="Bolivia")
    codigo: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_valor: Mapped[str] = mapped_column(String(50), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    valores: Mapped[list["ParametroValorModel"]] = relationship(back_populates="parametro_legal", cascade="all, delete-orphan")
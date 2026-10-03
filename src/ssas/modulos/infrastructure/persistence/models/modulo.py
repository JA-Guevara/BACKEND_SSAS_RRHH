from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ssas.infrastructure.database.base import Base


class ModuloModel(Base):
    """Catálogo global de módulos contratables.

    ``codigo`` coincide con ``permiso.modulo``: es la bisagra que permite filtrar los
    permisos efectivos de una empresa sin tocar los guards de cada endpoint.
    """

    __tablename__ = "modulo"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    codigo: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    icono: Mapped[str | None] = mapped_column(String(60), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    # Un módulo núcleo no se puede deshabilitar: sin él la empresa no puede ni
    # administrar sus propios usuarios.
    es_core: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

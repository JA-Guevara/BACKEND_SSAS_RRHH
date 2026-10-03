from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ssas.infrastructure.database.base import Base


class EmpleadoModel(Base):
    __tablename__ = "empleado"
    __table_args__ = (
        CheckConstraint(
            "fecha_salida IS NULL OR fecha_salida >= fecha_ingreso", name="ck_empleado_fechas"
        ),
        CheckConstraint("estado IN ('ACTIVO', 'INACTIVO')", name="ck_empleado_estado"),
        UniqueConstraint("empresa_id", "codigo", name="uq_empleado_empresa_codigo"),
        UniqueConstraint("empresa_id", "ci", name="uq_empleado_empresa_ci"),
        Index("idx_empleado_empresa_id", "empresa_id"),
        Index("idx_empleado_usuario_id", "usuario_id"),
        Index("idx_empleado_empresa_id_estado", "empresa_id", "estado"),
        Index("idx_empleado_fecha_ingreso", "fecha_ingreso"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="RESTRICT"), nullable=False
    )
    usuario_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=True
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido_materno: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ci: Mapped[str] = mapped_column(String(30), nullable=False)
    ci_expedido: Mapped[str] = mapped_column(String(10), nullable=False)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    genero: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado_civil: Mapped[str | None] = mapped_column(String(30), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email_personal: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contacto_emergencia: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefono_emergencia: Mapped[str | None] = mapped_column(String(40), nullable=True)
    nua_cua: Mapped[str | None] = mapped_column(String(40), nullable=True)
    afp: Mapped[str | None] = mapped_column(String(80), nullable=True)
    banco: Mapped[str | None] = mapped_column(String(120), nullable=True)
    numero_cuenta: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tipo_cuenta: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_salida: Mapped[date | None] = mapped_column(Date, nullable=True)
    motivo_salida: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'ACTIVO'"))
    foto_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


Index(
    "uq_empleado_empresa_codigo_ci",
    EmpleadoModel.empresa_id,
    func.lower(EmpleadoModel.codigo),
    unique=True,
)

Index(
    "uq_empleado_empresa_ci_ci",
    EmpleadoModel.empresa_id,
    func.lower(EmpleadoModel.ci),
    unique=True,
)

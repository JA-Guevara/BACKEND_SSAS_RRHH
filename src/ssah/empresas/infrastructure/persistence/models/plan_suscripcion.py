from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssah.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssah.empresas.infrastructure.persistence.models.suscripcion import SuscripcionModel


class PlanSuscripcionModel(Base):
    __tablename__ = "plan_suscripcion"
    __table_args__ = (
        CheckConstraint("precio_mensual >= 0", name="chk_plan_precio_no_negativo"),
        CheckConstraint("max_empleados > 0", name="chk_plan_max_empleados_positivo"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    precio_mensual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    max_empleados: Mapped[int] = mapped_column(Integer, nullable=False)
    modulos: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    suscripciones: Mapped[list["SuscripcionModel"]] = relationship(back_populates="plan")
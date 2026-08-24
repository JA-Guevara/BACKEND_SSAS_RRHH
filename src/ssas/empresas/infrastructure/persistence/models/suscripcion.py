from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssas.empresas.infrastructure.persistence.models.plan_suscripcion import (
        PlanSuscripcionModel,
    )


class SuscripcionModel(Base):
    __tablename__ = "suscripcion"
    __table_args__ = (
        CheckConstraint("fecha_fin IS NULL OR fecha_fin >= fecha_inicio", name="chk_suscripcion_fechas"),
        Index("idx_suscripcion_empresa_id", "empresa_id"),
        Index("idx_suscripcion_plan_id", "plan_id"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    empresa_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("plan_suscripcion.id", ondelete="RESTRICT"), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="suscripciones")
    plan: Mapped["PlanSuscripcionModel"] = relationship(back_populates="suscripciones")

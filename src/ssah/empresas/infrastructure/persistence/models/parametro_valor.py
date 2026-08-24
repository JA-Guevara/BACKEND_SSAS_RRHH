from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssah.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssah.empresas.infrastructure.persistence.models.empresa import EmpresaModel
    from ssah.empresas.infrastructure.persistence.models.parametro_legal import ParametroLegalModel


class ParametroValorModel(Base):
    __tablename__ = "parametro_valor"
    __table_args__ = (CheckConstraint("vigente_hasta IS NULL OR vigente_hasta >= vigente_desde", name="chk_parametro_valor_fechas"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid())
    empresa_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False, index=True)
    parametro_legal_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("parametro_legal.id", ondelete="CASCADE"), nullable=False, index=True)
    norma_legal: Mapped[str | None] = mapped_column(String(150), nullable=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="parametros_valor")
    parametro_legal: Mapped["ParametroLegalModel"] = relationship(back_populates="valores")
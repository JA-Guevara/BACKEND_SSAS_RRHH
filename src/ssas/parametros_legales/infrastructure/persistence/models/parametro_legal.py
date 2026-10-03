from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ssas.infrastructure.database.base import Base

if TYPE_CHECKING:
    from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel


class ParametroLegalModel(Base):
    __tablename__ = "parametro_legal"
    __table_args__ = (
        CheckConstraint(
            "vigencia_hasta >= vigencia_desde",
            name="chk_parametro_legal_rango_vigencia",
        ),
        CheckConstraint(
            "afp BETWEEN 0 AND 100",
            name="chk_parametro_legal_afp",
        ),
        CheckConstraint(
            "aporte_solidario IS NULL OR aporte_solidario BETWEEN 0 AND 100",
            name="chk_parametro_legal_aporte_solidario",
        ),
        CheckConstraint(
            "rc_iva IS NULL OR rc_iva BETWEEN 0 AND 100",
            name="chk_parametro_legal_rc_iva",
        ),
        CheckConstraint(
            "aguinaldo IS NULL OR aguinaldo BETWEEN 0 AND 100",
            name="chk_parametro_legal_aguinaldo",
        ),
        CheckConstraint(
            "prima IS NULL OR prima BETWEEN 0 AND 100",
            name="chk_parametro_legal_prima",
        ),
        Index("idx_parametro_legal_empresa_vigencia", "empresa_id", "vigencia_desde"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, server_default=func.gen_random_uuid()
    )
    empresa_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("empresa.id", ondelete="CASCADE"), nullable=False
    )
    vigencia_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigencia_hasta: Mapped[date] = mapped_column(Date, nullable=False)
    afp: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    aporte_solidario: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rc_iva: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    aguinaldo: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    prima: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    empresa: Mapped["EmpresaModel"] = relationship(back_populates="parametros_legales")
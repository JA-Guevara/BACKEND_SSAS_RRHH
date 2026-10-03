from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

PORCENTAJE = (0, 100)


class ParametroLegalRequest(BaseModel):
    vigencia_desde: date
    vigencia_hasta: date
    afp: Decimal | None = Field(default=None, ge=0, le=100)
    aporte_solidario: Decimal | None = Field(default=None, ge=0, le=100)
    rc_iva: Decimal | None = Field(default=None, ge=0, le=100)
    aguinaldo: Decimal | None = Field(default=None, ge=0, le=100)
    prima: Decimal | None = Field(default=None, ge=0, le=100)

    @model_validator(mode="after")
    def validar_rango(self):
        if self.vigencia_desde > self.vigencia_hasta:
            raise ValueError("vigencia_desde no puede ser posterior a vigencia_hasta")
        return self


class ActualizarParametroLegalRequest(BaseModel):
    vigencia_desde: date | None = None
    vigencia_hasta: date | None = None
    afp: Decimal | None = Field(default=None, ge=0, le=100)
    aporte_solidario: Decimal | None = Field(default=None, ge=0, le=100)
    rc_iva: Decimal | None = Field(default=None, ge=0, le=100)
    aguinaldo: Decimal | None = Field(default=None, ge=0, le=100)
    prima: Decimal | None = Field(default=None, ge=0, le=100)


class ParametroLegalResponse(BaseModel):
    id: str
    empresa_id: str
    vigencia_desde: date
    vigencia_hasta: date
    afp: Decimal | None
    aporte_solidario: Decimal | None
    rc_iva: Decimal | None
    aguinaldo: Decimal | None
    prima: Decimal | None
    vigente: bool
    created_at: datetime
    updated_at: datetime
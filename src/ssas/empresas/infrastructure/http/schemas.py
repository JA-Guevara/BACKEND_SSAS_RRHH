from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, model_validator


class ParametroEmpresaResponse(BaseModel):
    codigo: str
    nombre: str
    tipo_valor: str
    descripcion: str | None = None
    valor_id: str | None = None
    valor: Decimal | None = None
    norma_legal: str | None = None
    vigente_desde: date | None = None
    vigente_hasta: date | None = None
    updated_at: datetime | None = None


class ActualizarParametroEmpresaRequest(BaseModel):
    valor: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    vigente_desde: date
    vigente_hasta: date | None = None
    norma_legal: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def validate_vigencia(self):
        if self.vigente_hasta is not None and self.vigente_hasta < self.vigente_desde:
            raise ValueError("vigente_hasta debe ser mayor o igual a vigente_desde")
        return self


class MiEmpresaUpdateRequest(BaseModel):
    nombre_comercial: str | None = Field(default=None, min_length=2, max_length=200)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=40)
    direccion: str | None = None
    ciudad: str | None = Field(default=None, max_length=100)
    logo_url: str | None = None

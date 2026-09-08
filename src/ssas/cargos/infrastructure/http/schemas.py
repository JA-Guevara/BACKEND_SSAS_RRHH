from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _validar_rango_salarial(salario_min: Decimal | None, salario_max: Decimal | None) -> None:
    if salario_min is not None and salario_max is not None and salario_min > salario_max:
        raise ValueError("El salario mínimo no puede ser mayor que el salario máximo")


class CrearCargoRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    codigo: str | None = Field(default=None, max_length=40)
    departamento_id: str | None = None
    descripcion: str | None = Field(default=None, max_length=1000)
    nivel: str | None = Field(default=None, max_length=80)
    salario_min: Decimal | None = None
    salario_max: Decimal | None = None
    activo: bool = True

    @model_validator(mode="after")
    def _validar_rangos(self) -> "CrearCargoRequest":
        _validar_rango_salarial(self.salario_min, self.salario_max)
        return self


class ActualizarCargoRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    codigo: str | None = Field(default=None, max_length=40)
    departamento_id: str | None = None
    descripcion: str | None = Field(default=None, max_length=1000)
    nivel: str | None = Field(default=None, max_length=80)
    salario_min: Decimal | None = None
    salario_max: Decimal | None = None
    activo: bool | None = None

    @model_validator(mode="after")
    def _validar_rangos(self) -> "ActualizarCargoRequest":
        _validar_rango_salarial(self.salario_min, self.salario_max)
        return self


class CargoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    empresa_id: str
    departamento_id: str | None
    nombre: str
    codigo: str | None = None
    descripcion: str | None = None
    nivel: str | None = None
    salario_min: Decimal | None = None
    salario_max: Decimal | None = None
    activo: bool
    created_at: datetime
    updated_at: datetime


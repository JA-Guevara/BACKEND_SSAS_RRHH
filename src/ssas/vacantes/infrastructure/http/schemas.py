from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Modalidad = Literal["PRESENCIAL", "REMOTO", "HIBRIDO"]
EstadoVacante = Literal["BORRADOR", "PUBLICADA", "PAUSADA", "CERRADA", "CANCELADA"]


class CrearVacanteRequest(BaseModel):
    cargo_id: str
    departamento_id: str
    titulo: str = Field(min_length=3, max_length=180)
    descripcion: str = Field(min_length=3)
    requisitos: str | None = None
    beneficios: str | None = None
    cantidad_vacantes: int = Field(default=1, gt=0)
    salario_min: Decimal | None = Field(default=None, ge=0)
    salario_max: Decimal | None = Field(default=None, ge=0)
    mostrar_salario: bool = False
    modalidad: Modalidad
    ubicacion: str | None = Field(default=None, max_length=160)
    experiencia_min: int = Field(default=0, ge=0)
    fecha_cierre: datetime | None = None

    @model_validator(mode="after")
    def validar_salario(self):
        if (
            self.salario_min is not None
            and self.salario_max is not None
            and self.salario_max < self.salario_min
        ):
            raise ValueError("salario_max debe ser mayor o igual que salario_min")
        return self


class ActualizarVacanteRequest(CrearVacanteRequest):
    cargo_id: str | None = None
    departamento_id: str | None = None
    titulo: str | None = Field(default=None, min_length=3, max_length=180)
    descripcion: str | None = Field(default=None, min_length=3)
    cantidad_vacantes: int | None = Field(default=None, gt=0)
    modalidad: Modalidad | None = None
    experiencia_min: int | None = Field(default=None, ge=0)


class VacanteResponse(BaseModel):
    id: str
    empresa_id: str
    cargo_id: str
    departamento_id: str
    responsable_id: str
    titulo: str
    descripcion: str
    requisitos: str | None
    beneficios: str | None
    cantidad_vacantes: int
    salario_min: Decimal | None
    salario_max: Decimal | None
    mostrar_salario: bool
    modalidad: str
    ubicacion: str | None
    experiencia_min: int
    fecha_publicacion: datetime | None
    fecha_cierre: datetime | None
    estado: str
    fecha_registro: datetime
    created_at: datetime
    updated_at: datetime


class VacantePublicaResponse(BaseModel):
    id: str
    empresa_nombre: str
    titulo: str
    descripcion: str
    requisitos: str | None
    beneficios: str | None
    cantidad_vacantes: int
    salario_min: Decimal | None
    salario_max: Decimal | None
    mostrar_salario: bool
    modalidad: str
    ubicacion: str | None
    experiencia_min: int
    fecha_publicacion: datetime
    fecha_cierre: datetime | None

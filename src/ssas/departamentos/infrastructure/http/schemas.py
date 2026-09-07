from datetime import datetime

from pydantic import BaseModel, Field


class CrearDepartamentoRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str | None = None
    activo: bool = True


class ActualizarDepartamentoRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    descripcion: str | None = None
    activo: bool | None = None


class DepartamentoResponse(BaseModel):
    id: str
    empresa_id: str
    nombre: str
    descripcion: str | None = None
    activo: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

from datetime import datetime

from pydantic import BaseModel, Field


class RespaldoSchema(BaseModel):
    id: str
    nombre: str
    formato: str
    tamano_bytes: int | None
    sha256: str | None
    estado: str
    creado_por_id: str
    fecha_creacion: datetime
    fecha_finalizacion: datetime | None
    fecha_restauracion: datetime | None
    restaurado_por_id: str | None
    mensaje_error: str | None

    model_config = {"from_attributes": True}


class CrearRespaldoSchema(BaseModel):
    nombre: str | None = Field(default=None, max_length=180)


class RestaurarRespaldoSchema(BaseModel):
    confirmacion: str = Field(min_length=1, max_length=100)


class OperacionRespaldoSchema(BaseModel):
    id: str
    estado: str
    mensaje: str


class RespaldoProgramacionSchema(BaseModel):
    id: str
    empresa_id: str | None = None
    nombre: str
    frecuencia: str  # DIARIA | SEMANAL | MENSUAL
    hora: str
    dia_semana: int | None = None
    dia_mes: int | None = None
    retencion_dias: int
    activo: bool
    ultima_ejecucion: datetime | None = None
    proxima_ejecucion: datetime
    creado_por_id: str
    fecha_creacion: datetime

    model_config = {"from_attributes": True}


class CrearRespaldoProgramacionSchema(BaseModel):
    empresa_id: str | None = None
    nombre: str = Field(min_length=2, max_length=120)
    frecuencia: str = Field(pattern="^(DIARIA|SEMANAL|MENSUAL)$")
    hora: str = Field(pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    dia_mes: int | None = Field(default=None, ge=1, le=28)
    retencion_dias: int = Field(default=30, ge=1, le=365)


class ActualizarRespaldoProgramacionSchema(BaseModel):
    nombre: str | None = Field(default=None, max_length=120)
    frecuencia: str | None = Field(default=None, pattern="^(DIARIA|SEMANAL|MENSUAL)$")
    hora: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    dia_mes: int | None = Field(default=None, ge=1, le=28)
    retencion_dias: int | None = Field(default=None, ge=1, le=365)
    activo: bool | None = None


class VerificarIntegridadResponseSchema(BaseModel):
    id: str
    sha256_registrado: str | None
    sha256_calculado: str
    integro: bool
    tamano_bytes: int

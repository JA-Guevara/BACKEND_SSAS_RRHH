from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

TipoEntrevista = Literal["TECNICA", "TELEFONICA", "VIRTUAL", "PRESENCIAL", "PSICOLOGICA"]
Modalidad = Literal["VIRTUAL", "PRESENCIAL", "TELEFONICA"]
EstadoEntrevista = Literal["PROGRAMADA", "CONFIRMADA", "REALIZADA", "CANCELADA"]


class EntrevistaRequest(BaseModel):
    postulacion_id: UUID
    entrevistador_id: UUID
    tipo: TipoEntrevista
    fecha_hora: datetime
    duracion_min: int = Field(default=45, ge=1, le=480)
    modalidad: Modalidad
    enlace_reunion: str = Field(default="", max_length=1000)
    lugar: str = Field(default="", max_length=1000)


class EntrevistaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    postulacion_id: str
    entrevistador_id: str
    tipo: str
    fecha_hora: datetime
    duracion_min: int
    modalidad: str
    enlace_reunion: str | None
    lugar: str | None
    estado: str
    puntaje: Decimal | None
    observaciones: str | None
    recomendacion: str | None
    fecha_registro: datetime
    nombre_postulante: str | None = None
    entrevistador_nombre: str | None = None


class EstadoRequest(BaseModel):
    estado: Literal["CONFIRMADA", "CANCELADA"]


class ResultadoRequest(BaseModel):
    puntaje: Decimal = Field(ge=0, le=100)
    observaciones: str = Field(min_length=1, max_length=4000)
    recomendacion: str = Field(min_length=1, max_length=40)


class EvaluacionRequest(BaseModel):
    evaluador_id: UUID | None = None
    tipo: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=150)
    puntaje: Decimal = Field(ge=0)
    puntaje_maximo: Decimal = Field(gt=0, le=10000)
    aprobado: bool
    observaciones: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validar_puntaje(self):
        if self.puntaje > self.puntaje_maximo:
            raise ValueError("El puntaje no puede superar el máximo")
        return self


class EvaluacionResponse(EvaluacionRequest):
    model_config = ConfigDict(from_attributes=True)
    id: str
    postulacion_id: str
    evaluador_id: str
    observaciones: str | None = None
    evaluador_nombre: str | None = None
    archivo_url: str | None
    fecha: datetime


class AnalisisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    postulacion_id: str
    puntaje_afinidad: Decimal
    habilidades_detectadas: list[str]
    habilidades_faltantes: list[str]
    anios_experiencia_detectados: float | None
    resumen_ia: str
    fortalezas: list[str]
    observaciones: str | None
    modelo_usado: str
    tiempo_proceso_ms: int
    fecha_analisis: datetime


class ContratarRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    apellido_paterno: str = Field(min_length=1, max_length=120)
    apellido_materno: str = Field(default="", max_length=120)
    ci_expedido: Literal["SC", "LP", "CB", "OR", "PT", "TJ", "CH", "BE", "PD"]
    fecha_ingreso: date


class EmpleadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    empresa_id: str
    codigo: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str | None
    fecha_ingreso: date
    estado: str


class CompararRequest(BaseModel):
    postulacion_ids: list[UUID] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def distintos(self):
        if len(set(self.postulacion_ids)) != len(self.postulacion_ids):
            raise ValueError("Selecciona postulaciones diferentes")
        return self


class VacanteSeleccionResponse(BaseModel):
    id: str
    titulo: str
    habilidades: list[str]


class BancoRequest(BaseModel):
    en_banco_talento: bool


class AsociarRequest(BaseModel):
    vacante_id: UUID


class CandidatoResponse(BaseModel):
    id: str
    postulante_id: str
    nombre_postulante: str
    estado: str
    experiencia_anios: int
    educacion: str
    puntaje_ia: float | None
    puntaje_manual: float | None
    puntaje_evaluaciones: float | None
    puntaje_entrevistas: float | None
    habilidades_detectadas: list[str]
    habilidades_faltantes: list[str]
    entrevistas: list[EntrevistaResponse]
    evaluaciones: list[EvaluacionResponse]


class RankingResponse(BaseModel):
    items: list[CandidatoResponse]
    total: int


class AgendaResponse(BaseModel):
    items: list[EntrevistaResponse]
    total: int


class EventoResponse(BaseModel):
    id: str
    tipo: str
    fecha: datetime
    responsable: str
    puntaje: float | None = None
    recomendacion: str = ""
    observaciones: str = ""


class EntrevistadorOpcion(BaseModel):
    id: str
    nombre: str
    rol: str


class PostulacionOpcion(BaseModel):
    id: str
    nombre_postulante: str
    vacante: str


class OpcionesResponse(BaseModel):
    entrevistadores: list[EntrevistadorOpcion]
    postulaciones: list[PostulacionOpcion]

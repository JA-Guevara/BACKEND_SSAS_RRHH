from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from ssas.reportes.infrastructure.http.schemas import FiltroReporte, OrdenReporte


class Agregacion(StrEnum):
    CONTEO = "conteo"
    CONTEO_DISTINTO = "conteo_distinto"
    SUMA = "suma"
    PROMEDIO = "promedio"
    MINIMO = "minimo"
    MAXIMO = "maximo"


class Medida(BaseModel):
    agregacion: Agregacion
    campo: str | None = None
    etiqueta: str | None = None

    @model_validator(mode="after")
    def campo_requerido(self):
        if self.agregacion != Agregacion.CONTEO and not self.campo:
            raise ValueError("Esa agregación necesita un campo")
        return self


class ConsultaAgregada(BaseModel):
    fuente: str
    medidas: list[Medida] = Field(min_length=1, max_length=4)
    agrupar_por: list[str] = Field(default_factory=list, max_length=2)
    granularidad: Literal["dia", "semana", "mes", "trimestre", "anio"] | None = None
    filtros: list[FiltroReporte] = Field(default_factory=list, max_length=10)
    orden: list[OrdenReporte] = Field(default_factory=list, max_length=2)
    limite: int = Field(default=50, ge=1, le=500)


class SerieAgregada(BaseModel):
    """Una fila del resultado: las claves de agrupación más los valores de cada medida."""

    claves: dict[str, Any]
    valores: dict[str, float | None]


class RespuestaAgregada(BaseModel):
    series: list[SerieAgregada]
    medidas: list[str]
    total_grupos: int
    truncado: bool
    generado_en: datetime
    milisegundos: int
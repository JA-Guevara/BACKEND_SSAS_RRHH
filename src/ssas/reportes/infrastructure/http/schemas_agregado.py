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


class CrearWidgetPanel(BaseModel):
    titulo: str = Field(min_length=1, max_length=120)
    tipo: Literal["kpi", "linea", "barra", "barra_apilada", "embudo", "tabla"]
    consulta: ConsultaAgregada
    posicion: int = Field(default=0, ge=0)
    ancho: int = Field(default=2, ge=1, le=4)


class ActualizarWidgetPanel(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=120)
    tipo: Literal["kpi", "linea", "barra", "barra_apilada", "embudo", "tabla"] | None = None
    consulta: ConsultaAgregada | None = None
    posicion: int | None = Field(default=None, ge=0)
    ancho: int | None = Field(default=None, ge=1, le=4)
    activo: bool | None = None


class WidgetPanelResponse(BaseModel):
    id: str
    empresa_id: str
    usuario_id: str
    titulo: str
    tipo: Literal["kpi", "linea", "barra", "barra_apilada", "embudo", "tabla"]
    consulta: ConsultaAgregada
    posicion: int
    ancho: int
    activo: bool
    fecha_registro: datetime


class PanelResponse(BaseModel):
    widgets: list[WidgetPanelResponse]
    origen: Literal["guardadas", "predeterminadas"]
    omitidas_por_permiso: list[str]
    fuentes_disponibles: list[str]
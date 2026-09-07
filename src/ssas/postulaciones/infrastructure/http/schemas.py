from datetime import datetime

from pydantic import BaseModel


class PostulacionPublicaResponse(BaseModel):
    id: str
    codigo_seguimiento: str
    estado: str
    fecha_postulacion: datetime


class SeguimientoPostulacionResponse(BaseModel):
    codigo_seguimiento: str
    estado: str
    etapa: str
    vacante: str
    fecha_postulacion: datetime
    fecha_ultimo_cambio: datetime

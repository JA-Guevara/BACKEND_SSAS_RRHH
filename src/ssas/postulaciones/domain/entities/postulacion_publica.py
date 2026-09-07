from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VacantePublica:
    id: str
    empresa_id: str
    titulo: str
    estado: str


@dataclass(frozen=True)
class PostulantePublico:
    id: str
    empresa_id: str
    ci: str


@dataclass(frozen=True)
class DatosPostulantePublico:
    vacante_id: str
    nombres: str
    apellidos: str
    ci: str
    email: str
    telefono: str
    ciudad: str
    nivel_educativo: str
    anios_experiencia: int
    linkedin: str | None


@dataclass(frozen=True)
class CvAdjunto:
    filename: str
    content_type: str | None
    content: bytes


@dataclass(frozen=True)
class PostulacionCreada:
    id: str
    codigo_seguimiento: str
    estado: str
    fecha_postulacion: datetime


@dataclass(frozen=True)
class PostulacionSeguimiento:
    codigo_seguimiento: str
    estado: str
    etapa: str
    vacante: str
    fecha_postulacion: datetime
    fecha_ultimo_cambio: datetime

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Postulante:
    id: str
    empresa_id: str
    nombres: str
    apellidos: str
    ci: str
    email: str
    telefono: str
    direccion: str | None
    ciudad: str
    fecha_nacimiento: date | None
    cv_url: str | None
    cv_texto: str | None
    linkedin: str | None
    nivel_educativo: str
    anios_experiencia: int
    fuente: str
    en_banco_talento: bool
    fecha_registro: datetime
    created_at: datetime
    updated_at: datetime

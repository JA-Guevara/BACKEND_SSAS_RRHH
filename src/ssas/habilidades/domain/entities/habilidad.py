from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Habilidad:
    id: str
    empresa_id: str
    nombre: str
    categoria: str | None
    descripcion: str | None
    activo: bool
    created_at: datetime
    updated_at: datetime

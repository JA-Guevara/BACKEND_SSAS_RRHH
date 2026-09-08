from dataclasses import dataclass
from datetime import datetime


@dataclass
class Departamento:
    id: str
    empresa_id: str
    nombre: str
    codigo: str | None = None
    descripcion: str | None = None
    departamento_padre_id: str | None = None
    responsable_id: str | None = None
    activo: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


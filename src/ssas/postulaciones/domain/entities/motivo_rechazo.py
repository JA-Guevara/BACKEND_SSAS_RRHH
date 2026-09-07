from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MotivoRechazo:
    id: str
    empresa_id: str
    nombre: str
    descripcion: str | None
    activo: bool
    created_at: datetime
    updated_at: datetime

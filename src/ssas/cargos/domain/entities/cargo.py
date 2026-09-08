from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Cargo:
    id: str
    empresa_id: str
    nombre: str
    codigo: str | None = None
    departamento_id: str | None = None
    descripcion: str | None = None
    nivel: str | None = None
    salario_min: Decimal | None = None
    salario_max: Decimal | None = None
    activo: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


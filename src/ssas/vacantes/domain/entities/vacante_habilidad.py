from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class VacanteHabilidad:
    id: str
    vacante_id: str
    habilidad_id: str
    nivel_requerido: str
    es_obligatorio: bool
    peso: Decimal
    created_at: datetime
    updated_at: datetime

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EtapaReclutamiento:
    id: str
    empresa_id: str
    nombre: str
    orden: int
    color: str | None
    es_inicial: bool
    es_contratado: bool
    es_rechazado: bool
    created_at: datetime
    updated_at: datetime

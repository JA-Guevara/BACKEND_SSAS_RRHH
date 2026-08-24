from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class ParametroEmpresa:
    codigo: str
    nombre: str
    tipo_valor: str
    descripcion: str | None
    valor_id: str | None = None
    valor: Decimal | None = None
    norma_legal: str | None = None
    vigente_desde: date | None = None
    vigente_hasta: date | None = None
    updated_at: datetime | None = None
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class ParametroLegal:
    id: str
    empresa_id: str
    vigencia_desde: date
    vigencia_hasta: date
    afp: Decimal | None
    aporte_solidario: Decimal | None
    rc_iva: Decimal | None
    aguinaldo: Decimal | None
    prima: Decimal | None
    created_at: datetime
    updated_at: datetime

    @property
    def vigente(self) -> bool:
        hoy = datetime.now().astimezone().date()
        return self.vigencia_desde <= hoy <= self.vigencia_hasta
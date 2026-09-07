from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Postulacion:
    id: str
    vacante_id: str
    postulante_id: str
    etapa_id: str
    motivo_rechazo_id: str | None
    empleado_id: str | None
    puntaje_ia: Decimal | None
    puntaje_manual: Decimal | None
    notas: str | None
    codigo_seguimiento: str
    fecha_postulacion: datetime
    fecha_ultimo_cambio: datetime
    estado: str
    created_at: datetime
    updated_at: datetime

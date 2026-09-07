from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class VacantePublica:
    id: str
    empresa_nombre: str
    titulo: str
    descripcion: str
    requisitos: str | None
    beneficios: str | None
    cantidad_vacantes: int
    salario_min: Decimal | None
    salario_max: Decimal | None
    mostrar_salario: bool
    modalidad: str
    ubicacion: str | None
    experiencia_min: int
    fecha_publicacion: datetime
    fecha_cierre: datetime | None

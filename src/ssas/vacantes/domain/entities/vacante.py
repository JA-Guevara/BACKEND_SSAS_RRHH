from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class VacanteHabilidadInfo:
    habilidad_id: str
    nombre: str
    nivel_requerido: str
    es_obligatorio: bool = True
    peso: Decimal = Decimal("1.0")


@dataclass(frozen=True)
class Vacante:
    id: str
    empresa_id: str
    cargo_id: str
    departamento_id: str
    responsable_id: str
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
    fecha_publicacion: datetime | None
    fecha_cierre: datetime | None
    estado: str
    fecha_registro: datetime
    created_at: datetime
    updated_at: datetime
    cargo_nombre: str | None = None
    departamento_nombre: str | None = None
    habilidades: list[VacanteHabilidadInfo] = field(default_factory=list)

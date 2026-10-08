from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class EmpleadoListItem(BaseModel):
    """Fila de la grilla de empleados."""

    model_config = ConfigDict(from_attributes=True)
    id: str
    codigo: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str | None = None
    cargo_nombre: str | None = None  # resuelto por join
    fecha_ingreso: date
    estado: str


class EmpleadoDetalle(EmpleadoListItem):
    """Ficha completa del empleado. Incluye datos personales y bancarios."""

    empresa_id: str
    ci: str
    ci_expedido: str
    fecha_nacimiento: date | None = None
    genero: str | None = None
    estado_civil: str | None = None
    direccion: str | None = None
    telefono: str | None = None
    email_personal: str | None = None
    contacto_emergencia: str | None = None
    telefono_emergencia: str | None = None
    nua_cua: str | None = None
    afp: str | None = None
    banco: str | None = None
    numero_cuenta: str | None = None
    tipo_cuenta: str | None = None
    fecha_salida: date | None = None
    motivo_salida: str | None = None
    foto_url: str | None = None
    fecha_registro: datetime
    postulacion_id: str | None = None


class EmpleadosPage(BaseModel):
    items: list[EmpleadoListItem]
    total: int

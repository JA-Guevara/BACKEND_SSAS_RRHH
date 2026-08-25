from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class PlatformLoginRequest(BaseModel):
    login: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=1, max_length=72)


class PlatformRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class PlatformTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PlatformAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nombre: str
    apellido: str
    email: EmailStr
    username: str
    activo: bool
    email_verified: bool
    ultimo_acceso: datetime | None = None
    created_at: datetime


class PlatformChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=12, max_length=72)


class MessageResponse(BaseModel):
    message: str


class PlanCreateRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    precio_mensual: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    max_empleados: int = Field(gt=0)
    modulos: list[str] = Field(default_factory=list)
    activo: bool = True


class PlanUpdateRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    precio_mensual: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    max_empleados: int | None = Field(default=None, gt=0)
    modulos: list[str] | None = None
    activo: bool | None = None


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nombre: str
    precio_mensual: Decimal
    max_empleados: int
    modulos: list[Any]
    activo: bool
    created_at: datetime
    updated_at: datetime


class SubscriptionResponse(BaseModel):
    id: str
    empresa_id: str
    empresa_nombre: str | None = None
    plan: PlanResponse
    fecha_inicio: date
    fecha_fin: date | None = None
    activo: bool
    created_at: datetime


class SubscriptionPageResponse(BaseModel):
    items: list[SubscriptionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class SubscriptionUpdateRequest(BaseModel):
    plan_id: str
    fecha_inicio: date
    fecha_fin: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")
        return self


class EmpresaCreateData(BaseModel):
    nit: str | None = Field(default=None, max_length=30)
    razon_social: str = Field(min_length=2, max_length=200)
    nombre_comercial: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-zA-Z0-9-]+$")
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=40)
    direccion: str | None = None
    ciudad: str | None = Field(default=None, max_length=100)
    logo_url: str | None = None


class EmpresaUpdateRequest(BaseModel):
    nit: str | None = Field(default=None, max_length=30)
    razon_social: str | None = Field(default=None, min_length=2, max_length=200)
    nombre_comercial: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=120, pattern=r"^[a-zA-Z0-9-]+$")
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=40)
    direccion: str | None = None
    ciudad: str | None = Field(default=None, max_length=100)
    logo_url: str | None = None


class InitialAdminData(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    apellido: str = Field(min_length=1, max_length=120)
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=12, max_length=72)
    telefono: str | None = Field(default=None, max_length=40)


class ProvisionEmpresaRequest(BaseModel):
    empresa: EmpresaCreateData
    plan_id: str
    fecha_inicio: date
    fecha_fin: date | None = None
    administrador: InitialAdminData

    @model_validator(mode="after")
    def validate_dates(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")
        return self


class EmpresaResponse(BaseModel):
    id: str
    nit: str | None = None
    razon_social: str
    nombre_comercial: str
    slug: str
    email: EmailStr | None = None
    telefono: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    logo_url: str | None = None
    activo: bool
    fecha_registro: datetime
    suscripcion: SubscriptionResponse | None = None
    created_at: datetime
    updated_at: datetime


class EmpresaPageResponse(BaseModel):
    items: list[EmpresaResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ProvisionEmpresaResponse(BaseModel):
    empresa: EmpresaResponse
    administrador_id: str
    administrador_email: EmailStr
    verification_email_sent: bool


class PlatformAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    admin_id: str | None = None
    actor_etiqueta: str | None = None
    modulo: str
    accion: str
    nivel: str
    descripcion: str
    tabla_afectada: str | None = None
    registro_id: str | None = None
    datos_previos: dict[str, Any] | None = None
    datos_nuevos: dict[str, Any] | None = None
    ip_origen: str | None = None
    user_agent: str | None = None
    fecha: datetime


class PlatformAuditPageResponse(BaseModel):
    items: list[PlatformAuditResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

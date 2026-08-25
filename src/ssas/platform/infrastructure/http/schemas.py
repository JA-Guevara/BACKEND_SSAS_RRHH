from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


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
    administrador: InitialAdminData


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

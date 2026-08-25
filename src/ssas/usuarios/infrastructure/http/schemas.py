from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CrearUsuarioRequest(BaseModel):
    empresa_id: str | None = None
    nombre: str = Field(min_length=2, max_length=120)
    apellido: str = Field(min_length=1, max_length=120)
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=12, max_length=72)
    telefono: str | None = Field(default=None, max_length=40)
    role_ids: list[str] = Field(min_length=1)


class ActualizarUsuarioRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    apellido: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=80)
    telefono: str | None = Field(default=None, max_length=40)
    role_ids: list[str] | None = None


class UsuarioResponse(BaseModel):
    id: str
    empresa_id: str | None
    nombre: str
    apellido: str
    email: EmailStr
    username: str
    telefono: str | None = None
    is_active: bool
    email_verified: bool
    must_change_password: bool
    failed_login_attempts: int
    locked_until: datetime | None = None
    roles: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UsuarioPageResponse(BaseModel):
    items: list[UsuarioResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class CambiarPasswordUsuarioRequest(BaseModel):
    new_password: str = Field(min_length=12, max_length=72)
    must_change: bool = True

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CrearUsuarioRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    apellido: str = Field(min_length=1, max_length=120)
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=72)
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
    empresa_id: str
    nombre: str
    apellido: str
    email: EmailStr
    username: str
    telefono: str | None = None
    is_active: bool
    roles: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
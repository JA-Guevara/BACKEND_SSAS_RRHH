from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class LoginSchema(BaseModel):
    """Credenciales de acceso.

    ``empresa_slug`` decide DÓNDE se busca la cuenta:

        ausente  -> entre los administradores de la plataforma (empresa_id IS NULL)
        presente -> dentro de esa empresa

    Enviarlo con un valor inventado hace que no se encuentre la cuenta y la respuesta
    sea 401, aunque el correo y la contraseña sean correctos. En Swagger hay que
    BORRAR la línea, no dejar el valor de ejemplo.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Administrador de plataforma (sin empresa)",
                    "value": {"email": "admin@ssas.bo", "password": "TuClaveSegura.2026"},
                },
                {
                    "summary": "Usuario de una empresa",
                    "value": {
                        "empresa_slug": "conecta",
                        "email": "ana@conecta.bo",
                        "password": "TuClaveSegura.2026",
                    },
                },
            ]
        }
    )

    # Ausente = administrador de la plataforma (no pertenece a ninguna empresa).
    empresa_slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
        pattern=r"^[a-zA-Z0-9-]+$",
        description="Slug de la empresa. Omitir para administradores de plataforma.",
    )
    email: EmailStr | None = Field(default=None, description="Correo. Alternativa: username.")
    username: str | None = Field(default=None, min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=72)

    @model_validator(mode="after")
    def validate_login_identifier(self):
        if self.email is None and not self.username:
            raise ValueError("Debe enviar email o username")
        return self


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    must_change_password: bool = False


class RefreshTokenSchema(BaseModel):
    refresh_token: str = Field(min_length=1)


class ForgotPasswordSchema(BaseModel):
    email: EmailStr
    empresa_slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-zA-Z0-9-]+$")


class ForgotPasswordResponseSchema(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordSchema(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=12, max_length=72)


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=12, max_length=72)


class VerifyEmailSchema(BaseModel):
    token: str = Field(min_length=1)


class ResendVerificationSchema(BaseModel):
    email: EmailStr
    empresa_slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-zA-Z0-9-]+$")


class MessageSchema(BaseModel):
    message: str


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    empresa_id: str | None = None
    username: str | None = None
    roles: list[str] = Field(default_factory=list)
    is_active: bool
    email_verified: bool
    must_change_password: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

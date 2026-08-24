from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class LoginSchema(BaseModel):
    empresa_slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-zA-Z0-9-]+$")
    email: EmailStr | None = None
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
    new_password: str = Field(min_length=8, max_length=72)


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
    created_at: datetime | None = None
    updated_at: datetime | None = None

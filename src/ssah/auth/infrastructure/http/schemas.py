from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class RegisterSchema(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class TokenPairSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(BaseModel):
    refresh_token: str = Field(min_length=1)


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


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
    is_active: bool
    email_verified: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

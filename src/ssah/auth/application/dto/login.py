from dataclasses import dataclass


@dataclass(frozen=True)
class LoginRequest:
    email: str
    password: str


@dataclass(frozen=True)
class LoginResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
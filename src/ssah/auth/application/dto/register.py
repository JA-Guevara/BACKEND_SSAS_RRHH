from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterRequest:
    name: str
    email: str
    password: str


@dataclass(frozen=True)
class RegisterResponse:
    id: str
    name: str
    email: str
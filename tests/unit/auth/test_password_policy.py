import pytest

from ssas.auth.domain.exceptions import InvalidPasswordError
from ssas.auth.domain.password_policy import validate_password


def test_password_policy_accepts_strong_password() -> None:
    assert validate_password("Fuerte#2026.Valid") == "Fuerte#2026.Valid"


@pytest.mark.parametrize(
    "password",
    ["Corta#1", "sinmayuscula#2026", "SINMINUSCULA#2026", "SinNumero#Clave", "SinSimbolo2026", "Con Espacio#2026"],
)
def test_password_policy_rejects_weak_passwords(password: str) -> None:
    with pytest.raises(InvalidPasswordError):
        validate_password(password)


def test_password_policy_rejects_username_inside_password() -> None:
    with pytest.raises(InvalidPasswordError):
        validate_password("Usuario#Seguro2026", "usuario")

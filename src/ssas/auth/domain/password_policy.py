import re

from ssas.auth.domain.exceptions import InvalidPasswordError

COMMON_PASSWORDS = {
    "123456789012",
    "administrador",
    "contraseña123",
    "password1234",
    "qwerty123456",
}


def validate_password(password: str, *personal_values: str | None) -> str:
    """Valida una contraseña antes de cifrarla y devuelve el valor original."""
    errors: list[str] = []
    if len(password) < 12:
        errors.append("al menos 12 caracteres")
    if len(password) > 72:
        errors.append("máximo 72 caracteres")
    if not re.search(r"[a-z]", password):
        errors.append("una letra minúscula")
    if not re.search(r"[A-Z]", password):
        errors.append("una letra mayúscula")
    if not re.search(r"\d", password):
        errors.append("un número")
    if not re.search(r"[^A-Za-z0-9\s]", password):
        errors.append("un carácter especial")
    if re.search(r"\s", password):
        errors.append("ningún espacio")
    if password.casefold() in COMMON_PASSWORDS:
        errors.append("una contraseña que no sea común")

    normalized_password = password.casefold()
    for value in personal_values:
        if not value:
            continue
        candidate = value.split("@", 1)[0].strip().casefold()
        if len(candidate) >= 3 and candidate in normalized_password:
            errors.append("no contener el nombre de usuario ni el correo")
            break

    if errors:
        raise InvalidPasswordError("La contraseña debe tener " + ", ".join(errors))
    return password

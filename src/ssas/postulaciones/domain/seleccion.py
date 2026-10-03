from datetime import datetime


class SeleccionError(Exception):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


def transicion_entrevista(actual: str, siguiente: str) -> None:
    permitidas = {
        "PROGRAMADA": {"CONFIRMADA", "CANCELADA", "REALIZADA"},
        "CONFIRMADA": {"CANCELADA", "REALIZADA"},
        "REALIZADA": set(),
        "CANCELADA": set(),
    }
    if siguiente != actual and siguiente not in permitidas.get(actual, set()):
        raise SeleccionError("La entrevista no permite ese cambio de estado")


def validar_agenda(fecha: datetime, modalidad: str, enlace: str, lugar: str) -> None:
    if fecha.tzinfo is None or fecha.utcoffset() is None:
        raise SeleccionError("La fecha debe incluir zona horaria", 422)
    if modalidad == "VIRTUAL" and not enlace.startswith("https://"):
        raise SeleccionError("La entrevista virtual requiere un enlace HTTPS", 422)
    if modalidad == "PRESENCIAL" and not lugar.strip():
        raise SeleccionError("La entrevista presencial requiere un lugar", 422)

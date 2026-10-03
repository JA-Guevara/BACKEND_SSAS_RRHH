"""Metadatos confiables y normalizados de una petición HTTP."""

from ipaddress import ip_address

from fastapi import Request


def _normalize_ip(raw_value: str | None) -> str | None:
    """Devuelve una IPv4/IPv6 válida o ``None`` para no romper la columna INET."""
    if raw_value is None:
        return None

    value = raw_value.strip().strip('"')
    if not value:
        return None

    # X-Forwarded-For es una lista donde el primer elemento representa al cliente.
    value = value.split(",", 1)[0].strip()

    # Admite la notación habitual [IPv6]:puerto que algunos proxies producen.
    if value.startswith("[") and "]" in value:
        value = value[1 : value.index("]")]
    elif value.count(":") == 1:
        host, possible_port = value.rsplit(":", 1)
        if possible_port.isdigit():
            value = host

    try:
        return ip_address(value).compressed
    except ValueError:
        return None


def get_client_ip(request: Request) -> str | None:
    """Obtiene la IP del cliente real en Railway y conserva soporte para local.

    Railway termina TLS y añade ``X-Real-IP``. ``X-Forwarded-For`` permite operar
    detrás de otros proxies compatibles; ``request.client`` queda como último recurso.
    Todos los candidatos se validan antes de llegar a PostgreSQL ``INET``.
    """
    candidates = (
        request.headers.get("x-real-ip"),
        request.headers.get("x-forwarded-for"),
        request.client.host if request.client else None,
    )
    for candidate in candidates:
        normalized = _normalize_ip(candidate)
        if normalized is not None:
            return normalized
    return None


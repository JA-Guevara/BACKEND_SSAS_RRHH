from dataclasses import dataclass

import pytest
from fastapi import HTTPException

from ssas.core.api.tenancy import resolver_empresa


@dataclass
class _Usuario:
    id: str
    empresa_id: str | None
    es_plataforma: bool


def test_plataforma_exige_empresa() -> None:
    with pytest.raises(HTTPException) as exc:
        resolver_empresa(_Usuario("admin", None, True), None)

    assert exc.value.status_code == 422


def test_plataforma_usa_la_empresa_solicitada() -> None:
    assert resolver_empresa(_Usuario("admin", None, True), "empresa-b") == "empresa-b"


def test_tenant_resuelve_su_propia_empresa() -> None:
    user = _Usuario("u", "empresa-a", False)

    assert resolver_empresa(user, None) == "empresa-a"
    assert resolver_empresa(user, "empresa-a") == "empresa-a"


def test_tenant_no_puede_operar_sobre_otra_empresa() -> None:
    with pytest.raises(HTTPException) as exc:
        resolver_empresa(_Usuario("u", "empresa-a", False), "empresa-b")

    assert exc.value.status_code == 403
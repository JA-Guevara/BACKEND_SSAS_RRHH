import pytest
from fastapi import HTTPException

from ssas.habilidades.infrastructure.http.router import _empresa


class _Plataforma:
    es_plataforma = True
    empresa_id = None


class _Tenant:
    es_plataforma = False
    empresa_id = "empresa-a"


def test_plataforma_sin_empresa_devuelve_422() -> None:
    with pytest.raises(HTTPException) as exc:
        _empresa(_Plataforma(), None)
    assert exc.value.status_code == 422
    assert exc.value.detail == "Debe indicar empresa_id"


def test_plataforma_usa_la_empresa_solicitada() -> None:
    assert _empresa(_Plataforma(), "empresa-b") == "empresa-b"


def test_tenant_resuelve_su_propia_empresa() -> None:
    assert _empresa(_Tenant(), None) == "empresa-a"
    assert _empresa(_Tenant(), "empresa-a") == "empresa-a"


def test_tenant_no_puede_operar_sobre_otra_empresa() -> None:
    with pytest.raises(HTTPException) as exc:
        _empresa(_Tenant(), "empresa-b")
    assert exc.value.status_code == 403
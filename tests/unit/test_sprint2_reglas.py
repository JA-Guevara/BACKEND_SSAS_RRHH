"""Reglas del Sprint 2 verificables sin base de datos (T2-21).

Caso 1: el puntaje manual está entre 0 y 100.
Caso 3: la transacción por petición confirma o revierte completa.
Caso 4: el banco de talento (postulantes) no sale de la empresa del token.
"""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from ssas.config.settings import settings
from ssas.core.security.dependencies import CurrentUser
from ssas.core.security.jwt import JWTService
from ssas.infrastructure.database import session as db_session
from ssas.infrastructure.database.session import get_session
from ssas.main import app
from ssas.postulaciones.infrastructure.http.tablero_router import PuntajeRequest
from ssas.postulaciones.infrastructure.http.tablero_router import router as tablero_router
from ssas.postulantes.infrastructure.http.router import _empresa

RUTA_PUNTAJE = "/postulaciones/{postulacion_id}/puntaje"


@pytest.fixture(autouse=True)
def secure_test_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_secret_key", "unit-test-secret-key-with-at-least-32-bytes")


# --- Caso 1 · Puntaje 0–100 ---------------------------------------------------


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(0, Decimal("0")), (100, Decimal("100")), (85.5, Decimal("85.5")), ("50", Decimal("50"))],
)
def test_puntaje_acepta_valores_dentro_del_rango(valor, esperado) -> None:
    assert PuntajeRequest(puntaje=valor).puntaje == esperado


@pytest.mark.parametrize("valor", [-1, 100.01, "abc", None])
def test_puntaje_rechaza_valores_fuera_del_rango_o_invalidos(valor) -> None:
    with pytest.raises(ValidationError):
        PuntajeRequest(puntaje=valor)


def test_puntaje_es_obligatorio() -> None:
    with pytest.raises(ValidationError):
        PuntajeRequest.model_validate({})


class _SesionNoUsada:
    """Falla si el endpoint llega a tocar la base: el 422 debe ocurrir antes."""

    def __getattr__(self, nombre):
        raise AssertionError(f"La sesión no debía usarse (se llamó a {nombre})")


def _dependencia_de_usuario(path: str, method: str):
    """Devuelve la dependencia de permisos que FastAPI resolvió para el parámetro ``user``.

    ``require_scoped_permission`` crea una función nueva en cada llamada, así que solo
    se puede sobrescribir buscando la instancia registrada en la ruta del módulo.
    """
    for route in tablero_router.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            for dependency in route.dependant.dependencies:
                if dependency.name == "user":
                    return dependency.call
    raise AssertionError(f"No se encontró la ruta {method} {path}")


@pytest.mark.asyncio
@pytest.mark.parametrize("valor", [-1, 100.01, "abc"])
async def test_patch_puntaje_fuera_de_rango_responde_422(valor) -> None:
    usuario = CurrentUser(id="usuario-a", empresa_id="empresa-a", roles=["RECLUTADOR"])

    async def sesion_falsa():
        yield _SesionNoUsada()

    app.dependency_overrides[_dependencia_de_usuario(RUTA_PUNTAJE, "PATCH")] = lambda: usuario
    app.dependency_overrides[get_session] = sesion_falsa
    # El middleware de empresa valida el JWT antes de llegar a las dependencias.
    token = JWTService().create_access_token(usuario.id, usuario.empresa_id, usuario.roles)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                "/api/v1/postulaciones/postulacion-1/puntaje",
                json={"puntaje": valor},
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "puntaje"]


# --- Caso 3 · Atomicidad de la transacción por petición ------------------------


class _SesionRegistradora:
    def __init__(self, falla_commit: bool = False) -> None:
        self.llamadas: list[str] = []
        self.falla_commit = falla_commit

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info) -> None:
        self.llamadas.append("close")

    async def commit(self) -> None:
        self.llamadas.append("commit")
        if self.falla_commit:
            raise RuntimeError("commit rechazado por la base")

    async def rollback(self) -> None:
        self.llamadas.append("rollback")


def _usar_sesion(monkeypatch, sesion: _SesionRegistradora) -> None:
    monkeypatch.setattr(db_session, "AsyncSessionLocal", lambda: sesion)


@pytest.mark.asyncio
async def test_get_session_confirma_cuando_la_peticion_termina_bien(monkeypatch) -> None:
    sesion = _SesionRegistradora()
    _usar_sesion(monkeypatch, sesion)

    dependencia = get_session()
    assert await dependencia.__anext__() is sesion
    with pytest.raises(StopAsyncIteration):
        await dependencia.__anext__()

    assert sesion.llamadas == ["commit", "close"]


@pytest.mark.asyncio
async def test_get_session_revierte_sin_confirmar_ante_una_excepcion(monkeypatch) -> None:
    sesion = _SesionRegistradora()
    _usar_sesion(monkeypatch, sesion)

    dependencia = get_session()
    await dependencia.__anext__()
    with pytest.raises(RuntimeError, match="bitácora caída"):
        await dependencia.athrow(RuntimeError("bitácora caída"))

    assert sesion.llamadas == ["rollback", "close"]
    assert "commit" not in sesion.llamadas


@pytest.mark.asyncio
async def test_get_session_revierte_si_falla_el_commit(monkeypatch) -> None:
    sesion = _SesionRegistradora(falla_commit=True)
    _usar_sesion(monkeypatch, sesion)

    dependencia = get_session()
    await dependencia.__anext__()
    with pytest.raises(RuntimeError, match="commit rechazado"):
        await dependencia.__anext__()

    assert sesion.llamadas == ["commit", "rollback", "close"]


# --- Caso 4 · Aislamiento por empresa en postulantes ---------------------------


_PLATAFORMA = CurrentUser(id="admin-plataforma", empresa_id=None)
_EMPRESA_A = CurrentUser(id="usuario-a", empresa_id="empresa-a")


def test_postulantes_tenant_no_puede_operar_sobre_otra_empresa() -> None:
    with pytest.raises(HTTPException) as exc:
        _empresa(_EMPRESA_A, "empresa-b")
    assert exc.value.status_code == 403
    assert exc.value.detail == "No puedes operar sobre otra empresa"


def test_postulantes_plataforma_sin_empresa_devuelve_422() -> None:
    with pytest.raises(HTTPException) as exc:
        _empresa(_PLATAFORMA, None)
    assert exc.value.status_code == 422
    assert exc.value.detail == "Debe indicar empresa_id"


def test_postulantes_tenant_sin_empresa_usa_la_del_token() -> None:
    assert _empresa(_EMPRESA_A, None) == "empresa-a"
    assert _empresa(_EMPRESA_A, "empresa-a") == "empresa-a"


def test_postulantes_tenant_sin_empresa_asignada_devuelve_403() -> None:
    class _SinEmpresa:
        es_plataforma = False
        empresa_id = None

    with pytest.raises(HTTPException) as exc:
        _empresa(_SinEmpresa(), None)
    assert exc.value.status_code == 403

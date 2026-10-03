"""Reglas del Sprint 2 contra PostgreSQL real (T2-21).

Cada prueba corre dentro de una transacción externa que se revierte al final: no deja
datos en la base. ``AsyncSessionLocal`` se reemplaza por sesiones unidas a esa
conexión con ``join_transaction_mode="create_savepoint"``, de modo que el
``get_session`` real sigue haciendo su commit/rollback (sobre un savepoint).
"""

import os
from decimal import Decimal
from secrets import token_hex
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DATABASE_TESTS") != "1" or os.getenv("APP_ENV") != "test",
    reason="Pruebas de base real: requieren RUN_DATABASE_TESTS=1 y APP_ENV=test",
)

PASSWORD = "Qa.Integration!48276"


@pytest_asyncio.fixture
async def sesiones(monkeypatch):
    from ssas.config.settings import settings
    from ssas.infrastructure.database import session as db_session

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    monkeypatch.setattr(db_session, "AsyncSessionLocal", factory)
    try:
        yield factory
    finally:
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client():
    from ssas.main import app

    # raise_app_exceptions=False: un error no controlado llega como 500, igual que en producción.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def _crear_empresa_con_postulacion(factory) -> dict[str, str]:
    """Aprovisiona una empresa completa (roles, etapas, módulos) con una postulación."""
    from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
    from ssas.core.security.jwt import JWTService
    from ssas.departamentos.infrastructure.persistence.models.departamento import (
        DepartamentoModel,
    )
    from ssas.platform.application.use_cases.provision_empresa import ProvisionEmpresa
    from ssas.platform.infrastructure.http.schemas import ProvisionEmpresaRequest
    from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
        EtapaReclutamientoModel,
    )
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
    from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
    from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel

    marker = uuid4().hex[:10]
    slug = f"qa-t221-{marker}"
    async with factory() as session:
        empresa, admin, _ = await ProvisionEmpresa(session).execute(
            ProvisionEmpresaRequest.model_validate(
                {
                    "empresa": {"razon_social": slug, "nombre_comercial": slug, "slug": slug},
                    "administrador": {
                        "nombre": "Admin",
                        "apellido": "QA",
                        "email": f"{slug}@example.com",
                        "username": slug,
                        "password": PASSWORD,
                    },
                }
            )
        )
        departamento = DepartamentoModel(empresa_id=empresa.id, nombre="RRHH QA")
        session.add(departamento)
        await session.flush()
        cargo = CargoModel(
            empresa_id=empresa.id, departamento_id=departamento.id, nombre="Analista QA"
        )
        session.add(cargo)
        await session.flush()
        vacante = VacanteModel(
            empresa_id=empresa.id,
            cargo_id=cargo.id,
            departamento_id=departamento.id,
            responsable_id=admin.id,
            titulo="Analista QA",
            descripcion="Vacante de prueba T2-21",
            modalidad="PRESENCIAL",
            estado="PUBLICADA",
        )
        postulante = PostulanteModel(
            empresa_id=empresa.id,
            nombres="Candidato",
            apellidos=marker,
            ci=marker,
            email=f"candidato-{marker}@example.com",
            telefono="70000000",
            ciudad="Santa Cruz",
            nivel_educativo="LICENCIATURA",
            fuente="OTRO",
            en_banco_talento=True,
        )
        session.add_all([vacante, postulante])
        await session.flush()
        etapas = {
            etapa.nombre: etapa
            for etapa in (
                await session.scalars(
                    select(EtapaReclutamientoModel).where(
                        EtapaReclutamientoModel.empresa_id == empresa.id
                    )
                )
            ).all()
        }
        inicial = next(etapa for etapa in etapas.values() if etapa.es_inicial)
        contratado = next(etapa for etapa in etapas.values() if etapa.es_contratado)
        postulacion = PostulacionModel(
            vacante_id=vacante.id,
            postulante_id=postulante.id,
            etapa_id=inicial.id,
            codigo_seguimiento=f"POST-{token_hex(4).upper()}",
        )
        session.add(postulacion)
        await session.commit()

        return {
            "empresa_id": empresa.id,
            "postulante_id": postulante.id,
            "postulacion_id": postulacion.id,
            "etapa_inicial_id": inicial.id,
            "etapa_contratado_id": contratado.id,
            "token": JWTService().create_access_token(admin.id, empresa.id, ["ADMIN_EMPRESA"]),
        }


async def _postulacion(factory, postulacion_id: str):
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel

    async with factory() as session:
        return await session.scalar(
            select(PostulacionModel).where(PostulacionModel.id == postulacion_id)
        )


def _auth(datos: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {datos['token']}"}


# --- Caso 1 · Puntaje 0–100 ---------------------------------------------------


@pytest.mark.asyncio
async def test_puntaje_80_se_guarda(sesiones, client) -> None:
    datos = await _crear_empresa_con_postulacion(sesiones)

    response = await client.patch(
        f"/api/v1/postulaciones/{datos['postulacion_id']}/puntaje",
        json={"puntaje": 80},
        headers=_auth(datos),
    )

    assert response.status_code == 200, response.text
    assert Decimal(str(response.json()["puntaje_manual"])) == Decimal("80")
    guardada = await _postulacion(sesiones, datos["postulacion_id"])
    assert guardada.puntaje_manual == Decimal("80.00")


@pytest.mark.asyncio
async def test_puntaje_con_tres_decimales_se_redondea_a_100(sesiones, client) -> None:
    datos = await _crear_empresa_con_postulacion(sesiones)

    response = await client.patch(
        f"/api/v1/postulaciones/{datos['postulacion_id']}/puntaje",
        json={"puntaje": 99.999},
        headers=_auth(datos),
    )

    assert response.status_code == 200, response.text
    guardada = await _postulacion(sesiones, datos["postulacion_id"])
    assert guardada.puntaje_manual == Decimal("100.00")


@pytest.mark.asyncio
async def test_check_de_bd_rechaza_puntaje_150(sesiones) -> None:
    from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel

    datos = await _crear_empresa_con_postulacion(sesiones)

    async with sesiones() as session:
        with pytest.raises(IntegrityError) as exc:
            await session.execute(
                update(PostulacionModel)
                .where(PostulacionModel.id == datos["postulacion_id"])
                .values(puntaje_manual=150)
            )
        assert "ck_postulacion_puntaje_manual" in str(exc.value)


# --- Caso 3 · Atomicidad al mover a la etapa "Contratado" ----------------------


@pytest.mark.asyncio
async def test_error_en_bitacora_revierte_el_cambio_a_contratado(
    sesiones, client, monkeypatch
) -> None:
    from ssas.bitacora.application.events.postulacion_events import PostulacionEvents

    datos = await _crear_empresa_con_postulacion(sesiones)
    antes = await _postulacion(sesiones, datos["postulacion_id"])

    async def bitacora_caida(self, **context):
        raise RuntimeError("bitácora caída")

    monkeypatch.setattr(PostulacionEvents, "etapa_cambiada", bitacora_caida)

    response = await client.patch(
        f"/api/v1/postulaciones/{datos['postulacion_id']}/etapa",
        json={"etapa_id": datos["etapa_contratado_id"]},
        headers=_auth(datos),
    )

    assert response.status_code == 500
    despues = await _postulacion(sesiones, datos["postulacion_id"])
    assert despues.etapa_id == datos["etapa_inicial_id"]
    assert despues.fecha_ultimo_cambio == antes.fecha_ultimo_cambio
    assert despues.estado == "ACTIVA"


@pytest.mark.asyncio
async def test_mover_a_contratado_confirma_la_etapa(sesiones, client) -> None:
    datos = await _crear_empresa_con_postulacion(sesiones)

    response = await client.patch(
        f"/api/v1/postulaciones/{datos['postulacion_id']}/etapa",
        json={"etapa_id": datos["etapa_contratado_id"]},
        headers=_auth(datos),
    )

    assert response.status_code == 200, response.text
    despues = await _postulacion(sesiones, datos["postulacion_id"])
    assert despues.etapa_id == datos["etapa_contratado_id"]


@pytest.mark.xfail(
    reason=(
        "HALLAZGO: PATCH /postulaciones/{id}/etapa a la etapa es_contratado=true solo cambia "
        "etapa_id; el estado sigue en ACTIVA (rechazar sí pone DESCARTADA)."
    ),
    strict=True,
)
@pytest.mark.asyncio
async def test_mover_a_contratado_marca_estado_contratada(sesiones, client) -> None:
    datos = await _crear_empresa_con_postulacion(sesiones)

    response = await client.patch(
        f"/api/v1/postulaciones/{datos['postulacion_id']}/etapa",
        json={"etapa_id": datos["etapa_contratado_id"]},
        headers=_auth(datos),
    )

    assert response.status_code == 200, response.text
    assert response.json()["estado"] == "CONTRATADA"


# --- Caso 4 · Banco de talento aislado por empresa -----------------------------


@pytest.mark.asyncio
async def test_listado_de_postulantes_solo_trae_los_de_la_empresa(sesiones, client) -> None:
    a = await _crear_empresa_con_postulacion(sesiones)
    b = await _crear_empresa_con_postulacion(sesiones)

    response = await client.get("/api/v1/postulantes", headers=_auth(a))

    assert response.status_code == 200, response.text
    ids = {postulante["id"] for postulante in response.json()}
    assert ids == {a["postulante_id"]}
    assert b["postulante_id"] not in ids
    assert {postulante["empresa_id"] for postulante in response.json()} == {a["empresa_id"]}


@pytest.mark.asyncio
async def test_postulante_de_otra_empresa_devuelve_404(sesiones, client) -> None:
    a = await _crear_empresa_con_postulacion(sesiones)
    b = await _crear_empresa_con_postulacion(sesiones)

    response = await client.get(f"/api/v1/postulantes/{b['postulante_id']}", headers=_auth(a))

    assert response.status_code == 404
    assert response.json() == {"detail": "Postulante no encontrado"}


@pytest.mark.asyncio
async def test_listar_postulantes_de_otra_empresa_por_query_devuelve_403(
    sesiones, client
) -> None:
    a = await _crear_empresa_con_postulacion(sesiones)
    b = await _crear_empresa_con_postulacion(sesiones)

    response = await client.get(
        f"/api/v1/postulantes?empresa_id={b['empresa_id']}", headers=_auth(a)
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "No puedes operar sobre otra empresa"}


@pytest.mark.asyncio
async def test_puntaje_de_postulacion_de_otra_empresa_devuelve_404(sesiones, client) -> None:
    a = await _crear_empresa_con_postulacion(sesiones)
    b = await _crear_empresa_con_postulacion(sesiones)

    response = await client.patch(
        f"/api/v1/postulaciones/{b['postulacion_id']}/puntaje",
        json={"puntaje": 90},
        headers=_auth(a),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Postulacion no encontrada"}
    intacta = await _postulacion(sesiones, b["postulacion_id"])
    assert intacta.puntaje_manual is None

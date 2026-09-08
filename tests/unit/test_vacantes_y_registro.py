from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from ssas.main import app
from ssas.vacantes.application.use_cases.gestionar_vacantes import GestionarVacantes
from ssas.vacantes.domain.entities.vacante import Vacante, VacanteHabilidadInfo
from ssas.vacantes.domain.exceptions import VacanteInvalidStateError, VacanteReferenceError
from ssas.vacantes.infrastructure.http.schemas import (
    EmpresaPublicaResponse,
    HabilidadVacanteResponse,
    VacanteResponse,
)


def _fake_vacante(estado: str = "BORRADOR", vacante_id: str = "vac-1", empresa_id: str = "emp-1"):
    now = datetime.now(UTC)
    return Vacante(
        id=vacante_id,
        empresa_id=empresa_id,
        cargo_id="cargo-1",
        departamento_id="dept-1",
        responsable_id="user-1",
        titulo="Desarrollador Backend Senior",
        descripcion="Buscamos backend developer con experiencia en FastAPI",
        requisitos="Python, PostgreSQL",
        beneficios="Remoto 100%",
        cantidad_vacantes=2,
        salario_min=Decimal("3000.00"),
        salario_max=Decimal("5000.00"),
        mostrar_salario=True,
        modalidad="REMOTO",
        ubicacion="Santa Cruz, Bolivia",
        experiencia_min=3,
        fecha_publicacion=now if estado != "BORRADOR" else None,
        fecha_cierre=None,
        estado=estado,
        fecha_registro=now,
        created_at=now,
        updated_at=now,
        cargo_nombre="Desarrollador Backend",
        departamento_nombre="Tecnología",
        habilidades=[
            VacanteHabilidadInfo(
                habilidad_id="hab-1",
                nombre="Python",
                nivel_requerido="AVANZADO",
                es_obligatorio=True,
                peso=Decimal("2.0"),
            )
        ],
    )


@pytest.mark.asyncio
async def test_gestionar_vacantes_valida_habilidades_pertenecientes_a_empresa():
    repo = AsyncMock()
    repo.references_belong_to_empresa.return_value = True
    repo.skills_belong_to_empresa.return_value = False

    use_case = GestionarVacantes(repo)
    with pytest.raises(VacanteReferenceError):
        await use_case.crear(
            empresa_id="emp-1",
            responsable_id="user-1",
            values={
                "cargo_id": "cargo-1",
                "departamento_id": "dept-1",
                "habilidades": [{"habilidad_id": "hab-ajena", "nivel_requerido": "AVANZADO"}],
            },
        )


@pytest.mark.asyncio
async def test_gestionar_vacantes_ciclo_de_estados():
    repo = AsyncMock()
    repo.get_by_id.side_effect = [
        _fake_vacante(estado="BORRADOR"),
        _fake_vacante(estado="PUBLICADA"),
        _fake_vacante(estado="PAUSADA"),
        _fake_vacante(estado="PUBLICADA"),
    ]
    repo.publish.return_value = _fake_vacante(estado="PUBLICADA")
    repo.cambiar_estado.side_effect = lambda _vid, _eid, est: _fake_vacante(estado=est)

    use_case = GestionarVacantes(repo)

    # 1. BORRADOR -> PUBLICADA
    pub = await use_case.publicar("vac-1", "emp-1")
    assert pub.estado == "PUBLICADA"

    # 2. PUBLICADA -> PAUSADA
    pau = await use_case.pausar("vac-1", "emp-1")
    assert pau.estado == "PAUSADA"

    # 3. PAUSADA -> PUBLICADA (reanudar)
    rea = await use_case.reanudar("vac-1", "emp-1")
    assert rea.estado == "PUBLICADA"

    # 4. PUBLICADA -> CERRADA
    cer = await use_case.cerrar("vac-1", "emp-1")
    assert cer.estado == "CERRADA"


@pytest.mark.asyncio
async def test_gestionar_vacantes_rechaza_transiciones_invalidas():
    repo = AsyncMock()
    repo.get_by_id.return_value = _fake_vacante(estado="CERRADA")
    use_case = GestionarVacantes(repo)

    with pytest.raises(VacanteInvalidStateError):
        await use_case.publicar("vac-1", "emp-1")

    with pytest.raises(VacanteInvalidStateError):
        await use_case.pausar("vac-1", "emp-1")

    with pytest.raises(VacanteInvalidStateError):
        await use_case.reanudar("vac-1", "emp-1")


def test_openapi_exposes_new_endpoints_with_descriptions():
    paths = app.openapi()["paths"]
    assert "/api/v1/auth/registro-empresa" in paths
    assert "/api/v1/vacantes/{vacante_id}/reanudar" in paths
    assert "/api/v1/publico/{empresa_slug}" in paths


def test_schemas_serialize_skills_and_names():
    now = datetime.now(UTC)
    resp = VacanteResponse(
        id="vac-1",
        empresa_id="emp-1",
        cargo_id="cargo-1",
        departamento_id="dept-1",
        responsable_id="user-1",
        cargo_nombre="Desarrollador Backend",
        departamento_nombre="Tecnología",
        titulo="Backend Dev",
        descripcion="Python dev",
        requisitos=None,
        beneficios=None,
        cantidad_vacantes=1,
        salario_min=Decimal(3000),
        salario_max=Decimal(4000),
        mostrar_salario=True,
        modalidad="REMOTO",
        ubicacion=None,
        experiencia_min=2,
        fecha_publicacion=now,
        fecha_cierre=None,
        estado="PUBLICADA",
        fecha_registro=now,
        created_at=now,
        updated_at=now,
        habilidades=[
            HabilidadVacanteResponse(
                habilidad_id="hab-1",
                nombre="FastAPI",
                nivel_requerido="AVANZADO",
                es_obligatorio=True,
                peso=Decimal("1.0"),
            )
        ],
    )
    dumped = resp.model_dump()
    assert dumped["cargo_nombre"] == "Desarrollador Backend"
    assert dumped["departamento_nombre"] == "Tecnología"
    assert len(dumped["habilidades"]) == 1
    assert dumped["habilidades"][0]["nombre"] == "FastAPI"

    emp_resp = EmpresaPublicaResponse(
        id="emp-1",
        nombre="Acme Corp",
        slug="acme-corp",
        color_primario="#ff5500",
        portal_publico_activo=True,
    )
    assert emp_resp.color_primario == "#ff5500"
    assert emp_resp.portal_publico_activo is True


@pytest.mark.asyncio
async def test_crear_departamento_y_cargo_con_codigo():
    from ssas.cargos.application.use_cases.crear_cargo import CrearCargo
    from ssas.departamentos.application.use_cases.crear_departamento import CrearDepartamento

    dept_repo = AsyncMock()
    dept_repo.get_by_nombre.return_value = None
    dept_repo.create_departamento.return_value = {"id": "d1", "codigo": "TI-01"}

    use_case_dept = CrearDepartamento(dept_repo)
    await use_case_dept.execute(
        empresa_id="emp-1",
        nombre="Tecnología",
        codigo="ti-01",
    )
    dept_repo.create_departamento.assert_called_once_with(
        empresa_id="emp-1",
        nombre="Tecnología",
        descripcion=None,
        activo=True,
        codigo="ti-01",
        departamento_padre_id=None,
        responsable_id=None,
    )

    cargo_repo = AsyncMock()
    cargo_repo.get_by_nombre.return_value = None
    cargo_repo.departamento_exists.return_value = True
    cargo_repo.create_cargo.return_value = {"id": "c1", "codigo": "DEV-SR"}

    use_case_cargo = CrearCargo(cargo_repo)
    await use_case_cargo.execute(
        empresa_id="emp-1",
        nombre="Senior Dev",
        departamento_id="d1",
        codigo="dev-sr",
        nivel="Senior",
        salario_min=Decimal(4000),
        salario_max=Decimal(6000),
    )
    cargo_repo.create_cargo.assert_called_once_with(
        empresa_id="emp-1",
        nombre="Senior Dev",
        departamento_id="d1",
        descripcion=None,
        activo=True,
        codigo="dev-sr",
        nivel="Senior",
        salario_min=Decimal(4000),
        salario_max=Decimal(6000),
    )


@pytest.mark.asyncio
async def test_tenant_isolation_rejects_cross_tenant_references():
    repo = AsyncMock()
    # Cross tenant cargo/dept
    repo.references_belong_to_empresa.return_value = False
    use_case = GestionarVacantes(repo)

    with pytest.raises(VacanteReferenceError):
        await use_case.crear(
            empresa_id="empresa-a",
            responsable_id="admin-a",
            values={
                "cargo_id": "cargo-de-empresa-b",
                "departamento_id": "dept-de-empresa-b",
            },
        )



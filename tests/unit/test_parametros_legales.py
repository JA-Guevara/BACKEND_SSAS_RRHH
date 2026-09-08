from datetime import UTC, date

import pytest

from ssas.parametros_legales.application.use_cases.gestionar_parametros import (
    GestionarParametrosLegales,
)
from ssas.parametros_legales.domain.entities.parametro_legal import ParametroLegal
from ssas.parametros_legales.domain.exceptions import (
    ParametroLegalNotFoundError,
    ParametroLegalOverlapError,
    ParametroLegalPercentError,
    ParametroLegalRangeError,
)

pytestmark = pytest.mark.asyncio


class FakeParametroLegalRepository:
    def __init__(self):
        self.periodos: list[ParametroLegal] = []
        self._counter = 0

    async def list_by_empresa(self, empresa_id):
        return [p for p in self.periodos if p.empresa_id == empresa_id]

    async def get_by_id(self, periodo_id, empresa_id):
        return next(
            (p for p in self.periodos if p.id == periodo_id and p.empresa_id == empresa_id),
            None,
        )

    async def find_overlap(self, empresa_id, vigencia_desde, vigencia_hasta, exclude_id=None):
        for p in self.periodos:
            if p.empresa_id != empresa_id or p.id == exclude_id:
                continue
            if vigencia_desde <= p.vigencia_hasta and p.vigencia_desde <= vigencia_hasta:
                return p
        return None

    async def create(self, empresa_id, values):
        self._counter += 1
        periodo = ParametroLegal(
            id=f"pl-{self._counter}",
            empresa_id=empresa_id,
            vigencia_desde=values["vigencia_desde"],
            vigencia_hasta=values["vigencia_hasta"],
            afp=values.get("afp"),
            aporte_solidario=values.get("aporte_solidario"),
            rc_iva=values.get("rc_iva"),
            aguinaldo=values.get("aguinaldo"),
            prima=values.get("prima"),
            created_at=_ahora(),
            updated_at=_ahora(),
        )
        self.periodos.append(periodo)
        return periodo

    async def update(self, periodo_id, empresa_id, values):
        periodo = await self.get_by_id(periodo_id, empresa_id)
        if periodo is None:
            raise ParametroLegalNotFoundError("Periodo de parámetros no encontrado")
        campos = {
            "vigencia_desde": values.get("vigencia_desde", periodo.vigencia_desde),
            "vigencia_hasta": values.get("vigencia_hasta", periodo.vigencia_hasta),
            "afp": values.get("afp", periodo.afp),
            "aporte_solidario": values.get("aporte_solidario", periodo.aporte_solidario),
            "rc_iva": values.get("rc_iva", periodo.rc_iva),
            "aguinaldo": values.get("aguinaldo", periodo.aguinaldo),
            "prima": values.get("prima", periodo.prima),
        }
        nuevo = ParametroLegal(
            id=periodo.id,
            empresa_id=periodo.empresa_id,
            vigencia_desde=campos["vigencia_desde"],
            vigencia_hasta=campos["vigencia_hasta"],
            afp=campos["afp"],
            aporte_solidario=campos["aporte_solidario"],
            rc_iva=campos["rc_iva"],
            aguinaldo=campos["aguinaldo"],
            prima=campos["prima"],
            created_at=periodo.created_at,
            updated_at=_ahora(),
        )
        self.periodos = [
            nuevo if p.id == periodo.id else p for p in self.periodos
        ]
        return nuevo


def _ahora():
    from datetime import datetime

    return datetime.now(UTC)


def _payload(afp=None, **extra):
    return {"vigencia_desde": date(2026, 1, 1), "vigencia_hasta": date(2026, 12, 31), "afp": afp, **extra}


async def test_crear_periodo_valido() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)

    periodo = await service.crear("empresa-a", _payload(afp=12.75))

    assert periodo.empresa_id == "empresa-a"
    assert periodo.afp == 12.75
    assert periodo.vigente


async def test_no_permite_periodos_superpuestos() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)
    await service.crear("empresa-a", _payload(afp=12.75))

    with pytest.raises(ParametroLegalOverlapError):
        await service.crear(
            "empresa-a",
            {
                "vigencia_desde": date(2026, 6, 1),
                "vigencia_hasta": date(2027, 6, 30),
                "afp": 13,
            },
        )


async def test_si_permite_misma_empresa_periodos_adyacentes() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)
    await service.crear("empresa-a", _payload(afp=12.75))

    periodo = await service.crear(
        "empresa-a",
        {
            "vigencia_desde": date(2027, 1, 1),
            "vigencia_hasta": date(2027, 12, 31),
            "afp": 13,
        },
    )
    assert periodo.vigencia_desde == date(2027, 1, 1)


async def test_empresas_distintas_no_entran_en_solape() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)
    await service.crear("empresa-a", _payload(afp=12.75))

    periodo = await service.crear("empresa-b", _payload(afp=13.5))
    assert periodo.empresa_id == "empresa-b"


async def test_rango_invalido_rechazado() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)

    with pytest.raises(ParametroLegalRangeError):
        await service.crear(
            "empresa-a",
            {
                "vigencia_desde": date(2027, 1, 1),
                "vigencia_hasta": date(2026, 12, 31),
                "afp": 12,
            },
        )


async def test_porcentaje_fuera_de_rango_rechazado() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)

    with pytest.raises(ParametroLegalPercentError):
        await service.crear("empresa-a", _payload(afp=101))


async def test_actualizar_valida_solape_excluyendo_el_propio() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)
    creado = await service.crear("empresa-a", _payload(afp=12.75))
    await service.crear(
        "empresa-a",
        {
            "vigencia_desde": date(2024, 1, 1),
            "vigencia_hasta": date(2024, 12, 31),
            "afp": 11,
        },
    )

    actualizado = await service.actualizar(
        creado.id,
        "empresa-a",
        {"afp": 13.0, "vigencia_desde": date(2026, 1, 1), "vigencia_hasta": date(2027, 12, 31)},
    )
    assert actualizado.afp == 13.0

    with pytest.raises(ParametroLegalOverlapError):
        await service.actualizar(
            creado.id,
            "empresa-a",
            {
                "vigencia_desde": date(2024, 1, 1),
                "vigencia_hasta": date(2024, 12, 31),
            },
        )


async def test_actualizar_periodo_de_otra_empresa_rechazado() -> None:
    repository = FakeParametroLegalRepository()
    service = GestionarParametrosLegales(repository)
    creado = await service.crear("empresa-a", _payload())

    with pytest.raises(ParametroLegalNotFoundError):
        await service.actualizar(creado.id, "empresa-b", {"afp": 13})
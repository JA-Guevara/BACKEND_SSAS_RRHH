from dataclasses import MISSING

import pytest
from fastapi import HTTPException

from ssas.reportes.application.agregador import construir_sql
from ssas.reportes.domain.catalogo import CATALOGO, Fuente
from ssas.reportes.infrastructure.http.schemas_agregado import ConsultaAgregada


def test_toda_fuente_declara_tenant() -> None:
    campo = Fuente.__dataclass_fields__["columna_tenant"]
    assert campo.default is MISSING
    assert campo.default_factory is MISSING
    for code, fuente in CATALOGO.items():
        assert fuente.columna_tenant, f"{code} no declara columna de inquilino"


@pytest.mark.parametrize("fuente", sorted(CATALOGO))
def test_agregado_siempre_filtra_por_inquilino_primero(fuente: str) -> None:
    consulta = ConsultaAgregada(fuente=fuente, medidas=[{"agregacion": "conteo"}])

    sql, params, _ = construir_sql(consulta, "empresa-a")

    esperado = f"{CATALOGO[fuente].columna_tenant} = :empresa_id"
    assert esperado in sql
    assert sql.index(esperado) == sql.index("WHERE") + len("WHERE ")
    assert params["empresa_id"] == "empresa-a"


def test_agrupar_por_fecha_exige_granularidad() -> None:
    consulta = ConsultaAgregada(
        fuente="postulaciones",
        medidas=[{"agregacion": "conteo"}],
        agrupar_por=["fecha_postulacion"],
    )

    with pytest.raises(HTTPException) as error:
        construir_sql(consulta, "empresa-a")

    assert error.value.status_code == 422


def test_granularidad_no_se_concatena() -> None:
    consulta = ConsultaAgregada(
        fuente="postulaciones",
        medidas=[{"agregacion": "conteo"}],
        agrupar_por=["fecha_postulacion"],
        granularidad="semana",
    )

    sql, params, _ = construir_sql(consulta, "empresa-a")

    assert "semana" not in sql
    assert params["g0_gran"] == "week"


def test_medida_rechaza_campo_no_agregable() -> None:
    consulta = ConsultaAgregada(
        fuente="postulaciones",
        medidas=[{"agregacion": "suma", "campo": "estado"}],
    )

    with pytest.raises(HTTPException) as error:
        construir_sql(consulta, "empresa-a")

    assert error.value.status_code == 422


def test_orden_por_medida_usa_su_alias() -> None:
    consulta = ConsultaAgregada(
        fuente="analisis_cv",
        medidas=[{"agregacion": "promedio", "campo": "puntaje_afinidad"}],
        agrupar_por=["vacante"],
        orden=[{"campo": "puntaje_afinidad", "direccion": "desc"}],
    )

    sql, _, _ = construir_sql(consulta, "empresa-a")

    assert "ORDER BY m0 DESC" in sql
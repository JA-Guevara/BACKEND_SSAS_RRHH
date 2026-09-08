from decimal import Decimal

import pytest
from pydantic import ValidationError

from ssas.cargos.infrastructure.http.schemas import (
    ActualizarCargoRequest,
    CrearCargoRequest,
)


def test_crear_cargo_rechaza_salario_min_mayor_que_max() -> None:
    with pytest.raises(ValidationError):
        CrearCargoRequest(
            nombre="Analista",
            salario_min=Decimal(9000),
            salario_max=Decimal(4000),
        )


def test_crear_cargo_con_rango_valido() -> None:
    cargo = CrearCargoRequest(
        nombre="Analista",
        salario_min=Decimal(4000),
        salario_max=Decimal(9000),
    )
    assert cargo.activo is True
    assert cargo.salario_min == Decimal(4000)


def test_actualizar_cargo_rechaza_rango_invertido() -> None:
    with pytest.raises(ValidationError):
        ActualizarCargoRequest(
            salario_min=Decimal(100),
            salario_max=Decimal(50),
        )


def test_actualizar_cargo_acepta_solo_un_extremo() -> None:
    cargo = ActualizarCargoRequest(salario_min=Decimal(4000))
    assert cargo.salario_min == Decimal(4000)
    assert cargo.salario_max is None

    cargo = ActualizarCargoRequest(salario_max=Decimal(9000))
    assert cargo.salario_max == Decimal(9000)
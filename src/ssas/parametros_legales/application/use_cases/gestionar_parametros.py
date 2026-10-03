from datetime import date
from decimal import Decimal
from typing import Any

from ssas.parametros_legales.domain.entities.parametro_legal import ParametroLegal
from ssas.parametros_legales.domain.exceptions import (
    ParametroLegalNotFoundError,
    ParametroLegalOverlapError,
    ParametroLegalPercentError,
    ParametroLegalRangeError,
)
from ssas.parametros_legales.ports.outgoing.parametro_legal_repository import (
    ParametroLegalRepository,
)

PORCENTAJES = ("afp", "aporte_solidario", "rc_iva", "aguinaldo", "prima")


def _validar_rango(
    vigencia_desde: date, vigencia_hasta: date, **_: Any
) -> float:
    if vigencia_desde > vigencia_hasta:
        raise ParametroLegalRangeError(
            "La fecha de inicio no puede ser posterior a la fecha de fin"
        )
    return 0.0


def _validar_porcentajes(values: dict[str, Any]) -> None:
    for campo in PORCENTAJES:
        valor = values.get(campo)
        if valor is None:
            continue
        numero = Decimal(str(valor))
        if numero < 0 or numero > 100:
            raise ParametroLegalPercentError(
                f"{campo.replace('_', ' ').title()} debe estar entre 0 y 100"
            )


def _registro_valido(values: dict[str, Any]) -> None:
    _validar_rango(values["vigencia_desde"], values["vigencia_hasta"])
    _validar_porcentajes(values)


def _sobrepuestos(desde: date, hasta: date, inicio: date, fin: date) -> bool:
    return desde <= fin and inicio <= hasta


class GestionarParametrosLegales:
    def __init__(self, repository: ParametroLegalRepository) -> None:
        self.repository = repository

    async def listar(self, empresa_id: str) -> list[ParametroLegal]:
        return await self.repository.list_by_empresa(empresa_id)

    async def crear(self, empresa_id: str, values: dict[str, Any]) -> ParametroLegal:
        _registro_valido(values)
        registrado = await self.repository.find_overlap(
            empresa_id, values["vigencia_desde"], values["vigencia_hasta"]
        )
        if registrado is not None:
            raise ParametroLegalOverlapError(
                f"Ya existe un periodo vigente del {registrado.vigencia_desde} al "
                f"{registrado.vigencia_hasta}"
            )
        return await self.repository.create(empresa_id, values)

    async def actualizar(
        self, periodo_id: str, empresa_id: str, values: dict[str, Any]
    ) -> ParametroLegal:
        actual = await self.repository.get_by_id(periodo_id, empresa_id)
        if actual is None:
            raise ParametroLegalNotFoundError("Periodo de parámetros no encontrado")

        combinados = {
            "vigencia_desde": values.get("vigencia_desde", actual.vigencia_desde),
            "vigencia_hasta": values.get("vigencia_hasta", actual.vigencia_hasta),
            **{campo: values.get(campo, getattr(actual, campo)) for campo in PORCENTAJES},
        }
        _registro_valido(combinados)

        if combinados["vigencia_desde"] != actual.vigencia_desde or (
            combinados["vigencia_hasta"] != actual.vigencia_hasta
        ):
            registrado = await self.repository.find_overlap(
                empresa_id,
                combinados["vigencia_desde"],
                combinados["vigencia_hasta"],
                exclude_id=periodo_id,
            )
            if registrado is not None:
                raise ParametroLegalOverlapError(
                    f"Ya existe un periodo vigente del {registrado.vigencia_desde} al "
                    f"{registrado.vigencia_hasta}"
                )

        return await self.repository.update(periodo_id, empresa_id, values)
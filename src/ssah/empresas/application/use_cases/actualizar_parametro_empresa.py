from datetime import date
from decimal import Decimal

from ssah.empresas.domain.entities.parametro import ParametroEmpresa
from ssah.empresas.domain.exceptions import (
    ParametroLegalNotFoundError,
    ParametroValorInvalidoError,
    ParametroVigenciaInvalidaError,
)
from ssah.empresas.ports.outgoing.parametro_repository import ParametroRepository


class ActualizarParametroEmpresa:
    def __init__(self, parametro_repository: ParametroRepository):
        self.parametro_repository = parametro_repository

    async def execute(
        self,
        empresa_id: str,
        codigo: str,
        valor: Decimal,
        vigente_desde: date,
        vigente_hasta: date | None = None,
        norma_legal: str | None = None,
    ) -> ParametroEmpresa:
        parametro_legal = await self.parametro_repository.get_parametro_legal_by_codigo(codigo)
        if parametro_legal is None:
            raise ParametroLegalNotFoundError("Parámetro legal no encontrado")
        if valor < 0:
            raise ParametroValorInvalidoError("El valor no puede ser negativo")
        if parametro_legal.tipo_valor == "porcentaje" and valor > Decimal("100"):
            raise ParametroValorInvalidoError("El porcentaje debe estar entre 0 y 100")
        if vigente_hasta is not None and vigente_hasta < vigente_desde:
            raise ParametroVigenciaInvalidaError(
                "La fecha vigente_hasta debe ser mayor o igual a vigente_desde"
            )

        return await self.parametro_repository.upsert_parametro_valor(
            empresa_id=empresa_id,
            codigo=codigo,
            valor=valor,
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            norma_legal=norma_legal.strip() if norma_legal else None,
        )
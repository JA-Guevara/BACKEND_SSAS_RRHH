from datetime import date
from decimal import Decimal
from typing import Protocol

from ssah.empresas.domain.entities.parametro import ParametroEmpresa


class ParametroRepository(Protocol):
    async def list_parametros_empresa(self, empresa_id: str) -> list[ParametroEmpresa]:
        ...

    async def get_parametro_legal_by_codigo(self, codigo: str) -> ParametroEmpresa | None:
        ...

    async def upsert_parametro_valor(
        self,
        empresa_id: str,
        codigo: str,
        valor: Decimal,
        vigente_desde: date,
        vigente_hasta: date | None,
        norma_legal: str | None,
    ) -> ParametroEmpresa:
        ...
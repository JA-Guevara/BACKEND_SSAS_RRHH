from datetime import date
from typing import Any, Protocol

from ssas.parametros_legales.domain.entities.parametro_legal import ParametroLegal


class ParametroLegalRepository(Protocol):
    async def list_by_empresa(self, empresa_id: str) -> list[ParametroLegal]: ...

    async def get_by_id(self, periodo_id: str, empresa_id: str) -> ParametroLegal | None: ...

    async def find_overlap(
        self,
        empresa_id: str,
        vigencia_desde: date,
        vigencia_hasta: date,
        exclude_id: str | None = None,
    ) -> ParametroLegal | None: ...

    async def create(self, empresa_id: str, values: dict[str, Any]) -> ParametroLegal: ...

    async def update(
        self, periodo_id: str, empresa_id: str, values: dict[str, Any]
    ) -> ParametroLegal: ...
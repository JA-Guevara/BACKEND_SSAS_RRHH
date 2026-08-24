from ssas.empresas.domain.entities.parametro import ParametroEmpresa
from ssas.empresas.ports.outgoing.parametro_repository import ParametroRepository


class ListarParametrosEmpresa:
    def __init__(self, parametro_repository: ParametroRepository):
        self.parametro_repository = parametro_repository

    async def execute(self, empresa_id: str) -> list[ParametroEmpresa]:
        return await self.parametro_repository.list_parametros_empresa(empresa_id)
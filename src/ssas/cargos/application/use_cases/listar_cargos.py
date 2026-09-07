from ssas.cargos.ports.outgoing.cargo_repository import CargoRepository


class ListarCargos:
    def __init__(self, repository: CargoRepository):
        self.repository = repository

    async def execute(
        self,
        empresa_id: str,
        activo: bool | None = None,
        departamento_id: str | None = None,
    ):
        return await self.repository.list_cargos(empresa_id, activo, departamento_id)

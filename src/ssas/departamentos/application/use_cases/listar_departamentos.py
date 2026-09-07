from ssas.departamentos.ports.outgoing.departamento_repository import DepartamentoRepository


class ListarDepartamentos:
    def __init__(self, repository: DepartamentoRepository):
        self.repository = repository

    async def execute(self, empresa_id: str, activo: bool | None = None):
        return await self.repository.list_departamentos(empresa_id, activo)

from ssas.departamentos.domain.exceptions import (
    DepartamentoInUseError,
    DepartamentoNotFoundError,
)
from ssas.departamentos.ports.outgoing.departamento_repository import DepartamentoRepository


class EliminarDepartamento:
    def __init__(self, repository: DepartamentoRepository):
        self.repository = repository

    async def execute(self, departamento_id: str, empresa_id: str) -> None:
        if not await self.repository.exists(departamento_id, empresa_id):
            raise DepartamentoNotFoundError("Departamento no encontrado")
        if await self.repository.has_dependencies(departamento_id, empresa_id):
            raise DepartamentoInUseError(
                "No se puede eliminar un departamento con cargos asociados"
            )
        await self.repository.delete_departamento(departamento_id, empresa_id)

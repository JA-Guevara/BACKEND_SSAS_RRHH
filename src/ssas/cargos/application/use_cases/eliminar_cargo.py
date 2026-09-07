from ssas.cargos.domain.exceptions import CargoInUseError, CargoNotFoundError
from ssas.cargos.ports.outgoing.cargo_repository import CargoRepository


class EliminarCargo:
    def __init__(self, repository: CargoRepository):
        self.repository = repository

    async def execute(self, cargo_id: str, empresa_id: str) -> None:
        if not await self.repository.exists(cargo_id, empresa_id):
            raise CargoNotFoundError("Cargo no encontrado")
        if await self.repository.has_dependencies(cargo_id, empresa_id):
            raise CargoInUseError("No se puede eliminar un cargo con dependencias")
        await self.repository.delete_cargo(cargo_id, empresa_id)

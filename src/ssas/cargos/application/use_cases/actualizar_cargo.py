from ssas.cargos.domain.exceptions import (
    CargoAlreadyExistsError,
    CargoNotFoundError,
    InvalidDepartamentoForCargoError,
)
from ssas.cargos.ports.outgoing.cargo_repository import CargoRepository


class ActualizarCargo:
    def __init__(self, repository: CargoRepository):
        self.repository = repository

    async def execute(self, cargo_id: str, empresa_id: str, values: dict):
        current = await self.repository.get_by_id(cargo_id, empresa_id)
        if current is None:
            raise CargoNotFoundError("Cargo no encontrado")
        if not values:
            return current
        if "nombre" in values and values["nombre"] is not None:
            values["nombre"] = values["nombre"].strip()
            existing = await self.repository.get_by_nombre(values["nombre"], empresa_id)
            if existing and existing.id != cargo_id:
                raise CargoAlreadyExistsError("Ya existe un cargo con ese nombre")
        if "departamento_id" in values and values["departamento_id"]:
            if not await self.repository.departamento_exists(values["departamento_id"], empresa_id):
                raise InvalidDepartamentoForCargoError("El departamento no existe en la empresa")
        if "descripcion" in values and values["descripcion"] is not None:
            values["descripcion"] = values["descripcion"].strip()
        return await self.repository.update_cargo(cargo_id, empresa_id, values)

from ssas.departamentos.domain.exceptions import (
    DepartamentoAlreadyExistsError,
    DepartamentoNotFoundError,
)
from ssas.departamentos.ports.outgoing.departamento_repository import DepartamentoRepository


class ActualizarDepartamento:
    def __init__(self, repository: DepartamentoRepository):
        self.repository = repository

    async def execute(self, departamento_id: str, empresa_id: str, values: dict):
        current = await self.repository.get_by_id(departamento_id, empresa_id)
        if current is None:
            raise DepartamentoNotFoundError("Departamento no encontrado")
        if not values:
            return current
        if "nombre" in values and values["nombre"] is not None:
            values["nombre"] = values["nombre"].strip()
            existing = await self.repository.get_by_nombre(values["nombre"], empresa_id)
            if existing and existing.id != departamento_id:
                raise DepartamentoAlreadyExistsError("Ya existe un departamento con ese nombre")
        if "descripcion" in values and values["descripcion"] is not None:
            values["descripcion"] = values["descripcion"].strip()
        return await self.repository.update_departamento(departamento_id, empresa_id, values)

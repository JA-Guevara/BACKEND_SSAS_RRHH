from ssas.cargos.domain.exceptions import (
    CargoAlreadyExistsError,
    InvalidDepartamentoForCargoError,
)
from ssas.cargos.ports.outgoing.cargo_repository import CargoRepository


class CrearCargo:
    def __init__(self, repository: CargoRepository):
        self.repository = repository

    async def execute(
        self,
        empresa_id: str,
        nombre: str,
        departamento_id: str | None = None,
        descripcion: str | None = None,
        activo: bool = True,
    ):
        normalized_nombre = nombre.strip()
        if await self.repository.get_by_nombre(normalized_nombre, empresa_id):
            raise CargoAlreadyExistsError("Ya existe un cargo con ese nombre")
        if departamento_id and not await self.repository.departamento_exists(
            departamento_id, empresa_id
        ):
            raise InvalidDepartamentoForCargoError("El departamento no existe en la empresa")
        return await self.repository.create_cargo(
            empresa_id=empresa_id,
            nombre=normalized_nombre,
            departamento_id=departamento_id,
            descripcion=descripcion.strip() if descripcion else None,
            activo=activo,
        )

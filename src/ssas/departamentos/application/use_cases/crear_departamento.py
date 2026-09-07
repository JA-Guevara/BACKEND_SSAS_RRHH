from ssas.departamentos.domain.exceptions import DepartamentoAlreadyExistsError
from ssas.departamentos.ports.outgoing.departamento_repository import DepartamentoRepository


class CrearDepartamento:
    def __init__(self, repository: DepartamentoRepository):
        self.repository = repository

    async def execute(
        self,
        empresa_id: str,
        nombre: str,
        descripcion: str | None = None,
        activo: bool = True,
    ):
        normalized_nombre = nombre.strip()
        if await self.repository.get_by_nombre(normalized_nombre, empresa_id):
            raise DepartamentoAlreadyExistsError("Ya existe un departamento con ese nombre")
        return await self.repository.create_departamento(
            empresa_id=empresa_id,
            nombre=normalized_nombre,
            descripcion=descripcion.strip() if descripcion else None,
            activo=activo,
        )

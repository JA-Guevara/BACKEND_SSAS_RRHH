from abc import ABC, abstractmethod

from ssas.departamentos.domain.entities.departamento import Departamento


class DepartamentoRepository(ABC):
    @abstractmethod
    async def list_departamentos(
        self, empresa_id: str, activo: bool | None = None
    ) -> list[Departamento]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, departamento_id: str, empresa_id: str) -> Departamento | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_nombre(self, nombre: str, empresa_id: str) -> Departamento | None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, departamento_id: str, empresa_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def has_dependencies(self, departamento_id: str, empresa_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create_departamento(
        self,
        empresa_id: str,
        nombre: str,
        descripcion: str | None,
        activo: bool,
    ) -> Departamento:
        raise NotImplementedError

    @abstractmethod
    async def update_departamento(
        self, departamento_id: str, empresa_id: str, values: dict
    ) -> Departamento:
        raise NotImplementedError

    @abstractmethod
    async def delete_departamento(self, departamento_id: str, empresa_id: str) -> None:
        raise NotImplementedError

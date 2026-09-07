from abc import ABC, abstractmethod

from ssas.cargos.domain.entities.cargo import Cargo


class CargoRepository(ABC):
    @abstractmethod
    async def list_cargos(
        self,
        empresa_id: str,
        activo: bool | None = None,
        departamento_id: str | None = None,
    ) -> list[Cargo]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, cargo_id: str, empresa_id: str) -> Cargo | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_nombre(self, nombre: str, empresa_id: str) -> Cargo | None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, cargo_id: str, empresa_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def departamento_exists(self, departamento_id: str, empresa_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def has_dependencies(self, cargo_id: str, empresa_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def create_cargo(
        self,
        empresa_id: str,
        nombre: str,
        departamento_id: str | None,
        descripcion: str | None,
        activo: bool,
    ) -> Cargo:
        raise NotImplementedError

    @abstractmethod
    async def update_cargo(self, cargo_id: str, empresa_id: str, values: dict) -> Cargo:
        raise NotImplementedError

    @abstractmethod
    async def delete_cargo(self, cargo_id: str, empresa_id: str) -> None:
        raise NotImplementedError

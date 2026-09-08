from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ssas.vacantes.domain.entities.vacante import Vacante
from ssas.vacantes.domain.entities.vacante_publica import VacantePublica


class VacanteRepository(ABC):
    @abstractmethod
    async def list_by_empresa(self, empresa_id: str, estado: str | None = None) -> list[Vacante]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, vacante_id: str, empresa_id: str) -> Vacante | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, empresa_id: str, responsable_id: str, values: dict[str, Any]) -> Vacante:
        raise NotImplementedError

    @abstractmethod
    async def update(self, vacante_id: str, empresa_id: str, values: dict[str, Any]) -> Vacante:
        raise NotImplementedError

    @abstractmethod
    async def publish(self, vacante_id: str, empresa_id: str, fecha_publicacion: datetime) -> Vacante:
        raise NotImplementedError

    @abstractmethod
    async def cambiar_estado(self, vacante_id: str, empresa_id: str, estado: str) -> Vacante:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, vacante_id: str, empresa_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def references_belong_to_empresa(
        self, empresa_id: str, cargo_id: str, departamento_id: str, responsable_id: str
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def skills_belong_to_empresa(self, empresa_id: str, habilidad_ids: list[str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_publicadas(
        self, empresa_slug: str, ubicacion: str | None, modalidad: str | None
    ) -> list[VacantePublica]:
        raise NotImplementedError

    @abstractmethod
    async def get_publicada(self, empresa_slug: str, vacante_id: str) -> VacantePublica | None:
        raise NotImplementedError


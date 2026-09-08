from datetime import UTC, datetime
from typing import Any

from ssas.vacantes.domain.entities.vacante import Vacante
from ssas.vacantes.domain.entities.vacante_publica import VacantePublica
from ssas.vacantes.domain.exceptions import (
    VacanteInvalidStateError,
    VacanteNotFoundError,
    VacanteReferenceError,
)
from ssas.vacantes.ports.outgoing.vacante_repository import VacanteRepository

ESTADOS_CERRABLES = ("PUBLICADA", "PAUSADA")


class GestionarVacantes:
    def __init__(self, repository: VacanteRepository) -> None:
        self.repository = repository

    async def listar(self, empresa_id: str, estado: str | None = None) -> list[Vacante]:
        return await self.repository.list_by_empresa(empresa_id, estado)

    async def obtener(self, vacante_id: str, empresa_id: str) -> Vacante:
        vacante = await self.repository.get_by_id(vacante_id, empresa_id)
        if vacante is None:
            raise VacanteNotFoundError("Vacante no encontrada")
        return vacante

    async def crear(
        self, empresa_id: str, responsable_id: str, values: dict[str, Any]
    ) -> Vacante:
        if not await self.repository.references_belong_to_empresa(
            empresa_id, values["cargo_id"], values["departamento_id"], responsable_id
        ):
            raise VacanteReferenceError("Cargo, departamento o responsable no pertenece a la empresa")
        return await self.repository.create(empresa_id, responsable_id, values)

    async def actualizar(
        self, vacante_id: str, empresa_id: str, values: dict[str, Any]
    ) -> Vacante:
        current = await self.obtener(vacante_id, empresa_id)
        if current.estado != "BORRADOR":
            raise VacanteInvalidStateError("Solo se pueden editar vacantes en borrador")
        references = {
            "cargo_id": values.get("cargo_id", current.cargo_id),
            "departamento_id": values.get("departamento_id", current.departamento_id),
            "responsable_id": values.get("responsable_id", current.responsable_id),
        }
        if not await self.repository.references_belong_to_empresa(empresa_id, **references):
            raise VacanteReferenceError("Cargo, departamento o responsable no pertenece a la empresa")
        return await self.repository.update(vacante_id, empresa_id, values)

    async def publicar(self, vacante_id: str, empresa_id: str) -> Vacante:
        current = await self.obtener(vacante_id, empresa_id)
        if current.estado != "BORRADOR":
            raise VacanteInvalidStateError("Solo se pueden publicar vacantes en borrador")
        if current.fecha_cierre and current.fecha_cierre < datetime.now(UTC):
            raise VacanteInvalidStateError("La fecha de cierre ya vencio")
        return await self.repository.publish(vacante_id, empresa_id, datetime.now(UTC))

    async def pausar(self, vacante_id: str, empresa_id: str) -> Vacante:
        """Retira temporalmente del portal una vacante publicada.

        Solo PUBLICADA -> PAUSADA: pausar un borrador o una vacante cerrada no
        significa nada y dejaría el tablero con estados imposibles.
        """
        current = await self.obtener(vacante_id, empresa_id)
        if current.estado != "PUBLICADA":
            raise VacanteInvalidStateError(
                f"Solo se pueden pausar vacantes publicadas; la vacante está en {current.estado}"
            )
        return await self.repository.cambiar_estado(vacante_id, empresa_id, "PAUSADA")

    async def cerrar(self, vacante_id: str, empresa_id: str) -> Vacante:
        """Cierra el proceso de una vacante publicada o pausada."""
        current = await self.obtener(vacante_id, empresa_id)
        if current.estado not in ESTADOS_CERRABLES:
            raise VacanteInvalidStateError(
                "Solo se pueden cerrar vacantes publicadas o pausadas; la vacante está en "
                f"{current.estado}"
            )
        return await self.repository.cambiar_estado(vacante_id, empresa_id, "CERRADA")

    async def eliminar(self, vacante_id: str, empresa_id: str) -> None:
        current = await self.obtener(vacante_id, empresa_id)
        if current.estado == "PUBLICADA":
            raise VacanteInvalidStateError("No se puede eliminar una vacante publicada")
        await self.repository.delete(vacante_id, empresa_id)

    async def listar_publicas(
        self, empresa_slug: str, ubicacion: str | None, modalidad: str | None
    ) -> list[VacantePublica]:
        return await self.repository.list_publicadas(empresa_slug, ubicacion, modalidad)

    async def obtener_publica(self, empresa_slug: str, vacante_id: str) -> VacantePublica:
        vacante = await self.repository.get_publicada(empresa_slug, vacante_id)
        if vacante is None:
            raise VacanteNotFoundError("Vacante no encontrada")
        return vacante

from ssas.postulaciones.domain.entities.postulacion_publica import PostulacionSeguimiento
from ssas.postulaciones.domain.exceptions import PostulacionNotFoundError
from ssas.postulaciones.ports.outgoing.postulacion_publica_repository import (
    PostulacionPublicaRepository,
)


class ConsultarPostulacionPublica:
    def __init__(self, repository: PostulacionPublicaRepository) -> None:
        self.repository = repository

    async def execute(self, codigo_seguimiento: str) -> PostulacionSeguimiento:
        seguimiento = await self.repository.get_by_codigo(codigo_seguimiento.strip().upper())
        if seguimiento is None:
            raise PostulacionNotFoundError("No existe una postulacion con ese codigo")
        return seguimiento

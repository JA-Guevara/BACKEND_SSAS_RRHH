from abc import ABC, abstractmethod

from ssas.postulaciones.domain.entities.postulacion_publica import CvAdjunto


class CvStorage(ABC):
    @abstractmethod
    async def save_cv(self, cv: CvAdjunto, codigo_seguimiento: str) -> str:
        raise NotImplementedError

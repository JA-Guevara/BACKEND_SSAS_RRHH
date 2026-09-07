from abc import ABC, abstractmethod

from ssas.postulaciones.domain.entities.postulacion_publica import (
    DatosPostulantePublico,
    PostulacionCreada,
    PostulacionSeguimiento,
    PostulantePublico,
    VacantePublica,
)


class PostulacionPublicaRepository(ABC):
    @abstractmethod
    async def get_vacante(self, vacante_id: str) -> VacantePublica | None:
        raise NotImplementedError

    @abstractmethod
    async def get_etapa_inicial_id(self, empresa_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def get_postulante_by_empresa_ci(
        self, empresa_id: str, ci: str
    ) -> PostulantePublico | None:
        raise NotImplementedError

    @abstractmethod
    async def postulacion_exists(self, vacante_id: str, postulante_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def codigo_exists(self, codigo_seguimiento: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def upsert_postulante(
        self,
        empresa_id: str,
        datos: DatosPostulantePublico,
        cv_url: str,
    ) -> PostulantePublico:
        raise NotImplementedError

    @abstractmethod
    async def create_postulacion(
        self,
        vacante_id: str,
        postulante_id: str,
        etapa_id: str,
        codigo_seguimiento: str,
    ) -> PostulacionCreada:
        raise NotImplementedError

    @abstractmethod
    async def get_by_codigo(self, codigo_seguimiento: str) -> PostulacionSeguimiento | None:
        raise NotImplementedError

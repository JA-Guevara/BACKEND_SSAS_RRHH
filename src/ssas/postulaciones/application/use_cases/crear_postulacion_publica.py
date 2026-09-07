from pathlib import Path
from secrets import token_hex

from ssas.postulaciones.domain.entities.postulacion_publica import (
    CvAdjunto,
    DatosPostulantePublico,
    PostulacionCreada,
)
from ssas.postulaciones.domain.exceptions import (
    CvInvalidoError,
    EtapaInicialNoConfiguradaError,
    PostulacionDuplicadaError,
    VacanteNoDisponibleError,
)
from ssas.postulaciones.ports.outgoing.cv_storage import CvStorage
from ssas.postulaciones.ports.outgoing.postulacion_publica_repository import (
    PostulacionPublicaRepository,
)

MAX_CV_BYTES = 5 * 1024 * 1024
ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_CV_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}


class CrearPostulacionPublica:
    def __init__(
        self,
        repository: PostulacionPublicaRepository,
        cv_storage: CvStorage,
    ) -> None:
        self.repository = repository
        self.cv_storage = cv_storage

    async def execute(
        self,
        datos: DatosPostulantePublico,
        cv: CvAdjunto,
    ) -> PostulacionCreada:
        self._validate_cv(cv)

        vacante = await self.repository.get_vacante(datos.vacante_id)
        if vacante is None or vacante.estado != "PUBLICADA":
            raise VacanteNoDisponibleError("La vacante no existe o no esta publicada")

        etapa_id = await self.repository.get_etapa_inicial_id(vacante.empresa_id)
        if etapa_id is None:
            raise EtapaInicialNoConfiguradaError(
                "La empresa no tiene una etapa inicial de reclutamiento configurada"
            )

        postulante = await self.repository.get_postulante_by_empresa_ci(
            vacante.empresa_id, datos.ci
        )
        if postulante is not None and await self.repository.postulacion_exists(
            vacante.id, postulante.id
        ):
            raise PostulacionDuplicadaError("Ya existe una postulacion para esta vacante")

        codigo_seguimiento = await self._generate_codigo_seguimiento()
        cv_url = await self.cv_storage.save_cv(cv, codigo_seguimiento)
        postulante = await self.repository.upsert_postulante(vacante.empresa_id, datos, cv_url)

        return await self.repository.create_postulacion(
            vacante_id=vacante.id,
            postulante_id=postulante.id,
            etapa_id=etapa_id,
            codigo_seguimiento=codigo_seguimiento,
        )

    async def _generate_codigo_seguimiento(self) -> str:
        for _ in range(10):
            codigo = f"POST-{token_hex(4).upper()}"
            if not await self.repository.codigo_exists(codigo):
                return codigo
        raise PostulacionDuplicadaError("No se pudo generar un codigo de seguimiento unico")

    @staticmethod
    def _validate_cv(cv: CvAdjunto) -> None:
        if not cv.content:
            raise CvInvalidoError("El CV es obligatorio")
        if len(cv.content) > MAX_CV_BYTES:
            raise CvInvalidoError("El CV no debe superar 5 MB")

        extension = Path(cv.filename).suffix.lower()
        if extension not in ALLOWED_CV_EXTENSIONS:
            raise CvInvalidoError("El CV debe ser un archivo PDF o DOCX")

        if cv.content_type and cv.content_type not in ALLOWED_CV_CONTENT_TYPES:
            raise CvInvalidoError("El tipo de archivo CV debe ser PDF o DOCX")

from typing import Protocol

from ssas.analisis_cv.domain.analysis import ResultadoIA


class AnalysisProvider(Protocol):
    """Puerto de salida para la extracción de datos de una hoja de vida.

    El proveedor NO calcula el puntaje de afinidad: eso lo hace calcular_afinidad().
    """

    @property
    def nombre(self) -> str:
        """Identificador que se persiste en analisis_cv.modelo_usado."""
        ...

    async def analyze(self, texto: str, vacante: dict, catalogo: list[dict]) -> ResultadoIA: ...


class CvExtractor(Protocol):
    async def extract(self, cv_url: str) -> str: ...

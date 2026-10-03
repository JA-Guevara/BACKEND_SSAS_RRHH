from typing import Protocol

from ssas.analisis_cv.domain.analysis import ResultadoIA


class AnalysisProvider(Protocol):
    async def analyze(self, texto: str, vacante: dict, catalogo: list[dict]) -> ResultadoIA: ...


class CvExtractor(Protocol):
    async def extract(self, cv_url: str) -> str: ...

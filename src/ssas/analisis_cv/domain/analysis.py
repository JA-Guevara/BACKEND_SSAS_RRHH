from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AnalisisCvError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


class HabilidadDetectada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    habilidad_id: str = Field(min_length=1, max_length=36)
    nivel: str = Field(min_length=1, max_length=30)
    evidencia: str = Field(min_length=1, max_length=1000)


class ResultadoIA(BaseModel):
    model_config = ConfigDict(extra="forbid")
    habilidades: list[HabilidadDetectada] = Field(max_length=200)
    anios_experiencia: float = Field(ge=0, le=80, allow_inf_nan=False)
    evidencia_experiencia: str = Field(max_length=2000)
    resumen: str = Field(min_length=1, max_length=4000)
    justificacion: str = Field(min_length=1, max_length=4000)


def validar_evidencia(resultado: ResultadoIA, catalogo: set[str], texto: str) -> None:
    ids = [item.habilidad_id for item in resultado.habilidades]
    if len(set(ids)) != len(ids) or not set(ids).issubset(catalogo):
        raise AnalisisCvError("La IA devolvio habilidades duplicadas o ajenas al catalogo", 502)
    normalized = " ".join(texto.casefold().split())
    evidencias = [item.evidencia for item in resultado.habilidades]
    if resultado.anios_experiencia > 0:
        evidencias.append(resultado.evidencia_experiencia)
    if any(not e.strip() or " ".join(e.casefold().split()) not in normalized for e in evidencias):
        raise AnalisisCvError("La IA devolvio evidencia que no aparece en el CV", 502)


def calcular_afinidad(requisitos: list[dict], resultado: ResultadoIA, minima: int) -> Decimal:
    """80% habilidades acreditadas (pesos) + 20% experiencia, limitada al requisito."""
    ids = {item.habilidad_id for item in resultado.habilidades}
    total = sum((Decimal(str(item["peso"])) for item in requisitos), Decimal(0))
    covered = sum(
        (Decimal(str(item["peso"])) for item in requisitos if item["habilidad_id"] in ids),
        Decimal(0),
    )
    skills = covered / total if total else Decimal(1)
    experience = (
        min(Decimal(str(resultado.anios_experiencia)) / Decimal(minima), Decimal(1))
        if minima > 0
        else Decimal(1)
    )
    return (80 * skills + 20 * experience).quantize(Decimal("0.01"))

import re
from typing import Any

from ssas.analisis_cv.domain.analysis import (
    AnalisisCvError,
    HabilidadDetectada,
    ResultadoIA,
)
from ssas.config.settings import Settings

SINONIMOS: dict[str, tuple[str, ...]] = {
    "postgresql": ("postgres", "psql"),
    "typescript": ("ts",),
    "javascript": ("js",),
    "react": ("reactjs", "react.js"),
    "python": ("py",),
}


class ExtraccionLocalProvider:
    @property
    def nombre(self) -> str:
        return "extraccion-local-v1"

    def __init__(self, config: Settings) -> None:
        self.config = config

    @staticmethod
    def _normalizar(texto: str) -> str:
        return " ".join(texto.casefold().split())

    @staticmethod
    def _evidencia(texto_norm: str, pos: int, largo: int) -> str:
        """Recorta una ventana de hasta 160 caracteres del texto normalizado,

        centrada en el match y ajustada a límites de palabra.
        """
        ventana_max = 160
        if len(texto_norm) <= ventana_max:
            return texto_norm

        inicio_deseado = max(0, pos - (ventana_max - largo) // 2)
        fin_deseado = min(len(texto_norm), inicio_deseado + ventana_max)

        # Ajustar a límites de espacio si es posible
        if inicio_deseado > 0:
            espacio = texto_norm.find(" ", inicio_deseado)
            if espacio != -1 and espacio < pos:
                inicio_deseado = espacio + 1

        if fin_deseado < len(texto_norm):
            espacio = texto_norm.rfind(" ", pos + largo, fin_deseado)
            if espacio != -1 and espacio > pos + largo:
                fin_deseado = espacio

        evidencia = texto_norm[inicio_deseado:fin_deseado].strip()
        if not evidencia:
            evidencia = texto_norm[pos : pos + largo]
        return evidencia[:1000]

    @staticmethod
    def _nivel(entorno: str) -> str:
        entorno_lower = entorno.lower()
        if re.search(r"\b(senior|experto|avanzado)\b", entorno_lower):
            if "senior" in entorno_lower:
                return "SENIOR"
            if "experto" in entorno_lower:
                return "EXPERTO"
            return "AVANZADO"
        if re.search(r"\b(intermedio|semi[- ]?senior)\b", entorno_lower):
            return "INTERMEDIO"
        if re.search(r"\b(junior|basico|inicial)\b", entorno_lower):
            if "junior" in entorno_lower:
                return "JUNIOR"
            return "BASICO"
        return "MENCIONADO"

    def _buscar_habilidad(self, nombre: str, texto_norm: str) -> int | None:
        nombre_norm = self._normalizar(nombre)
        if not nombre_norm:
            return None
        # Búsqueda con límite de palabras completas en el nombre y sus sinónimos
        variantes = [nombre_norm, *(self._normalizar(s) for s in SINONIMOS.get(nombre_norm, ()))]
        for variante in variantes:
            if not variante:
                continue
            patron = r"(?<!\w)" + re.escape(variante) + r"(?!\w)"
            match = re.search(patron, texto_norm)
            if match:
                return match.start()
        return None

    @classmethod
    def _experiencia(cls, texto_norm: str) -> tuple[float, str]:
        # Busca p. ej. "5 años", "3.5 anios", "2 years"
        patron = r"(?<!\w)(\d{1,2}(?:[.,]\d)?)\s*(?:a[ñn]os?|anios?|years?)(?!\w)"
        matches = list(re.finditer(patron, texto_norm))
        if not matches:
            return 0.0, ""

        max_anios = 0.0
        mejor_match = None
        for m in matches:
            val_str = m.group(1).replace(",", ".")
            try:
                val = float(val_str)
                if 0.0 <= val <= 80.0 and val > max_anios:
                    max_anios = val
                    mejor_match = m
            except ValueError:
                continue

        if mejor_match is None or max_anios == 0.0:
            return 0.0, ""

        evidencia = cls._evidencia(
            texto_norm, mejor_match.start(), mejor_match.end() - mejor_match.start()
        )
        return max_anios, evidencia

    @staticmethod
    def _resumen(detectadas: list[str], faltantes: list[str], anios: float) -> str:
        partes = []
        if detectadas:
            partes.append(f"Se identificaron las habilidades: {', '.join(detectadas)}.")
        else:
            partes.append("No se identificaron habilidades del catálogo en el documento.")
        if anios > 0:
            partes.append(f"Se detectaron aproximadamente {anios:g} años de experiencia laboral.")
        else:
            partes.append("No se detectó mención explícita de años de experiencia.")
        resumen = " ".join(partes)
        return resumen[:4000]

    @staticmethod
    def _justificacion(detectadas: list[str], faltantes: list[str]) -> str:
        lineas = []
        if detectadas:
            lineas.append(f"Habilidades acreditadas en el CV: {', '.join(detectadas)}.")
        if faltantes:
            lineas.append(f"Requisitos no identificados en el texto: {', '.join(faltantes)}.")
        if not lineas:
            lineas.append("Análisis determinista local completado sin coincidencias destacadas.")
        justificacion = " ".join(lineas)
        return justificacion[:4000]

    async def analyze(
        self, texto: str, vacante: dict[str, Any], catalogo: list[dict[str, Any]]
    ) -> ResultadoIA:
        texto_norm = self._normalizar(texto)
        if len(texto_norm) < 50:
            raise AnalisisCvError("El CV no contiene texto suficiente para analizar", 422)

        habilidades_detectadas: list[HabilidadDetectada] = []
        nombres_detectados: list[str] = []
        ids_vistos: set[str] = set()

        # Búsqueda determinista sobre el catálogo
        for item in catalogo:
            habilidad_id = str(item.get("habilidad_id") or item.get("id", ""))
            nombre = str(item.get("nombre", ""))
            if not habilidad_id or not nombre or habilidad_id in ids_vistos:
                continue

            pos = self._buscar_habilidad(nombre, texto_norm)
            if pos is not None:
                ids_vistos.add(habilidad_id)
                nombres_detectados.append(nombre)
                evidencia = self._evidencia(texto_norm, pos, len(self._normalizar(nombre)))
                nivel = self._nivel(evidencia)
                habilidades_detectadas.append(
                    HabilidadDetectada(
                        habilidad_id=habilidad_id,
                        nivel=nivel,
                        evidencia=evidencia,
                    )
                )

        # Ordenar por habilidad_id para determinismo estricto
        habilidades_detectadas.sort(key=lambda h: h.habilidad_id)

        # Detectar experiencia
        anios_exp, evidencia_exp = self._experiencia(texto_norm)

        # Requisitos de la vacante para el resumen y justificación
        requisitos_vacante = vacante.get("habilidades", [])
        nombres_req = [
            str(r.get("nombre") or r.get("habilidad_nombre", ""))
            for r in requisitos_vacante
            if str(r.get("habilidad_id", "")) not in ids_vistos
        ]
        faltantes = [n for n in nombres_req if n]

        resumen = self._resumen(nombres_detectados, faltantes, anios_exp)
        justificacion = self._justificacion(nombres_detectados, faltantes)

        return ResultadoIA(
            habilidades=habilidades_detectadas,
            anios_experiencia=anios_exp,
            evidencia_experiencia=evidencia_exp,
            resumen=resumen,
            justificacion=justificacion,
        )

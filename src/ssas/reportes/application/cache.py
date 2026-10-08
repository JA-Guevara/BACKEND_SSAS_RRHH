"""Caché corta para las consultas agregadas del panel.

La clave **siempre** incluye la empresa: un caché de reportes sin el inquilino en
la clave es la forma más rápida de filtrar datos entre empresas. La clave también
incluye el hash de la consulta completa, de modo que dos paneles distintos no se
pisan.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from typing import Any

from ssas.reportes.infrastructure.http.schemas_agregado import ConsultaAgregada

TTL_SEGUNDOS = 60
MAX_ENTRADAS = 512


def clave_consulta(consulta: ConsultaAgregada) -> str:
    return hashlib.sha256(consulta.model_dump_json().encode("utf-8")).hexdigest()


class CacheAgregados:
    """Caché en memoria con caducidad y clave (empresa_id, hash de consulta)."""

    def __init__(
        self,
        ttl_segundos: float = TTL_SEGUNDOS,
        max_entradas: int = MAX_ENTRADAS,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_segundos
        self._max = max_entradas
        self._reloj = reloj
        self._datos: dict[tuple[str, str], tuple[Any, float]] = {}

    def get(self, empresa_id: str, clave: str) -> Any | None:
        entrada = self._datos.get((empresa_id, clave))
        if entrada is None:
            return None
        valor, expira = entrada
        if self._reloj() >= expira:
            self._datos.pop((empresa_id, clave), None)
            return None
        return valor

    def set(self, empresa_id: str, clave: str, valor: Any) -> None:
        if len(self._datos) >= self._max:
            self._limpiar()
        self._datos[(empresa_id, clave)] = (valor, self._reloj() + self._ttl)

    def _limpiar(self) -> None:
        ahora = self._reloj()
        for clave, (_, expira) in list(self._datos.items()):
            if expira <= ahora:
                self._datos.pop(clave, None)
        while len(self._datos) >= self._max:
            mas_vieja = min(self._datos, key=lambda item: self._datos[item][1])
            self._datos.pop(mas_vieja, None)

    def clear(self) -> None:
        self._datos.clear()


cache_agregados = CacheAgregados()
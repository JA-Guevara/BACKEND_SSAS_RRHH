"""Verifica que docs/01, docs/02 y docs/03 sigan coincidiendo con el código.

    python scripts/verificar_documentacion.py

Sale con código 1 si encuentra desincronización. Pensado para correr en CI y como
último paso del protocolo de agentes.

Sin esta comprobación, tres documentos mantenidos a mano se desincronizan en dos
sprints y la "fuente de verdad" pasa a ser decorativa.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
D01, D02, D03 = (
    DOCS / n
    for n in ("01_ESTADO_PROYECTO.md", "02_API_ENDPOINTS.md", "03_BACKLOG_IMPLEMENTACION.md")
)

METODOS = ("GET", "POST", "PUT", "PATCH", "DELETE")
IGNORAR = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
ESTADOS_API = ("IMPLEMENTADO", "PARCIAL", "PENDIENTE", "BLOQUEADO", "DEPRECADO")
ESTADOS_TASK = ("PENDIENTE", "EN_PROGRESO", "BLOQUEADO", "IMPLEMENTADO", "VALIDADO", "CANCELADO")

fallos: list[str] = []
avisos: list[str] = []


def rutas_del_codigo() -> set[tuple[str, str]]:
    """Fuente de verdad: el OpenAPI que produce la aplicación."""
    os.environ.setdefault("APP_SECRET_KEY", "x" * 40)
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/x")
    sys.path.insert(0, str(RAIZ / "src"))
    from ssas.main import app

    return {
        (metodo.upper(), ruta)
        for ruta, ops in app.openapi()["paths"].items()
        for metodo in ops
        if metodo.upper() in METODOS and ruta not in IGNORAR
    }


def filas_matriz(texto: str) -> dict[str, dict]:
    """Lee la matriz de 02:  | API-001 | POST | `/ruta` | ... | ESTADO | ... | TASK |"""
    filas: dict[str, dict] = {}
    patron = re.compile(
        r"^\|\s*\**(API-\w+)\**\s*\|\s*(" + "|".join(METODOS) + r")\s*\|\s*`([^`]+)`\s*\|(.*)$"
    )
    for linea in texto.splitlines():
        m = patron.match(linea.strip())
        if not m:
            continue
        resto = m.group(4)
        filas[m.group(1)] = {
            "metodo": m.group(2),
            "ruta": m.group(3),
            "estado": next((e for e in ESTADOS_API if e in resto), "DESCONOCIDO"),
            "tasks": re.findall(r"\b([A-Z]{3,6}-\d{3})\b", resto),
        }
    return filas


def ids_backlog(texto: str) -> dict[str, str]:
    """Lee los IDs y estados de las fichas de 03."""
    tareas: dict[str, str] = {}
    for m in re.finditer(r"^### TASK ([A-Z]{3,6}-\d{3})", texto, re.MULTILINE):
        bloque = texto[m.end() : m.end() + 400]
        tareas[m.group(1)] = next((e for e in ESTADOS_TASK if e in bloque), "DESCONOCIDO")
    return tareas


def main() -> int:
    for f in (D01, D02, D03):
        if not f.exists():
            fallos.append(f"falta el documento {f.relative_to(RAIZ)}")
    if fallos:
        for x in fallos:
            print(f"  FALLO  {x}")
        return 1

    t02 = D02.read_text(encoding="utf-8")
    t03 = D03.read_text(encoding="utf-8")
    matriz = filas_matriz(t02)
    tareas = ids_backlog(t03)
    codigo = rutas_del_codigo()

    documentadas = {(v["metodo"], v["ruta"]) for v in matriz.values()}
    implementadas = {
        (v["metodo"], v["ruta"]) for v in matriz.values() if v["estado"] == "IMPLEMENTADO"
    }
    pendientes = {(v["metodo"], v["ruta"]) for v in matriz.values() if v["estado"] == "PENDIENTE"}

    for metodo, ruta in sorted(codigo - documentadas):
        fallos.append(f"{metodo} {ruta} existe en el código y no está en la matriz de 02")

    for metodo, ruta in sorted(implementadas - codigo):
        fallos.append(f"{metodo} {ruta} está marcado IMPLEMENTADO y no existe en el código")

    for metodo, ruta in sorted(pendientes & codigo):
        fallos.append(f"{metodo} {ruta} está marcado PENDIENTE pero ya existe en el código")

    for api, v in sorted(matriz.items()):
        for t in v["tasks"]:
            if t not in tareas:
                fallos.append(f"{api} referencia la task {t}, que no existe en 03")
            elif v["estado"] == "PENDIENTE" and tareas[t] in ("IMPLEMENTADO", "VALIDADO"):
                fallos.append(f"{api} está PENDIENTE y su task {t} figura como {tareas[t]}")
            elif v["estado"] == "IMPLEMENTADO" and tareas[t] in ("PENDIENTE", "BLOQUEADO"):
                avisos.append(f"{api} está IMPLEMENTADO pero su task {t} sigue en {tareas[t]}")

    for t in sorted(set(re.findall(r"\b(API-\w+)\b", t03))):
        if t not in matriz and ".." not in t:
            avisos.append(f"03 referencia {t}, que no está en la matriz de 02")

    print(f"  código:  {len(codigo)} operaciones")
    print(
        f"  doc 02:  {len(matriz)} fichas ({len(implementadas)} implementadas, {len(pendientes)} pendientes)"
    )
    print(f"  doc 03:  {len(tareas)} tareas")
    print()
    for x in avisos:
        print(f"  AVISO  {x}")
    for x in fallos:
        print(f"  FALLO  {x}")
    if not fallos and not avisos:
        print("  Todo sincronizado.")
    elif not fallos:
        print(f"\n  {len(avisos)} aviso(s), ningún fallo.")
    else:
        print(f"\n  {len(fallos)} fallo(s), {len(avisos)} aviso(s).")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())

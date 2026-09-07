# Instrucciones de arranque para el proceso multiagente

> Textos listos para copiar y pegar. El plan completo está en
> `04_EJECUCION_MULTIAGENTE_SPRINT1.md`; acá está sólo lo que hay que pegar y en qué orden.

---

## Antes de lanzar nada — 3 minutos

```bash
cd <ruta>/backend_ssas_rrhh

# 1. ¿A qué base apunta el entorno? Local, Railway y las pruebas comparten
#    la MISMA base de Supabase. Si esto apunta a producción, no lances agentes.
python -c "import os;from dotenv import load_dotenv;load_dotenv();u=os.getenv('DATABASE_URL','');print(u.split('@')[-1] if '@' in u else u)"

# 2. Punto de retorno: el trabajo del sprint no está commiteado.
git status --short | head -20
git stash list
git checkout -b sprint1/cierre        # rama de trabajo para los agentes

# 3. Línea base. Anotá estos cuatro números: son el antes/después.
ruff check src tests            | tail -1     # esperado: Found 15 errors
PYTHONPATH=src pytest -q        | tail -1     # esperado: 39 passed, 3 skipped
alembic heads                                  # esperado: DOS cabezas
APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"
```

**Decisión que tenés que tomar vos antes de la Ola 1** (ningún agente puede tomarla):
la máquina de estados de las etapas — ¿se puede mover una postulación hacia atrás?
`TEST-005` necesita la respuesta para escribir el caso. Recomendación: permitir cualquier
transición y registrar todo en bitácora.

---

## Ola 0 — un solo agente, secuencial

No se lanza nada en paralelo acá. Las cinco tareas tocan migraciones, configuración y git.

### Prompt para el agente de la Ola 0

```text
Sos un agente de desarrollo del backend backend_ssas_rrhh (FastAPI, SQLAlchemy 2.0
async, PostgreSQL, Vertical Slicing + Hexagonal). Trabajás sobre la rama sprint1/cierre.

MISIÓN: Ola 0 del cierre del Sprint 1. Cinco tareas EN ESTE ORDEN, sin paralelizar:
  MIG-002 → SEC-001 → TOOL-001 → TOOL-002 → DOC-003

Leé primero, en este orden:
  1. docs/01_ESTADO_PROYECTO.md          — reglas de multitenencia y guards
  2. docs/04_EJECUCION_MULTIAGENTE_SPRINT1.md §2  — las cinco fichas con evidencia
  3. docs/03_BACKLOG_IMPLEMENTACION.md   — fichas de los cinco IDs

CONTEXTO: el Sprint 1 está funcionalmente terminado (65 endpoints), pero no es
entregable. Estos cinco bloqueadores están verificados ejecutando el código:
  - alembic upgrade head FALLA: hay dos cabezas (20260825_0002 y 20260907_0007).
    Consecuencia: las migraciones de permisos 0005/0006/0007 no se pueden aplicar,
    así que los 15 permisos nuevos no llegan a la base.
  - ROLE_DEFINITIONS en provision_empresa.py pide "vacantes:gestionar" y
    "candidatos:gestionar"; las migraciones crearon los GRANULARES
    (vacantes:ver|crear|editar|publicar|eliminar). El rol RECLUTADOR recibe 0 permisos
    y el filtro descarta los códigos desconocidos en silencio.
  - pytest a secas falla con 8 errores de colección; funciona con PYTHONPATH=src.
  - ruff check src tests: 15 errores, 8 en archivos del Sprint 1.
  - Los 19 endpoints nuevos NO están commiteados, y 157 archivos figuran como
    modificados sólo por CRLF frente a LF.

REGLAS
  - ANTES de cualquier comando que escriba en la base, verificá DATABASE_URL.
    Local, Railway y las pruebas comparten la misma base de Supabase.
  - MIG-002: usá `alembic merge`. NO reescribas migraciones existentes.
  - SEC-001: hacé que un código de permiso inexistente levante excepción, no que se
    ignore. Ningún rol de empresa recibe permisos platform:*.
  - TOOL-002: `ruff --fix` y nada más. El único manual es SIM102 en
    cargos/application/use_cases/actualizar_cargo.py:24. Corregí también las dos
    líneas con tabulación en src/ssas/core/api/router.py.
  - DOC-003: último paso. Commit único con todo el trabajo del sprint.
  - Ninguna credencial, clave ni token en el código.

VERIFICACIÓN al terminar cada tarea, y pegá la salida literal:
  ruff check src tests
  pytest -q
  alembic heads
  APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"

PUERTA DE SALIDA de la ola — las cuatro tienen que cumplirse:
  [ ] alembic heads devuelve UNA cabeza
  [ ] pytest -q (SIN PYTHONPATH) devuelve 39 passed, 3 skipped
  [ ] ruff check src tests dice All checks passed
  [ ] git status limpio y el trabajo del sprint commiteado
  [ ] la app sigue publicando 65 operaciones

REPORTE FINAL, una sección por tarea:
  ## <ID> — IMPLEMENTADO | BLOQUEADO
  Archivos creados / modificados
  Criterios: [x] o [ ] con el motivo
  Verificación: salida literal de los cuatro comandos
  DECISIONES PENDIENTES encontradas
```

**No pases a la Ola 1** hasta que los cinco checks de la puerta estén en verde. Si
`alembic upgrade head` sigue fallando, los agentes de la Ola 1 no pueden preparar datos
de prueba.

---

## Ola 1 — cuatro agentes en paralelo

El código está escrito y sin una sola prueba: `pytest` devuelve los mismos 39 tests de
antes del sprint. Esta ola no agrega funcionalidad, la respalda.

| Agente | Tarea | Archivos propios |
|---|---|---|
| A1 | `TEST-004` vacantes y portal público | `tests/unit/test_vacantes_api.py`, `test_vacantes_repository.py`, `test_portal_publico.py` |
| A2 | `TEST-005` tablero, etapas y motivos | `tests/unit/test_tablero.py`, `test_catalogos_reclutamiento.py`, `test_aislamiento_tablero.py` |
| A3 | `TEST-002` departamentos y cargos | `tests/unit/test_departamentos.py`, `test_cargos.py` |
| A4 | `TEST-003` + `TEST-006` empresas y roles base | `tests/unit/test_empresas.py`, `test_roles_base_provision.py` |

Cada agente escribe **sólo** sus archivos: no hay dos que toquen el mismo, así que no
hay conflicto posible.

### Prompt base para los cuatro (cambiá las tres líneas marcadas)

```text
Sos un agente de desarrollo del backend backend_ssas_rrhh (FastAPI, SQLAlchemy 2.0
async, PostgreSQL, Vertical Slicing + Hexagonal). Trabajás sobre la rama sprint1/cierre.

TAREA: <<<TEST-004>>>                              ← CAMBIAR
OLA: 1 (en paralelo con otros tres agentes)

Leé primero:
  1. docs/01_ESTADO_PROYECTO.md          — reglas de multitenencia y guards
  2. docs/04_EJECUCION_MULTIAGENTE_SPRINT1.md §4.2  — tus archivos y tus casos
  3. docs/03_BACKLOG_IMPLEMENTACION.md   — ficha de tu ID
  4. docs/02_API_ENDPOINTS.md            — contrato de los endpoints que probás
  5. tests/unit/test_roles.py            — el estilo de test del proyecto

ARCHIVOS QUE PODÉS CREAR:  <<<lista de la tabla de arriba>>>     ← CAMBIAR
ARCHIVOS PROHIBIDOS: todo lo que esté fuera de esa lista. En particular
  src/ssas/core/api/router.py, src/ssas/core/tenancy/middleware.py,
  src/ssas/core/api/openapi.py y migrations/versions/.
  Si necesitás tocar código de producción para que un test pase, NO lo toques:
  reportalo en un bloque INTEGRACIÓN REQUERIDA con el diff exacto y seguí.

CASOS OBLIGATORIOS: <<<los de §4.2 para tu tarea>>>              ← CAMBIAR

REGLAS QUE NO SE NEGOCIAN
  - Cada endpoint de alcance empresa necesita un test que pruebe que la empresa A NO
    alcanza datos de la B, y que FALLE si alguien quita el filtro del repositorio.
  - Se responde 404, no 403, ante un recurso de otra empresa: un 403 confirmaría
    que existe.
  - No modifiques los tests existentes ni el freno RUN_DATABASE_TESTS de los e2e.
  - Ninguna credencial real en los tests: datos simulados.

VERIFICACIÓN al terminar, pegá la salida literal:
  ruff check src tests
  pytest -q
  APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"

REPORTE FINAL
  ## <ID> — IMPLEMENTADO | BLOQUEADO
  Tests creados: <archivo::nombre_del_test> uno por línea, con el caso del perfil que cubre
  Criterios: [x] o [ ] con el motivo
  Verificación: salida literal
  INTEGRACIÓN REQUERIDA: diffs de código de producción, o "ninguna"
  DEFECTOS ENCONTRADOS: si un test revela un fallo real, describilo y NO lo arregles
```

**Lo que hay que mirar al cerrar la ola.** El caso `CP-S1-21` del agente A2 es el que el
perfil marca como FALLA. Si el test pasa a la primera, revisá que realmente esté probando
con dos empresas distintas y no con la misma. Si falla, `BUG-001` sigue abierto y hay que
arreglarlo antes de la Ola 2.

---

## Ola 2 — tres agentes en paralelo

| Agente | Tarea | Qué hace |
|---|---|---|
| B1 | `ARCH-001` | Saca las 8 llamadas a `session.execute` de `tablero_router.py` y las pone en repositorios con puerto |
| B2 | `TAB-004` | Siembra las 7 etapas base al aprovisionar una empresa: hoy nacen sin ninguna |
| B3 | `INFRA-001` | Base de pruebas separada de producción |

`ARCH-001` **sólo se lanza si `TEST-005` quedó en verde**: esos tests son la única red que
garantiza que el refactor no cambie el contrato HTTP.

### Prompt para B1 (`ARCH-001`), el más delicado

```text
Sos un agente de desarrollo del backend backend_ssas_rrhh. Rama sprint1/cierre.

TAREA: ARCH-001 — extraer el repositorio del tablero fuera del router
OLA: 2

Leé: docs/01_ESTADO_PROYECTO.md (regla 7), docs/04_EJECUCION_MULTIAGENTE_SPRINT1.md §4.2,
y el módulo src/ssas/cargos/ COMPLETO: es el patrón correcto a copiar.

PROBLEMA: src/ssas/postulaciones/infrastructure/http/tablero_router.py hace 8 llamadas
directas a session.execute/session.scalar y no usa ningún repositorio. Contradice dos
reglas del proyecto: "la lógica de negocio no vive en los routers" y la regla 7,
"el filtro por empresa_id va en el repositorio, no en el router". Hoy funciona; el
riesgo es que el filtro de empresa es lo único que separa los datos de dos clientes y
está en la capa donde es más fácil olvidarlo en el próximo endpoint.

ARCHIVOS QUE PODÉS CREAR O MODIFICAR: los 10 nuevos + tablero_router.py listados
  en §4.2 de la tarea ARCH-001. Nada más.

RESTRICCIÓN CENTRAL — no negociable:
  El contrato HTTP de los 5 endpoints del tablero NO cambia. Mismas rutas, mismos
  códigos de estado, mismos cuerpos de respuesta. Los tests de TEST-005 son la
  verificación: tienen que seguir pasando SIN QUE LOS MODIFIQUES. Si un test de
  TEST-005 falla, tu refactor está mal, no el test.

VERIFICACIÓN: ruff check src tests · pytest -q · y además:
  grep -c "session.execute\|session.scalar" src/ssas/postulaciones/infrastructure/http/tablero_router.py
  # tiene que devolver 0

REPORTE FINAL: el formato habitual, más la salida de ese grep.
```

---

## Ola 3 — el orquestador, no agentes

`DOC-002` colección Postman · `DOC-001` retirar el SQL a mano · `PERF-001` alinear el
perfil · `MIG-001` numeración de migraciones.

`PERF-001` es el que más pesa para la defensa: el perfil usa **dos numeraciones de CU
distintas** entre §3.10 y el Capítulo 4, y es lo primero que se detecta al revisarlo.

---

## Cierre de cada ola — lo hace el orquestador, nunca un agente

```bash
# 1. aplicar los bloques INTEGRACIÓN REQUERIDA de todos los agentes de la ola
# 2. puerta de calidad
ruff check src tests
pytest -q
alembic heads                     # UNA cabeza
APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"
# 3. actualizar docs/01 (contadores), docs/02 (estados) y docs/03 (estados)
# 4. commit de la ola
git commit -m "test(sprint1): ola 1 — TEST-002, TEST-003, TEST-004, TEST-005, TEST-006"
```

**Si un agente entrega en rojo, no se integra.** Se le devuelve la tarea con la salida del
comando que falló. Integrar en rojo hace que el siguiente agente herede un fallo ajeno y
no pueda distinguirlo del propio — es exactamente cómo se llegó al estado actual, con
`ROLE_DEFINITIONS` desalineado de las migraciones de permisos.

---

## Tabla de control

Marcá acá mientras avanza. Los números de la columna «esperado» son los que verifica la
puerta de cada ola.

| Ola | Tareas | Esperado al cerrar | Hecho |
|---|---|---|---|
| 0 | MIG-002 · SEC-001 · TOOL-001 · TOOL-002 · DOC-003 | 1 cabeza · `pytest` a secas verde · `ruff` verde · commiteado | ☐ |
| 1 | TEST-004 · TEST-005 · TEST-002 · TEST-003 · TEST-006 | ~39 → 80+ tests · CP-S1-21 en verde | ☐ |
| 2 | ARCH-001 · TAB-004 · INFRA-001 | 0 `session.execute` en routers · 7 etapas al aprovisionar | ☐ |
| 3 | DOC-002 · DOC-001 · PERF-001 · MIG-001 | 65 endpoints documentados · perfil alineado | ☐ |

**Línea base de hoy:** 65 endpoints · 43 permisos · 39 tests (0 del Sprint 1) ·
2 cabezas de Alembic · 15 errores de ruff · 0 commits del sprint.

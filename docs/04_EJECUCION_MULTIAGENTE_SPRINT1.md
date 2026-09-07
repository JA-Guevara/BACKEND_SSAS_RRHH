# 04 — EJECUCIÓN MULTIAGENTE DEL SPRINT 1

> **Manual de operación para correr el Sprint 1 con varios agentes en paralelo.**
> Complementa a `03_BACKLOG_IMPLEMENTACION.md`: el backlog dice *qué* hacer;
> este documento dice *en qué orden*, *quién toca qué archivo* y *cómo se verifica*.
>
> Verificado ejecutando el código el **2026-09-07** sobre el commit `782ac60`.
> Los cinco bloqueadores de la Ola 0 se detectaron ejecutando los comandos que
> aparecen en cada ficha: no son inferencias.

---

## 0. Lo que hay que leer antes de tocar nada

| Orden | Documento | Para qué |
|---|---|---|
| 1 | `01_ESTADO_PROYECTO.md` | Reglas de multitenencia, guards y arquitectura real |
| 2 | Este documento | Ola asignada, archivos propios y prohibidos |
| 3 | `03_BACKLOG_IMPLEMENTACION.md` § ficha del ID | Alcance, reglas de negocio y criterios |
| 4 | `02_API_ENDPOINTS.md` § endpoint | Contrato exacto de entrada y salida |

---

## 1. Estado verificado del Sprint 1

El Sprint 1 del perfil (Capítulo 4) promete *«publicar una vacante, exponerla en un
portal público, permitir la postulación con carga de hoja de vida desde web y móvil, y
visualizar a los postulantes en el tablero»*.

Esto es lo que el código hace hoy, comprobado ejecutándolo:

| CU | Caso de uso | Estado real | Evidencia |
|---|---|---|---|
| CU-07 | Gestionar departamentos y cargos | **FUNCIONA** | 8 endpoints en OpenAPI |
| CU-08 | Gestionar vacantes | **NO EXISTE** | `src/ssas/vacantes/` solo tiene entidad y modelo ORM: 0 endpoints |
| CU-09 | Explorar el portal público | **NO EXISTE** | `/publico/{slug}/vacantes` no está en OpenAPI |
| CU-10 | Postular con hoja de vida | **FUNCIONA** | `POST /api/v1/publico/postulaciones` |
| CU-11 | Consultar estado de la postulación | **FUNCIONA** | `GET /api/v1/publico/postulaciones/{codigo}` |
| CU-12 | Gestionar tablero de candidatos | **NO EXISTE** | `etapa_reclutamiento` y `motivo_rechazo` migradas y sin uso |
| — | Notificaciones (T-13) | **NO EXISTE** | ni cola, ni broker, ni servicio de envío |

**46 endpoints funcionan. Ninguno es de vacantes, portal ni tablero.** El flujo de valor
está cortado en el medio: se puede postular a una vacante que no se puede crear, y no
hay dónde ver a los postulantes.

### 1.1 Comandos de verificación y su resultado real

```bash
# app: OK
APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"
#  -> 46 operaciones (37 protegidas, 9 públicas)

# tests: OK sólo con PYTHONPATH
PYTHONPATH=src pytest -q      #  -> 39 passed, 3 skipped
pytest -q                     #  -> 8 errors: ModuleNotFoundError: No module named 'ssas'

# lint: ROJO antes de empezar
ruff check src tests          #  -> Found 15 errors (14 fixable)

# migraciones: ROTO
alembic upgrade head          #  -> FAILED: Multiple head revisions are present
alembic heads                 #  -> 20260825_0002 (head) / 20260906_0004 (head)
```

---

## 2. Ola 0 — Bloqueadores. Nada arranca hasta que esto esté en verde

**Un solo agente, en secuencia.** Las cuatro tareas tocan configuración y migraciones:
si se paralelizan, se pisan entre sí.

| ID | Tarea | Por qué bloquea |
|---|---|---|
| **MIG-002** | Unificar las dos cabezas de Alembic | `alembic upgrade head` falla. Ningún agente puede crear el esquema ni añadir migraciones |
| **SEC-001** | El rol RECLUTADOR nace sin permisos | El actor protagonista del Sprint 1 no puede hacer nada, y falla en silencio |
| **TOOL-001** | `pytest` no encuentra el paquete `ssas` | El paso 8 del protocolo de agentes es inejecutable tal como está documentado |
| **TOOL-002** | `ruff check src tests` ya está en rojo | Un agente no puede distinguir sus errores de los 15 preexistentes |
| **DOC-003** | Los documentos de control no están en git | Un agente que clona el repo no ve `01`, `02`, `03` ni `scripts/` |

Las fichas completas están en `03_BACKLOG_IMPLEMENTACION.md`. Resumen de cada una:

### MIG-002 — Unificar las dos cabezas de Alembic · CRÍTICA

El grafo de migraciones se bifurcó en `20260825_0001` y nunca se volvió a unir:

```text
                          ┌── 20260825_0002  (borrado_logico)              ← cabeza 1
<base> ── 20260825_0001 ──┤
                          └── 20260830_0002 ── 7694bb109d4b ── 0d142a1a7539
                                            ── 20260906_0003 ── 20260906_0004 ← cabeza 2
```

El daily del 27/08 ya lo anticipaba: *«Coordinar con Jose Armando el orden de las
migraciones de Alembic (dos cabezas en paralelo)»*. Nunca se resolvió.

**Qué hacer.** Generar una migración de fusión y no reescribir las existentes:

```bash
alembic merge -m "unificar cabezas sprint0 y sprint1" 20260825_0002 20260906_0004
alembic upgrade head --sql > /dev/null   # debe terminar sin error
alembic heads                            # debe imprimir UNA sola cabeza
```

**Criterios.** `alembic heads` devuelve una sola línea · `alembic upgrade head` no
falla · la migración nueva sigue la convención `AAAAMMDD_000N_descripcion`.

> **Antes de ejecutar cualquier cosa contra la base:** local, Railway y las pruebas
> apuntan a la **misma** base de Supabase. Verificá `DATABASE_URL` primero. Para
> migraciones, conexión directa (5432), no el pooler (6543).

### SEC-001 — El rol RECLUTADOR nace sin permisos · CRÍTICA

`provision_empresa.py:25-34` define los roles base así:

```python
("RECLUTADOR", "Reclutador", ("vacantes:gestionar", "candidatos:gestionar")),
```

Ninguno de esos dos códigos existe en el catálogo, que tiene 28 permisos. Y el filtro
que los resuelve descarta lo que no encuentra **sin avisar**:

```python
selected = [permission_by_code[c] for c in permission_codes if c in permission_by_code]
```

Resultado comprobado: al aprovisionar una empresa, `RECLUTADOR` se crea con **0
permisos**. El reclutador es el actor de CU-08, CU-09 y CU-12: hoy no puede hacer nada,
y nadie se enteraría hasta que alguien intente iniciar sesión con ese rol.

**Qué hacer.** Alinear `ROLE_DEFINITIONS` con los códigos que crea `VAC-004`, y hacer
que un código inexistente **falle en vez de ignorarse**.

**Criterios.** `RECLUTADOR` recibe los permisos de vacantes y postulaciones al
aprovisionar · un código inexistente en `ROLE_DEFINITIONS` levanta una excepción · hay
un test que lo prueba.

> **DECISIÓN PENDIENTE — resolver antes de la Ola 1.** El backlog planea permisos
> granulares (`vacantes:ver|crear|editar|publicar|eliminar`) y el código espera uno
> grueso (`vacantes:gestionar`). Hay que elegir **uno**: `VAC-004` y `SEC-001` deben
> usar el mismo vocabulario o el rol vuelve a quedar vacío.
> *Recomendación:* granular, por coherencia con `departamentos:*` y `cargos:*`, que ya
> son granulares y son el patrón del proyecto.

### TOOL-001 — `pytest` no encuentra el paquete · ALTA

`pytest` a secas falla con 8 errores de colección. Con `PYTHONPATH=src` pasan 39
pruebas. `pip install -e .` **no** lo arregla (comprobado).

**Qué hacer.** Añadir a `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
pythonpath = ["src"]          # ← esta línea
```

**Criterios.** `pytest` a secas devuelve 39 passed · el `README` y `01` documentan el
comando que realmente funciona.

### TOOL-002 — Dejar `ruff` en cero · ALTA

15 errores preexistentes, 14 autocorregibles: `I001` (imports), `UP037` (comillas en
anotaciones), `RUF100`, `RUF019`, `SIM102`.

```bash
ruff check src tests --fix
ruff check src tests            # debe decir "All checks passed"
```

El único no automático es `SIM102` en `cargos/application/use_cases/actualizar_cargo.py:24`.

**Criterios.** `ruff check src tests` en verde · no se tocó nada más que lo que ruff señaló.

### DOC-003 — Versionar los documentos de control · ALTA

`docs/01_ESTADO_PROYECTO.md`, `docs/02_API_ENDPOINTS.md`,
`docs/03_BACKLOG_IMPLEMENTACION.md`, este documento y `scripts/` figuran como **no
versionados** (`??` en `git status`). El paso 8 del protocolo manda ejecutar
`scripts/verificar_documentacion.py`, que no está en el repositorio.

Además: 157 archivos de `src/` aparecen como modificados y la diferencia es **sólo el
final de línea** (CRLF frente a LF). Cualquier diff de agente va a ser ilegible.

**Qué hacer.**

```bash
git add docs/01_ESTADO_PROYECTO.md docs/02_API_ENDPOINTS.md \
        docs/03_BACKLOG_IMPLEMENTACION.md docs/04_EJECUCION_MULTIAGENTE_SPRINT1.md \
        docs/tareas_sprint1.json scripts/
```

Y crear `.gitattributes` en la raíz:

```gitattributes
* text=auto eol=lf
*.py text eol=lf
*.md text eol=lf
```

Después, normalizar de una vez: `git add --renormalize .`

**Criterios.** `git status` limpio salvo los cambios reales · los cuatro documentos y
`scripts/` están en el índice · un clon nuevo del repositorio los trae.

---

## 3. Olas de ejecución

Dependencias tomadas del backlog, más las que impone el reparto de archivos.

```text
OLA 0  ── un agente, secuencial ────────────────────────────────────
   MIG-002 → SEC-001 → TOOL-001 → TOOL-002 → DOC-003
   Puerta: alembic heads = 1 · pytest verde · ruff verde · git limpio

OLA 1  ── 4 agentes en paralelo ────────────────────────────────────
   A1  VAC-004   permisos vacantes:* + postulaciones:* (ÚNICA migración de la ola)
   A2  VAC-001   puerto, entidad y repositorio de vacantes
   A3  TAB-001a  puertos y repositorios de etapas y motivos de rechazo
   A4  INFRA-001 base de pruebas separada

OLA 2  ── 3 agentes en paralelo ────────────────────────────────────
   B1  VAC-002   casos de uso de vacantes            (dep. A2)
   B2  BUG-001 + TEST-001  aislamiento entre empresas (dep. A4)
   B3  PTE-001 + HAB-001   postulantes y habilidades

OLA 3  ── 3 agentes en paralelo ────────────────────────────────────
   C1  VAC-003   endpoints de vacantes               (dep. B1, A1)  ⚠ archivo compartido
   C2  TAB-001b  endpoints de catálogos + seed de etapas (dep. A3)  ⚠ archivo compartido
   C3  TEST-002 + TEST-003  tests de organización y empresas

OLA 4  ── 2 agentes en paralelo ────────────────────────────────────
   D1  POR-001   portal público de empleos           (dep. C1)      ⚠ archivo compartido
   D2  TAB-002   tablero por etapas                  (dep. C2, C1, B2)

OLA 5  ── 2 agentes en paralelo ────────────────────────────────────
   E1  TAB-003   mover de etapa y rechazar con motivo (dep. D2)
   E2  PTE-003 + HAB-003  endpoints de postulantes y habilidades

CIERRE ── el orquestador, no los agentes ───────────────────────────
   DOC-002 colección Postman · DOC-001 retirar el SQL a mano
   PERF-001 alinear el perfil · MIG-001 numeración de migraciones
```

`NOT-001` (notificaciones, T-13) queda **fuera del Sprint 1**: sin decisión sobre el
broker y sin dónde guardar los CV de forma persistente, no se puede cerrar. Ver §6.

---

## 4. Reparto de archivos — la regla que evita que los agentes se pisen

### 4.1 Archivos compartidos: prohibidos para los agentes

Estos cuatro archivos los toca **únicamente el orquestador**, al cerrar cada ola:

| Archivo | Quién lo necesita | Por qué no lo edita el agente |
|---|---|---|
| `src/ssas/core/api/router.py` | VAC-003, TAB-001b, POR-001, PTE-003, HAB-003 | Cinco agentes añadiendo un `include_router` al mismo bloque = conflicto garantizado |
| `src/ssas/core/tenancy/middleware.py` | POR-001 (alta en `PUBLIC_PATHS`) | Mismo motivo |
| `src/ssas/core/api/openapi.py` | los que definan un tag nuevo | `TAG_VACANTES`, `TAG_PORTAL_PUBLICO` y `TAG_POSTULACIONES` **ya existen**: usarlos, no crearlos |
| `migrations/versions/` | VAC-004 y quien altere el esquema | Dos migraciones en paralelo vuelven a partir el grafo en dos cabezas (el error de MIG-002) |

**Cómo lo entrega el agente.** En vez de editar el archivo, deja al final de su reporte
un bloque `INTEGRACIÓN REQUERIDA` con el diff exacto:

```text
INTEGRACIÓN REQUERIDA
archivo: src/ssas/core/api/router.py
  + from ssas.vacantes.infrastructure.http.router import router as vacantes_router
  + api_router.include_router(vacantes_router)
```

**Regla de migraciones.** Una sola migración por ola, y la crea el agente que la ola
designe (`A1` en la Ola 1). Cualquier otro agente que necesite tocar el esquema lo
declara en `INTEGRACIÓN REQUERIDA` y espera la ola siguiente. Al terminar cada ola:
`alembic heads` debe seguir devolviendo **una** cabeza.

### 4.2 Archivos propios por tarea

`+` archivo nuevo · `~` archivo existente que se modifica

**VAC-001 · repositorio de vacantes**

```text
+ src/ssas/vacantes/domain/exceptions.py
+ src/ssas/vacantes/ports/__init__.py
+ src/ssas/vacantes/ports/outgoing/__init__.py
+ src/ssas/vacantes/ports/outgoing/vacante_repository.py
+ src/ssas/vacantes/infrastructure/persistence/repositories/__init__.py
+ src/ssas/vacantes/infrastructure/persistence/repositories/vacante_repository.py
+ tests/unit/test_vacantes_repository.py
```

Referencia a copiar: `src/ssas/cargos/ports/outgoing/cargo_repository.py` y
`src/ssas/cargos/infrastructure/persistence/repositories/cargo_repository.py`.
El modelo ORM y la entidad **ya existen**: no los reescribas.

**VAC-002 · casos de uso de vacantes**

```text
+ src/ssas/vacantes/application/__init__.py
+ src/ssas/vacantes/application/use_cases/__init__.py
+ src/ssas/vacantes/application/use_cases/listar_vacantes.py
+ src/ssas/vacantes/application/use_cases/crear_vacante.py
+ src/ssas/vacantes/application/use_cases/obtener_vacante.py
+ src/ssas/vacantes/application/use_cases/actualizar_vacante.py
+ src/ssas/vacantes/application/use_cases/publicar_vacante.py
+ src/ssas/vacantes/application/use_cases/eliminar_vacante.py
+ tests/unit/test_vacantes_use_cases.py
~ src/ssas/vacantes/domain/exceptions.py     (si falta alguna excepción)
```

Referencia: `src/ssas/cargos/application/use_cases/`.

**VAC-003 · endpoints de vacantes** → API-P01 … API-P06

```text
+ src/ssas/vacantes/infrastructure/http/__init__.py
+ src/ssas/vacantes/infrastructure/http/router.py
+ src/ssas/vacantes/infrastructure/http/schemas.py
+ tests/unit/test_vacantes_api.py
⚠ src/ssas/core/api/router.py                → INTEGRACIÓN REQUERIDA
~ docs/02_API_ENDPOINTS.md                   → pasar API-P01..P06 a IMPLEMENTADO
```

Referencia: `src/ssas/cargos/infrastructure/http/router.py`. Copiá tal cual
`_target_empresa`, `_repository`, `_raise_http_<x>_error` y el guard
`require_scoped_permission`. Usá `TAG_VACANTES` y `AUTHENTICATED_RESPONSES` de
`ssas.core.api.openapi`.

**VAC-004 · permisos** — el único agente con migración en la Ola 1

```text
+ migrations/versions/AAAAMMDD_000N_permisos_reclutamiento.py
~ src/ssas/platform/application/use_cases/provision_empresa.py   (junto con SEC-001)
+ tests/unit/test_permisos_reclutamiento.py
```

Referencia: `migrations/versions/20260830_0002_crear_departamentos_y_cargos.py`,
que ya siembra `departamentos:*` y `cargos:*` de forma idempotente.

**POR-001 · portal público** → API-P07, API-P08

```text
+ src/ssas/vacantes/infrastructure/http/router_publico.py
+ src/ssas/vacantes/infrastructure/http/schemas_publicos.py
+ src/ssas/vacantes/application/use_cases/listar_vacantes_publicas.py
+ src/ssas/vacantes/application/use_cases/obtener_vacante_publica.py
+ tests/unit/test_portal_publico.py
⚠ src/ssas/core/api/router.py                → INTEGRACIÓN REQUERIDA
⚠ src/ssas/core/tenancy/middleware.py        → INTEGRACIÓN REQUERIDA (PUBLIC_PATHS)
```

El prefijo público ya tiene precedente: `PUBLIC_PATH_PREFIXES` incluye
`/api/v1/publico/postulaciones/`. El portal necesita `/api/v1/publico/` como prefijo, o
una entrada por ruta. Usá `TAG_PORTAL_PUBLICO`.

**TAB-001 · catálogos de etapas y motivos** → API-P15, API-P16

`TAB-001` es una sola ficha en el backlog, pero aquí se parte en dos porque los
repositorios no dependen de nada y los endpoints sí: `TAB-001a` va en la Ola 1 y
`TAB-001b` en la Ola 3. Al cerrar `TAB-001b`, `TAB-001` queda IMPLEMENTADO en `03`.

```text
a) repositorios (Ola 1)
+ src/ssas/postulaciones/ports/outgoing/etapa_reclutamiento_repository.py
+ src/ssas/postulaciones/ports/outgoing/motivo_rechazo_repository.py
+ src/ssas/postulaciones/infrastructure/persistence/repositories/etapa_reclutamiento_repository.py
+ src/ssas/postulaciones/infrastructure/persistence/repositories/motivo_rechazo_repository.py

b) endpoints y seed (Ola 3)
+ src/ssas/postulaciones/application/use_cases/listar_etapas.py
+ src/ssas/postulaciones/application/use_cases/listar_motivos_rechazo.py
~ src/ssas/postulaciones/infrastructure/http/router.py     (router propio, ya existe)
~ src/ssas/postulaciones/infrastructure/http/schemas.py
~ src/ssas/platform/application/use_cases/provision_empresa.py   (seed de etapas base)
+ tests/unit/test_catalogos_reclutamiento.py
```

**TAB-002 · tablero por etapas** → API-P11, API-P12

```text
+ src/ssas/postulaciones/application/use_cases/obtener_tablero_vacante.py
+ src/ssas/postulaciones/application/use_cases/listar_postulaciones.py
~ src/ssas/postulaciones/ports/outgoing/postulacion_repository.py
+ src/ssas/postulaciones/infrastructure/persistence/repositories/postulacion_repository.py
~ src/ssas/postulaciones/infrastructure/http/router.py
+ tests/unit/test_tablero.py
```

**TAB-003 · mover de etapa y rechazar** → API-P13, API-P14

```text
+ src/ssas/postulaciones/application/use_cases/mover_postulacion_etapa.py
+ src/ssas/postulaciones/application/use_cases/rechazar_postulacion.py
~ src/ssas/postulaciones/infrastructure/http/router.py
~ src/ssas/postulaciones/domain/exceptions.py
+ tests/unit/test_acciones_tablero.py
```

**BUG-001 · aislamiento del tablero**

```text
~ el repositorio de postulaciones (filtro por empresa_id)
+ tests/unit/test_aislamiento_tablero.py
```

**PTE-001 / PTE-003 · postulantes** → API-P09, API-P10 · **HAB-001 / HAB-003 · habilidades** → API-P17, API-P18

Mismo patrón que VAC-001…VAC-003, dentro de `src/ssas/postulantes/` y
`src/ssas/habilidades/` respectivamente.

---

## 5. Contrato del agente

### 5.1 Plantilla de prompt

```text
Sos un agente de desarrollo del backend backend_ssas_rrhh (FastAPI, SQLAlchemy 2.0
async, PostgreSQL, arquitectura Vertical Slicing + Hexagonal).

TAREA: <ID> — <título>
OLA: <n>

Antes de escribir código, leé en este orden:
  1. docs/01_ESTADO_PROYECTO.md          (reglas de multitenencia y guards)
  2. docs/04_EJECUCION_MULTIAGENTE_SPRINT1.md §4.2   (tus archivos)
  3. docs/03_BACKLOG_IMPLEMENTACION.md   (ficha de <ID>)
  4. docs/02_API_ENDPOINTS.md            (contrato de <endpoints>)
  5. <archivo de referencia indicado en §4.2>

ARCHIVOS QUE PODÉS CREAR O MODIFICAR: <lista de §4.2>
ARCHIVOS PROHIBIDOS: los cuatro compartidos de §4.1. Si los necesitás, no los edites:
  reportalos en un bloque INTEGRACIÓN REQUERIDA con el diff exacto.

REGLAS QUE NO SE NEGOCIAN
  - El filtro por empresa_id va en el REPOSITORIO, nunca en el router.
  - Una vacante o postulación de otra empresa se responde 404, no 403: un 403
    confirmaría que existe.
  - empresa_id se toma del token, nunca del cuerpo de la petición.
  - La lógica de negocio no vive en el router.
  - El dominio no importa FastAPI, SQLAlchemy ni Pydantic.
  - Toda implementación de repositorio hereda de su puerto.
  - Nombres de negocio en español, capas técnicas en inglés.
  - No agregues capas nuevas ni renombres las existentes.
  - Ninguna credencial, clave ni token en el código: todo por variable de entorno.

ANTES DE TOCAR LA BASE DE DATOS
  Local, Railway y las pruebas comparten la misma base de Supabase. Verificá
  DATABASE_URL. No quites el freno de los tests e2e.

AL TERMINAR, ejecutá y pegá la salida:
  ruff check src tests
  pytest -q
  alembic heads          # si tocaste migraciones: debe devolver UNA cabeza
  APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"

REPORTE FINAL (formato obligatorio)
  ## <ID> — <IMPLEMENTADO | BLOQUEADO>
  Archivos creados:    <lista>
  Archivos modificados:<lista>
  Endpoints:           <IDs de 02, o —>
  Criterios:           <uno por línea, marcado [x] o [ ] con el motivo>
  Verificación:        <salida literal de los cuatro comandos>
  INTEGRACIÓN REQUERIDA: <diffs de archivos compartidos, o "ninguna">
  DECISIONES PENDIENTES que encontré: <lista, o "ninguna">
```

### 5.2 Definición de hecho

Una tarea está terminada cuando cumple **todo**:

1. Los criterios de aceptación de su ficha en `03` están marcados.
2. `ruff check src tests` en verde.
3. `pytest -q` en verde, con al menos un test nuevo que cubra la tarea.
4. Si es de alcance empresa: existe un test que prueba que la empresa A **no** alcanza
   datos de la B, y que falla si alguien quita el filtro.
5. `alembic heads` devuelve una sola cabeza.
6. La app importa y publica los endpoints esperados.
7. `02_API_ENDPOINTS.md` y `03_BACKLOG_IMPLEMENTACION.md` actualizados.
8. El bloque `INTEGRACIÓN REQUERIDA` está completo, o dice "ninguna".

### 5.3 Cierre de ola, a cargo del orquestador

```bash
# 1. aplicar los INTEGRACIÓN REQUERIDA de todos los agentes de la ola
# 2. puerta de calidad
ruff check src tests
pytest -q
alembic heads                     # UNA cabeza
APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"
# 3. actualizar 01 (contador de endpoints), 02 (estados) y 03 (estados)
# 4. commit por ola:  feat(sprint1): ola <n> — <IDs>
```

Si un agente entrega en rojo, **no se integra**: se le devuelve la tarea con la salida
del comando que falló. Integrar en rojo hace que el siguiente agente herede un fallo
ajeno y no pueda distinguirlo del propio.

---

## 6. Decisiones pendientes — resolverlas antes de lanzar la ola que las necesita

Ninguna la puede tomar un agente: son decisiones de negocio o de arquitectura.

| # | Decisión | Bloquea | Recomendación |
|---|---|---|---|
| 1 | Permisos de vacantes: granulares (`vacantes:ver|crear|editar|publicar|eliminar`) o gruesos (`vacantes:gestionar`) | SEC-001, VAC-004, Ola 1 | **Granulares**: es el patrón que ya usan `departamentos:*` y `cargos:*` |
| 2 | Máquina de estados de las etapas: ¿qué transiciones son legales? ¿se puede volver atrás? | TAB-003, Ola 5 | Permitir cualquier transición y registrar todo en bitácora; endurecer después con datos reales |
| 3 | Dónde se guardan los CV. Hoy es `local_cv_storage.py` y **el disco de Railway es efímero**: los CV se pierden en cada despliegue | POR-001, NOT-001, y CU-10 en producción | Supabase Storage: ya está en el stack y evita sumar un proveedor |
| 4 | `plan_suscripcion` y `suscripcion`: el perfil las diseña, el código las eliminó | PERF-001 | Decidir si el SaaS las necesita este semestre; si no, quitarlas del perfil |
| 5 | Numeración de CU: el perfil usa dos esquemas distintos (§3.10 y Capítulo 4) | PERF-001 y la defensa | Adoptar la del Capítulo 4 y corregir §3.10, no al revés |
| 6 | Notificaciones (T-13): ¿cola real o envío síncrono? | NOT-001 | Fuera del Sprint 1. Envío síncrono en el Sprint 2 y cola sólo si aparece la necesidad |

**Sobre la #3 y el perfil.** El daily del 31/08 dejó registrado el problema —*«Decidir
donde guardar los CV: el sistema de archivos de Railway es efimero»*— y no se resolvió.
CU-10 figura como funcionando, y funciona en local; en el despliegue los archivos
desaparecen. Conviene cerrarlo antes de la Sprint Review.

---

## 7. Riesgo que hay que declarar en la Sprint Review

El reporte de pruebas del propio perfil marca **CP-S1-21 como FALLA** (05/09/2026):

> *«Usuario autenticado de la empresa B solicita el tablero de una vacante de la
> empresa A → no responde 404»* — resultado obtenido: *«no responde 404»*.

Es un fallo de aislamiento entre empresas, documentado por el equipo y sin resolver
(`BUG-001`). Es exactamente lo que evalúa la pregunta 3.d del examen final. Dos
consideraciones:

1. El endpoint del tablero **todavía no existe**, así que el caso no se pudo haber
   probado contra el backend: se probó contra el frontend con datos simulados. Al
   implementar TAB-002 hay que hacerlo pasar de verdad, con dos empresas reales.
2. Hoy **6 de los 9 módulos con endpoints no tienen ningún test**, así que el
   aislamiento no está verificado tampoco en departamentos, cargos, empresas ni
   postulaciones. `TEST-001` cubre eso y por eso está en la Ola 2, no al final.

---

## 8. Resumen ejecutable

| Ola | Tareas | Agentes | Puerta de salida |
|---|---|---|---|
| 0 | MIG-002 · SEC-001 · TOOL-001 · TOOL-002 · DOC-003 | 1, secuencial | `alembic heads` = 1 · `pytest` verde · `ruff` verde · git limpio |
| 1 | VAC-004 · VAC-001 · TAB-001a · INFRA-001 | 4 | Los 5 permisos existen · repositorios con filtro por empresa |
| 2 | VAC-002 · BUG-001+TEST-001 · PTE-001+HAB-001 | 3 | Aislamiento probado en todos los módulos |
| 3 | VAC-003 · TAB-001b · TEST-002+TEST-003 | 3 | API-P01…P06, P15, P16 en OpenAPI |
| 4 | POR-001 · TAB-002 | 2 | API-P07, P08, P11, P12 · CP-S1-21 en verde |
| 5 | TAB-003 · PTE-003+HAB-003 | 2 | API-P13, P14, P09, P10, P17, P18 |
| Cierre | DOC-002 · DOC-001 · PERF-001 · MIG-001 | orquestador | 64 endpoints · perfil alineado |

**18 endpoints pendientes.** Al terminar: 46 + 18 = **64 endpoints** y el flujo de valor
del Sprint 1 completo de punta a punta.

La lista en formato consumible por un orquestador está en `docs/tareas_sprint1.json`,
con los mismos IDs, dependencias, olas y manifiestos de archivos de este documento.

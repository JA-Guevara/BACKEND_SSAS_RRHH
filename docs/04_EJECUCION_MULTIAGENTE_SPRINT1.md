# 04 — EJECUCIÓN MULTIAGENTE DEL SPRINT 1

> **Manual de operación para cerrar el Sprint 1 con varios agentes en paralelo.**
> Complementa a `03_BACKLOG_IMPLEMENTACION.md`: el backlog dice *qué* hacer;
> este documento dice *en qué orden*, *quién toca qué archivo* y *cómo se verifica*.
>
> Verificado **ejecutando el código** el 2026-09-07, sobre el árbol de trabajo (no sobre
> `782ac60`: el árbol está muy por delante del último commit). Todo número de esta página
> sale de un comando, no de una estimación.

---

## 0. Lo que hay que leer antes de tocar nada

| Orden | Documento | Para qué |
|---|---|---|
| 1 | `01_ESTADO_PROYECTO.md` | Reglas de multitenencia, guards y arquitectura real |
| 2 | Este documento | Ola asignada, archivos propios y prohibidos |
| 3 | `03_BACKLOG_IMPLEMENTACION.md` § ficha del ID | Alcance, reglas de negocio y criterios |
| 4 | `02_API_ENDPOINTS.md` § endpoint | Contrato exacto de entrada y salida |

---

## 1. Estado real del Sprint 1

El Sprint 1 del perfil (Capítulo 4) promete *«publicar una vacante, exponerla en un
portal público, permitir la postulación con carga de hoja de vida desde web y móvil, y
visualizar a los postulantes en el tablero»*.

**Ese flujo ya está implementado de punta a punta.** La API pasó de 46 a **65
operaciones**: los 18 endpoints que figuraban como pendientes existen, más un
`DELETE /habilidades/{id}` que no estaba en el contrato.

| CU | Caso de uso | Endpoints | Código | Tests |
|---|---|---|---|---|
| CU-07 | Gestionar departamentos y cargos | 8 | **sí** | **0** |
| CU-08 | Gestionar vacantes | 6 | **sí** | **0** |
| CU-09 | Explorar el portal público | 2 | **sí** | **0** |
| CU-10 | Postular con hoja de vida | 1 | sí | 0 |
| CU-11 | Consultar estado de la postulación | 1 | sí | 0 |
| CU-11 | Banco de talentos (postulantes) | 2 | **sí** | **0** |
| CU-12 | Tablero de candidatos | 5 | **sí** | **0** |
| — | Catálogo de habilidades | 3 | **sí** | **0** |
| — | Notificaciones (T-13) | 0 | no | — |

Endpoints del Sprint 1 verificados en OpenAPI:

```text
GET    /api/v1/vacantes                                        sec
POST   /api/v1/vacantes                                        sec
GET    /api/v1/vacantes/{vacante_id}                            sec
PUT    /api/v1/vacantes/{vacante_id}                            sec
PATCH  /api/v1/vacantes/{vacante_id}/publicar                   sec
DELETE /api/v1/vacantes/{vacante_id}                            sec
GET    /api/v1/vacantes/{vacante_id}/tablero                    sec
GET    /api/v1/publico/{empresa_slug}/vacantes                  PÚBLICO
GET    /api/v1/publico/{empresa_slug}/vacantes/{vacante_id}     PÚBLICO
GET    /api/v1/etapas-reclutamiento                             sec
GET    /api/v1/motivos-rechazo                                  sec
GET    /api/v1/postulaciones                                    sec
PATCH  /api/v1/postulaciones/{postulacion_id}/etapa             sec
PATCH  /api/v1/postulaciones/{postulacion_id}/rechazar          sec
GET    /api/v1/postulantes                                      sec
GET    /api/v1/postulantes/{postulante_id}                      sec
GET    /api/v1/habilidades                                      sec
POST   /api/v1/habilidades                                      sec
DELETE /api/v1/habilidades/{habilidad_id}                       sec
```

El catálogo de permisos pasó de 28 a **43**: se agregaron `vacantes:ver|crear|editar|publicar|eliminar`,
`habilidades:ver|gestionar`, `postulaciones:ver|gestionar` y `postulantes:ver`.

**Lo que falta no es funcionalidad: es lo que hace que la funcionalidad sea entregable.**

### 1.1 Comandos de verificación y su resultado real

```bash
# la app arranca y publica todo
APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app; print(len(app.openapi()['paths']))"
#  -> OK · 65 operaciones (55 protegidas, 10 públicas)

# las pruebas: en verde, pero SOLO con PYTHONPATH y sin cubrir nada nuevo
PYTHONPATH=src pytest -q      #  -> 39 passed, 3 skipped   (los MISMOS 39 de antes)
pytest -q                     #  -> 8 errors: ModuleNotFoundError: No module named 'ssas'

# lint: rojo
ruff check src tests          #  -> Found 15 errors (14 fixable), 8 de ellos en archivos del Sprint 1

# migraciones: ROTO — y ahora bloquea los permisos nuevos
alembic upgrade head          #  -> FAILED: Multiple head revisions are present
alembic heads                 #  -> 20260825_0002 (head) / 20260907_0007 (head)
```

> **La consecuencia práctica del grafo roto:** las tres migraciones de permisos
> (`0005`, `0006`, `0007`) **no se pueden aplicar** con el comando documentado. Los 15
> permisos nuevos existen en el código y no en la base. Los 19 endpoints nuevos están
> protegidos por permisos que nadie tiene.

---

## 2. Ola 0 — Bloqueadores. Nada se entrega hasta que esto esté en verde

**Un solo agente, en secuencia.** Las cinco tocan configuración, migraciones y git: si se
paralelizan, se pisan entre sí.

| ID | Tarea | Por qué bloquea la entrega |
|---|---|---|
| **MIG-002** | Unificar las dos cabezas de Alembic | `alembic upgrade head` falla → los 15 permisos nuevos no llegan a la base → los 19 endpoints nuevos no se pueden usar |
| **SEC-001** | El rol RECLUTADOR sigue naciendo sin permisos | Los permisos granulares ya existen, pero `ROLE_DEFINITIONS` pide `vacantes:gestionar`, que no existe. El reclutador tiene **0** permisos |
| **TOOL-001** | `pytest` no encuentra el paquete `ssas` | El paso 8 del protocolo es inejecutable tal como está documentado |
| **TOOL-002** | `ruff check src tests` en rojo | 15 errores, 8 en archivos recién escritos |
| **DOC-003** | Nada está commiteado | 19 endpoints de trabajo viven sólo en el disco de una máquina |

### MIG-002 — Unificar las dos cabezas de Alembic · CRÍTICA

El grafo se bifurcó en `20260825_0001` y **nunca se volvió a unir**. Las migraciones
nuevas extendieron una de las dos ramas, así que el problema sigue igual:

```text
                          ┌── 20260825_0002  (borrado_logico)                    ← cabeza 1
<base> ── 20260825_0001 ──┤
                          └── 20260830_0002 ── 7694bb109d4b ── 0d142a1a7539 ──
                              20260906_0003 ── 0004 ── 0005 ── 0006 ── 0007      ← cabeza 2
```

El daily del 27/08 ya lo anticipaba: *«Coordinar con Jose Armando el orden de las
migraciones de Alembic (dos cabezas en paralelo)»*.

```bash
alembic merge -m "unificar cabezas sprint0 y sprint1" 20260825_0002 20260907_0007
alembic heads                            # debe imprimir UNA sola cabeza
alembic upgrade head --sql > /dev/null   # debe terminar sin error
```

**Criterios.** `alembic heads` devuelve una sola línea · `alembic upgrade head` no falla ·
los 43 permisos existen en la base después de aplicarla · no se reescribió ninguna
migración existente.

> **Antes de ejecutar cualquier cosa contra la base:** local, Railway y las pruebas
> apuntan a la **misma** base de Supabase. Verificá `DATABASE_URL`. Para migraciones,
> conexión directa (5432), no el pooler (6543).

### SEC-001 — El rol RECLUTADOR sigue naciendo sin permisos · CRÍTICA

Esto es lo que pasó, y es el caso de libro de por qué el reparto entre agentes necesita
un dueño de la integración:

- Las migraciones nuevas crearon los permisos **granulares**:
  `vacantes:ver|crear|editar|publicar|eliminar`.
- `provision_empresa.py` **no se tocó**, y sigue pidiendo el permiso **grueso**:

```python
("RECLUTADOR", "Reclutador", ("vacantes:gestionar", "candidatos:gestionar")),
```

- Ninguno de esos dos códigos existe entre los 43, y el filtro descarta lo que no
  encuentra **sin avisar**:

```python
selected = [permission_by_code[c] for c in permission_codes if c in permission_by_code]
```

Comprobado sobre el árbol actual: `RECLUTADOR pide 2 → recibe 0`. El actor de CU-08,
CU-09 y CU-12 no puede llamar a ninguno de los 19 endpoints nuevos, y no hay ningún
error que lo delate.

**Qué hacer.**

1. Reemplazar los dos códigos por los granulares que sí existen:
   `vacantes:ver|crear|editar|publicar`, `postulaciones:ver|gestionar`,
   `postulantes:ver`, `habilidades:ver`.
2. Hacer que un código inexistente **falle** en vez de ignorarse.
3. Test que detecte un rol base sin permisos.

**Criterios.** RECLUTADOR recibe sus permisos al aprovisionar · un código inexistente
levanta excepción · existe test · ningún rol de empresa recibe `platform:*`.

### TOOL-001 — `pytest` no encuentra el paquete · ALTA

```text
$ pytest -q                    -> ModuleNotFoundError: No module named 'ssas' · 8 errors
$ PYTHONPATH=src pytest -q     -> 39 passed, 3 skipped
```

`pip install -e .` **no** lo arregla (comprobado). Añadir a `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
pythonpath = ["src"]          # ← esta línea
```

### TOOL-002 — Dejar `ruff` en cero · ALTA

15 errores, 14 autocorregibles. **8 están en archivos del Sprint 1**, así que no es
deuda vieja: es deuda que se acaba de crear.

| Regla | Cuántos | Dónde |
|---|---|---|
| `UP037` comillas en anotaciones | 6 | modelos de `etapa_reclutamiento`, `motivo_rechazo`, `postulante` |
| `I001` imports desordenados | 6 | `main.py`, `database/base.py`, `database/session.py`, `cargo.py`, `vacante.py`, `local_cv_storage.py` |
| `RUF100` `noqa` sin usar | 1 | `database/base.py:29` |
| `RUF019` + `SIM102` | 2 | `cargos/…/actualizar_cargo.py:24` — `SIM102` es el único manual |

```bash
ruff check src tests --fix && ruff check src tests && pytest -q
```

Aparte: `src/ssas/core/api/router.py` tiene **dos líneas indentadas con tabulación**
mientras el resto del proyecto usa cuatro espacios. Corregir en la misma pasada.

### DOC-003 — Versionar el trabajo y normalizar finales de línea · ALTA

Dos problemas que rompen cualquier trabajo coordinado:

1. **Los 19 endpoints nuevos no están commiteados.** El último commit es `782ac60` y el
   árbol tiene 17 archivos nuevos o modificados sin versionar, incluidas las tres
   migraciones de permisos. Tampoco están versionados `docs/01`, `02`, `03`, `04`,
   `tareas_sprint1.json` ni `scripts/` — y el paso 8 del protocolo manda ejecutar
   `scripts/verificar_documentacion.py`, que no existe en el repositorio.
2. **157 archivos de `src/` figuran como modificados por puro final de línea** (CRLF
   frente a LF). Comprobado: normalizando los saltos, el árbol local y el de GitHub son
   idénticos byte a byte. Cualquier diff de agente es hoy ilegible.

```bash
git add -A src migrations docs scripts
printf '* text=auto eol=lf\n*.py text eol=lf\n*.md text eol=lf\n' > .gitattributes
git add .gitattributes && git add --renormalize .
git commit -m "feat(sprint1): vacantes, portal publico, tablero, postulantes y habilidades"
```

**Criterios.** `git status` limpio salvo cambios reales · un clon nuevo trae los 65
endpoints y los cuatro documentos · `.gitattributes` existe.

---

## 3. Olas de ejecución

El trabajo funcional del Sprint 1 está hecho. Lo que queda son tres frentes: **desbloquear
la entrega** (Ola 0), **probar lo que se escribió** (Ola 1) y **volver la arquitectura a su
sitio** (Ola 2).

```text
OLA 0  ── un agente, secuencial ────────────────────────────────────
   MIG-002 → SEC-001 → TOOL-001 → TOOL-002 → DOC-003
   Puerta: alembic heads = 1 · pytest verde a secas · ruff verde · git commiteado

OLA 1  ── 4 agentes en paralelo · pruebas de lo ya escrito ─────────
   A1  TEST-004  vacantes y portal público      (CU-08, CU-09)
   A2  TEST-005  tablero, etapas y motivos      (CU-12) — incluye CP-S1-19/20/21
   A3  TEST-002  departamentos y cargos         (CU-07)
   A4  TEST-003 + TEST-006  empresas y permisos de roles base

OLA 2  ── 3 agentes en paralelo · arquitectura ─────────────────────
   B1  ARCH-001  extraer el repositorio del tablero fuera del router
   B2  TAB-004   seed de etapas base al aprovisionar una empresa
   B3  INFRA-001 base de pruebas separada de producción

OLA 3  ── cierre, el orquestador ───────────────────────────────────
   DOC-002 Postman · DOC-001 retirar el SQL a mano
   PERF-001 alinear el perfil · MIG-001 numeración de migraciones
```

`NOT-001` (notificaciones, T-13) queda **fuera del Sprint 1**: sin decisión sobre el
broker y sin dónde guardar los CV de forma persistente, no se puede cerrar. Ver §6.

### 3.1 Por qué las pruebas son la Ola 1 y no el final

`pytest` sigue devolviendo **los mismos 39 tests de antes**. Se escribieron 19 endpoints,
19 permisos y un tablero completo sin una sola prueba. Eso significa tres cosas concretas:

1. **`CP-S1-21` sigue sin verificarse.** El reporte del perfil lo marca FALLA
   (05/09/2026): *«Usuario autenticado de la empresa B solicita el tablero de una vacante
   de la empresa A → no responde 404»*. El código nuevo **sí** hace la comprobación
   (`tablero_router.py:118-120` responde 404 si la vacante no es de la empresa), pero
   nadie lo probó, y no hay nada que impida que el próximo cambio lo rompa.
2. **Ningún endpoint nuevo tiene prueba de aislamiento.** Es la pregunta 3.d del examen
   final y hoy la respuesta es «confiamos en que el filtro está».
3. **`IMPLEMENTADO` no es `VALIDADO`.** El backlog distingue los dos estados. Los
   endpoints del Sprint 1 están en el primero. Para la Sprint Review hace falta el
   segundo.

---

## 4. Reparto de archivos — la regla que evita que los agentes se pisen

### 4.1 Archivos compartidos: prohibidos para los agentes

Estos cuatro los toca **únicamente el orquestador**, al cerrar cada ola:

| Archivo | Quién lo necesita | Por qué no lo edita el agente |
|---|---|---|
| `src/ssas/core/api/router.py` | cualquier módulo nuevo | Varios agentes añadiendo `include_router` al mismo bloque = conflicto garantizado |
| `src/ssas/core/tenancy/middleware.py` | cualquier ruta pública nueva | Mismo motivo |
| `src/ssas/core/api/openapi.py` | quien defina un tag nuevo | `TAG_VACANTES`, `TAG_PORTAL_PUBLICO` y `TAG_POSTULACIONES` **ya existen**: usarlos |
| `migrations/versions/` | quien altere el esquema | **Es exactamente el error de `MIG-002`.** Dos migraciones en paralelo vuelven a partir el grafo |

**Cómo lo entrega el agente.** En vez de editar el archivo, deja al final de su reporte
un bloque `INTEGRACIÓN REQUERIDA` con el diff exacto:

```text
INTEGRACIÓN REQUERIDA
archivo: src/ssas/core/api/router.py
  + from ssas.<modulo>.infrastructure.http.router import router as <x>_router
  + api_router.include_router(<x>_router)
```

**Regla de migraciones.** Una sola migración por ola, y la crea el agente que la ola
designe. Al terminar cada ola, `alembic heads` debe devolver **una** cabeza. Esta regla
existe porque ya se incumplió una vez y costó el bloqueo entero de la entrega.

**Regla de permisos.** Quien crea un permiso nuevo actualiza `ROLE_DEFINITIONS` en
`provision_empresa.py` **en el mismo cambio**. Un permiso que ningún rol recibe no
protege: deja el endpoint inalcanzable. Es lo que pasó con `SEC-001`.

### 4.2 Archivos propios por tarea

`+` archivo nuevo · `~` archivo existente que se modifica

**TEST-004 · vacantes y portal público**

```text
+ tests/unit/test_vacantes_api.py
+ tests/unit/test_vacantes_repository.py
+ tests/unit/test_portal_publico.py
```

Casos obligatorios, tomados del perfil:

| Caso | Qué debe pasar |
|---|---|
| `CP01` | `POST /vacantes` con datos válidos → 201 y la vacante aparece en el portal |
| `CP02` | Campos obligatorios vacíos → 422 con el detalle |
| `CP03` | `fecha_cierre` anterior a hoy → error de validación |
| `CP-S1-08` | Portal responde 200 sin token y muestra la marca de la empresa |
| `CP-S1-09` | Slug inexistente → 404 genérico, sin revelar información |
| `CP-S1-10` | Vacante con `fecha_cierre` vencida **no** aparece en el portal |
| `CP-S1-11` | `mostrar_salario` desactivado → el detalle no expone el rango |
| aislamiento | Empresa A no ve ni edita vacantes de la empresa B → 404 |

Referencia: `tests/unit/test_roles.py` para el estilo. El repositorio a probar es
`src/ssas/vacantes/infrastructure/persistence/repositories/vacante_repository.py`;
sus condiciones públicas están en `_public_conditions`.

**TEST-005 · tablero, etapas y motivos**

```text
+ tests/unit/test_tablero.py
+ tests/unit/test_catalogos_reclutamiento.py
+ tests/unit/test_aislamiento_tablero.py
```

Casos obligatorios:

| Caso | Qué debe pasar |
|---|---|
| `CP-S1-19` | Mover de etapa cambia la columna **y** escribe un evento en la bitácora |
| `CP-S1-20` | Rechazar sin motivo → 400 |
| `CP-S1-21` | Empresa B pide el tablero de una vacante de A → **404**, no 403 |
| — | El motivo de rechazo debe pertenecer al catálogo de la empresa |
| — | El tablero agrupa por etapa según `orden`, con contador por columna |
| — | Sin el permiso `postulaciones:ver` → 403 |

`CP-S1-21` es el que el perfil marca FALLA. Este test es el que cierra `BUG-001`: no se
da por terminado hasta que esté en verde y falle si alguien quita el filtro.

**TEST-002 · departamentos y cargos** → `tests/unit/test_departamentos.py`,
`tests/unit/test_cargos.py`. Árbol por `departamento_padre_id`, 409 por nombre duplicado,
rango `salario_min`/`salario_max`, aislamiento entre empresas.

**TEST-003 + TEST-006 · empresas y permisos de roles base** →
`tests/unit/test_empresas.py`, `tests/unit/test_roles_base_provision.py`.
El aprovisionamiento crea empresa, roles base y administrador; **ningún rol de empresa
recibe `platform:*`**; y —lo que descubrió `SEC-001`— **ningún rol base queda sin
permisos**.

**ARCH-001 · extraer el repositorio del tablero**

```text
+ src/ssas/postulaciones/ports/outgoing/postulacion_repository.py
+ src/ssas/postulaciones/ports/outgoing/etapa_reclutamiento_repository.py
+ src/ssas/postulaciones/ports/outgoing/motivo_rechazo_repository.py
+ src/ssas/postulaciones/infrastructure/persistence/repositories/postulacion_repository.py
+ src/ssas/postulaciones/infrastructure/persistence/repositories/etapa_reclutamiento_repository.py
+ src/ssas/postulaciones/infrastructure/persistence/repositories/motivo_rechazo_repository.py
+ src/ssas/postulaciones/application/use_cases/obtener_tablero_vacante.py
+ src/ssas/postulaciones/application/use_cases/listar_postulaciones.py
+ src/ssas/postulaciones/application/use_cases/mover_postulacion_etapa.py
+ src/ssas/postulaciones/application/use_cases/rechazar_postulacion.py
~ src/ssas/postulaciones/infrastructure/http/tablero_router.py
```

`tablero_router.py` hace **8 llamadas directas a `session.execute` / `session.scalar` y
no usa ningún repositorio**. Eso contradice dos reglas del propio proyecto:

> *«La lógica de negocio no vive en los routers.»*
> *«Todo repositorio de un recurso de empresa filtra por `empresa_id`. **En el
> repositorio, no en el router.**»* — regla 7 de `01_ESTADO_PROYECTO.md`

Hoy funciona. El problema es que el filtro de empresa es lo único que separa los datos de
dos clientes, y está en la capa donde es más fácil olvidarlo en el próximo endpoint.
Referencia del patrón correcto: el módulo `cargos` completo.

**No cambiar el contrato HTTP.** Los cinco endpoints del tablero deben responder
exactamente lo mismo antes y después. `TEST-005` es la red de seguridad: hacerlo
**después** de que esos tests estén en verde.

**TAB-004 · seed de etapas base al aprovisionar**

```text
~ src/ssas/platform/application/use_cases/provision_empresa.py
+ tests/unit/test_seed_etapas.py
```

`provision_empresa.py` no menciona `etapa` ni una vez. Una empresa nueva nace **sin
etapas de reclutamiento**, así que su tablero arranca vacío y `PATCH /postulaciones/{id}/etapa`
responde 404 para cualquier etapa. El perfil precarga **siete etapas por defecto**
(tarea T1-03 del sprint). El seed va donde ya se siembran los roles base.

**Criterios.** Una empresa nueva nace con sus siete etapas · exactamente una tiene
`es_inicial`, una `es_contratado` y una `es_rechazado` · el `orden` es único y consecutivo.

**INFRA-001 · base de pruebas separada** → `.env.test.example`, `tests/conftest.py`,
`docs/guias/GUIA_DESARROLLO.md`. El freno de los e2e no se quita: se complementa con una
base propia.

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
  - Si creás un permiso, actualizá ROLE_DEFINITIONS en el mismo cambio.
  - Si tocás el esquema, sos el único de tu ola que crea migración.
  - Nombres de negocio en español, capas técnicas en inglés.
  - No agregues capas nuevas ni renombres las existentes.
  - Ninguna credencial, clave ni token en el código: todo por variable de entorno.

ANTES DE TOCAR LA BASE DE DATOS
  Local, Railway y las pruebas comparten la misma base de Supabase. Verificá
  DATABASE_URL. No quites el freno de los tests e2e.

AL TERMINAR, ejecutá y pegá la salida:
  ruff check src tests
  pytest -q
  alembic heads          # debe devolver UNA cabeza
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
   datos de la B, y que **falla si alguien quita el filtro**.
5. `alembic heads` devuelve una sola cabeza.
6. La app importa y publica los endpoints esperados (65 o más).
7. `02_API_ENDPOINTS.md` y `03_BACKLOG_IMPLEMENTACION.md` actualizados.
8. El bloque `INTEGRACIÓN REQUERIDA` está completo, o dice "ninguna".

> **`IMPLEMENTADO` no es `VALIDADO`.** Una tarea de API pasa a `IMPLEMENTADO` cuando el
> endpoint responde según el contrato, y a `VALIDADO` cuando existe el test que lo
> demuestra. Los 19 endpoints del Sprint 1 están hoy en el primer estado. Para la Sprint
> Review hace falta el segundo.

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

Si un agente entrega en rojo, **no se integra**: se le devuelve la tarea con la salida del
comando que falló. Integrar en rojo hace que el siguiente agente herede un fallo ajeno y
no pueda distinguirlo del propio.

---

## 6. Decisiones pendientes — resolverlas antes de lanzar la ola que las necesita

Ninguna la puede tomar un agente: son decisiones de negocio o de arquitectura.

| # | Decisión | Bloquea | Estado |
|---|---|---|---|
| 1 | Permisos de vacantes: granulares o gruesos | `SEC-001` | **RESUELTA de hecho**: las migraciones crearon los granulares. Falta que `provision_empresa.py` los use |
| 2 | Máquina de estados de las etapas: ¿qué transiciones son legales? ¿se puede volver atrás? | `TEST-005`, `ARCH-001` | Abierta. El código actual permite cualquier transición. *Recomendación:* dejarlo así y registrar todo en bitácora; endurecer con datos reales |
| 3 | Dónde se guardan los CV. Hoy es `local_cv_storage.py` y **el disco de Railway es efímero**: los CV se pierden en cada despliegue | CU-10 en producción, `NOT-001` | Abierta desde el daily del 31/08. *Recomendación:* Supabase Storage, ya está en el stack |
| 4 | `plan_suscripcion` y `suscripcion`: el perfil las diseña, el código las eliminó | `PERF-001` | Abierta |
| 5 | Numeración de CU: el perfil usa dos esquemas distintos (§3.10 y Capítulo 4) | `PERF-001` y la defensa | Abierta. *Recomendación:* adoptar la del Capítulo 4 y corregir §3.10 |
| 6 | Notificaciones (T-13): ¿cola real o envío síncrono? | `NOT-001` | Abierta. Fuera del Sprint 1 |
| 7 | `DELETE /api/v1/habilidades/{id}` existe en el código y **no** en el contrato de `02` | `DOC-002` | ¿Se documenta o se retira? |

**Sobre la #3.** El daily del 31/08 dejó registrado el problema —*«Decidir donde guardar
los CV: el sistema de archivos de Railway es efimero»*— y no se resolvió. CU-10 figura
como funcionando, y funciona en local; en el despliegue los archivos desaparecen.
Conviene cerrarlo antes de la Sprint Review, porque es el tipo de detalle que la docente
pregunta al ver la demo.

---

## 7. Lo que hay que poder defender en la Sprint Review

| Pregunta previsible | Respuesta hoy | Qué la vuelve defendible |
|---|---|---|
| *¿El flujo funciona de punta a punta?* | Sí, 65 endpoints | Nada: ya está |
| *¿Un cliente puede ver datos de otro?* | «El filtro está en el código» | `TEST-005` + `TEST-004`: un test que falle si alguien lo quita |
| *`CP-S1-21` figura como FALLA en su informe* | El código ahora responde 404 | El test que lo demuestre, y actualizar el reporte del perfil |
| *¿Cómo despliegan la base?* | `alembic upgrade head` **falla** | `MIG-002` |
| *¿El reclutador puede publicar una vacante?* | **No**: tiene 0 permisos | `SEC-001` |
| *Muéstrenme el repositorio* | El trabajo no está commiteado | `DOC-003` |

Los dos últimos son los que más pesan: un repositorio sin los commits del sprint y un rol
que no puede operar son observaciones que se hacen en treinta segundos de revisión.

---

## 8. Resumen ejecutable

| Ola | Tareas | Agentes | Puerta de salida |
|---|---|---|---|
| 0 | MIG-002 · SEC-001 · TOOL-001 · TOOL-002 · DOC-003 | 1, secuencial | `alembic heads` = 1 · `pytest` verde a secas · `ruff` verde · trabajo commiteado |
| 1 | TEST-004 · TEST-005 · TEST-002 · TEST-003+TEST-006 | 4 | CP01–CP03 y CP-S1-08…21 en verde · aislamiento probado en todos los módulos |
| 2 | ARCH-001 · TAB-004 · INFRA-001 | 3 | Cero `session.execute` en routers · empresa nueva con sus 7 etapas · base de pruebas propia |
| 3 | DOC-002 · DOC-001 · PERF-001 · MIG-001 | orquestador | Contrato, perfil y migraciones alineados con el código |

**Estado de partida:** 65 endpoints, 43 permisos, 39 tests (ninguno del Sprint 1),
5 bloqueadores abiertos, 0 commits del sprint.

**Estado de llegada:** los mismos 65 endpoints, con pruebas que los respaldan, el
esquema desplegable, el reclutador operativo y todo en el repositorio.

La lista en formato consumible por un orquestador está en
[`tareas_sprint1.json`](tareas_sprint1.json), con los mismos IDs, dependencias, olas y
manifiestos de archivos de este documento.

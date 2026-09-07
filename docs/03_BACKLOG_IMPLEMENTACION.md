# 03 — BACKLOG DE IMPLEMENTACIÓN

> Centro de control del desarrollo. Abrí este archivo, elegí un ID y un agente
> tiene todo lo necesario para ejecutarlo.
> Sincronizado el **2026-09-07** contra el commit `782ac60`.

**Estados:** `PENDIENTE` · `EN_PROGRESO` · `BLOQUEADO` · `IMPLEMENTADO` · `VALIDADO` · `CANCELADO`  
**Prioridades:** `CRITICA` · `ALTA` · `MEDIA` · `BAJA`  
**Tipos:** `ARCHITECTURE` `DATABASE` `DOMAIN` `USE_CASE` `REPOSITORY` `API` `SECURITY` `TEST` `DOCUMENTATION` `BUG` `REFACTOR` `INTEGRATION`

---

## Matriz

| ID | Tarea | Módulo | PA / CU | Tipo | Prioridad | Estado | Dependencias | Endpoints |
|---|---|---|---|---|---|---|---|---|
| **AUTH-001** | Autenticación y sesión | Auth | PA-01 / CU-03 | API | CRITICA | IMPLEMENTADO | — | API-001, API-002, API-003, API-004, API-005, API-006, API-007, API-008, API-009 |
| **BUG-001** | Corregir el aislamiento multi-tenant del tablero de candidatos | Tablero | PA-03 / CU-12 | BUG | CRITICA | IMPLEMENTADO | — | API-P11 |
| **INFRA-001** | Separar la base de pruebas de la de producción | Infraestructura | — | ARCHITECTURE | CRITICA | BLOQUEADO | — | — |
| **MIG-002** | Unificar las dos cabezas de Alembic | Infraestructura | — | DATABASE | CRITICA | PENDIENTE | — | — |
| **SEC-001** | El rol RECLUTADOR sigue naciendo sin permisos | Empresas | PA-01 / CU-01 | SECURITY | CRITICA | PENDIENTE | — | — |
| **TEST-004** | Tests de vacantes y portal público | Vacantes | PA-02 / CU-08, CU-09 | TEST | CRITICA | PENDIENTE | TOOL-001, TOOL-002 | API-P01..API-P08 |
| **TEST-005** | Tests del tablero, etapas y motivos | Tablero | PA-03 / CU-12 | TEST | CRITICA | PENDIENTE | TOOL-001, TOOL-002 | API-P11..API-P16 |
| **TEST-006** | Test de permisos de los roles base | Empresas | PA-01 / CU-01, CU-05 | TEST | CRITICA | PENDIENTE | SEC-001 | — |
| **ARCH-001** | Extraer el repositorio del tablero fuera del router | Tablero | PA-03 / CU-12 | REFACTOR | ALTA | PENDIENTE | TEST-005 | API-P11..API-P16 |
| **DOC-003** | Versionar el trabajo del sprint y normalizar finales de línea | Documentación | — | DOCUMENTATION | ALTA | PENDIENTE | MIG-002, SEC-001, TOOL-001, TOOL-002 | — |
| **TAB-004** | Seed de etapas base al aprovisionar una empresa | Tablero | PA-03 / CU-12 | USE_CASE | ALTA | PENDIENTE | SEC-001 | API-P15 |
| **TOOL-001** | `pytest` no encuentra el paquete `ssas` | Infraestructura | — | REFACTOR | ALTA | PENDIENTE | — | — |
| **TOOL-002** | Dejar `ruff` en cero | Transversal | — | REFACTOR | ALTA | PENDIENTE | — | — |
| **TEST-001** | Tests de aislamiento entre empresas | Transversal | PA-01 | TEST | CRITICA | PENDIENTE | INFRA-001 | API-010..API-046 |
| **EMP-001** | Empresas y aprovisionamiento | Empresas | PA-01 / CU-01, CU-02 | API | ALTA | IMPLEMENTADO | ROL-001 | API-026, API-027, API-028, API-029, API-030, API-031, API-032, API-033 |
| **PERF-001** | Alinear el perfil del proyecto con el código | Documentación | — | DOCUMENTATION | ALTA | PENDIENTE | — | — |
| **POR-001** | Portal público de empleos | Portal | PA-02 / CU-09 | API | ALTA | IMPLEMENTADO | VAC-003 | API-P07, API-P08 |
| **POS-001** | Postulación pública | Postulaciones | PA-02 / CU-09, CU-12 | API | ALTA | IMPLEMENTADO | — | API-044, API-045 |
| **ROL-001** | Roles y permisos | Roles | PA-01 / CU-05 | API | ALTA | IMPLEMENTADO | USR-001 | API-020, API-021, API-022, API-023, API-024, API-025 |
| **TAB-001** | Catálogos de etapas y motivos de rechazo | Tablero | PA-03 / CU-12 | API | ALTA | IMPLEMENTADO | — | API-P15, API-P16 |
| **TAB-002** | Tablero de candidatos por etapas | Tablero | PA-03 / CU-12 | API | ALTA | IMPLEMENTADO | TAB-001, VAC-003, BUG-001 | API-P11, API-P12 |
| **TAB-003** | Mover de etapa y rechazar con motivo | Tablero | PA-03 / CU-12 | API | ALTA | IMPLEMENTADO | TAB-002 | API-P13, API-P14 |
| **TEST-002** | Tests de departamentos y cargos | Organización | PA-04 / CU-19 | TEST | ALTA | PENDIENTE | INFRA-001 | — |
| **TEST-003** | Tests de empresas (platform) | Empresas | PA-01 / CU-01 | TEST | ALTA | PENDIENTE | INFRA-001 | — |
| **USR-001** | Gestión de usuarios | Usuarios | PA-01 / CU-04 | API | ALTA | IMPLEMENTADO | AUTH-001 | API-010, API-011, API-012, API-013, API-014, API-015, API-016, API-017, API-018, API-019 |
| **VAC-001** | Repositorio de vacantes | Vacantes | PA-02 / CU-08 | REPOSITORY | ALTA | IMPLEMENTADO | — | — |
| **VAC-002** | Casos de uso de vacantes | Vacantes | PA-02 / CU-08 | USE_CASE | ALTA | IMPLEMENTADO | VAC-001 | — |
| **VAC-003** | Endpoints de vacantes | Vacantes | PA-02 / CU-08 | API | ALTA | IMPLEMENTADO | VAC-002, VAC-004 | API-P01, API-P02, API-P03, API-P04, API-P05, API-P06 |
| **VAC-004** | Permisos `vacantes:*` en el catálogo | Vacantes | PA-02 / CU-08 | SECURITY | ALTA | IMPLEMENTADO | — | — |
| **BIT-001** | Bitácora de auditoría | Bitácora | PA-01 / CU-06 | API | MEDIA | IMPLEMENTADO | USR-001 | API-034, API-035 |
| **CAR-001** | Cargos | Cargos | PA-04 / CU-19 | API | MEDIA | IMPLEMENTADO | DEP-001 | API-040, API-041, API-042, API-043 |
| **DEP-001** | Departamentos | Departamentos | PA-04 / CU-19 | API | MEDIA | IMPLEMENTADO | EMP-001 | API-036, API-037, API-038, API-039 |
| **DOC-001** | Retirar el esquema SQL escrito a mano | Documentación | — | DOCUMENTATION | MEDIA | PENDIENTE | — | — |
| **HAB-001** | Capa de aplicación de habilidades | Habilidades | PA-02 / apoyo CU-08 | USE_CASE | MEDIA | IMPLEMENTADO | — | — |
| **MIG-001** | Normalizar la numeración de migraciones | Infraestructura | — | REFACTOR | MEDIA | PENDIENTE | — | — |
| **NOT-001** | Servicio de notificaciones y cola asíncrona | Notificaciones | PA-02 / CU-35 | INTEGRATION | MEDIA | BLOQUEADO | POR-001 | — |
| **PTE-001** | Repositorio y casos de uso de postulantes | Postulantes | PA-02 / CU-11 | REPOSITORY | MEDIA | IMPLEMENTADO | — | — |
| **PTE-003** | Endpoints de postulantes | Postulantes | PA-02 / CU-11 | API | MEDIA | IMPLEMENTADO | PTE-001 | API-P09, API-P10 |
| **SYS-001** | Healthcheck | Sistema | — | API | MEDIA | IMPLEMENTADO | — | API-046 |
| **DOC-002** | Regenerar la colección Postman desde el OpenAPI | Documentación | — | DOCUMENTATION | BAJA | PENDIENTE | — | — |
| **HAB-003** | Endpoints de habilidades | Habilidades | PA-02 / apoyo CU-08 | API | BAJA | IMPLEMENTADO | HAB-001 | API-P17, API-P18 |

**41 tareas:** 9 críticas · 20 altas · 10 medias · 2 bajas

> **`IMPLEMENTADO` no es `VALIDADO`.** Las 19 tareas marcadas IMPLEMENTADO del
> Sprint 1 tienen el endpoint respondiendo según el contrato y **cero tests**.
> Pasan a `VALIDADO` cuando exista la prueba que lo demuestre: eso es la Ola 1.

## Orden de ejecución

El plan vive en **[`04_EJECUCION_MULTIAGENTE_SPRINT1.md`](04_EJECUCION_MULTIAGENTE_SPRINT1.md)**
y los textos listos para pegarle a cada agente en
**[`PROMPT_INICIO_MULTIAGENTE.md`](PROMPT_INICIO_MULTIAGENTE.md)**. La versión consumible
por un orquestador está en [`tareas_sprint1.json`](tareas_sprint1.json).

**El Sprint 1 está funcionalmente terminado: 65 endpoints.** Lo que falta no es
funcionalidad, es lo que la vuelve entregable. Verificado ejecutando el código el
2026-09-07 sobre el árbol de trabajo:

```text
OLA 0 — desbloquear la entrega (un agente, secuencial)
   MIG-002   alembic upgrade head FALLA: dos cabezas → los 15 permisos nuevos
             no llegan a la base y los 19 endpoints quedan inalcanzables
   SEC-001   ROLE_DEFINITIONS pide vacantes:gestionar y las migraciones crearon
             los granulares → RECLUTADOR recibe 0 permisos, en silencio
   TOOL-001  pytest a secas falla: 8 errores de colección
   TOOL-002  ruff check src tests: 15 errores, 8 en archivos del Sprint 1
   DOC-003   los 19 endpoints nuevos NO están commiteados
   Puerta: alembic heads = 1 · pytest verde a secas · ruff verde · commiteado

OLA 1 — probar lo que ya se escribió (4 agentes)
   TEST-004 vacantes y portal · TEST-005 tablero (cierra BUG-001 / CP-S1-21)
   TEST-002 departamentos y cargos · TEST-003 + TEST-006 empresas y roles base
   Puerta: CP01–CP03 y CP-S1-08…21 en verde · aislamiento probado

OLA 2 — devolver la arquitectura a su sitio (3 agentes)
   ARCH-001 sacar los 8 session.execute de tablero_router.py a repositorios
   TAB-004  seed de las 7 etapas base al aprovisionar (hoy nacen sin ninguna)
   INFRA-001 base de pruebas separada de producción

OLA 3 — cierre documental (orquestador)
   DOC-002 Postman · DOC-001 retirar el SQL a mano
   PERF-001 alinear el perfil · MIG-001 numeración de migraciones
```

> `NOT-001` queda **fuera del Sprint 1**: falta decidir el broker y dónde se almacenan los
> CV, porque el disco de Railway es efímero. Las siete decisiones pendientes están en el
> §6 del documento 04.

---

## Fichas

### TASK MIG-002 — Unificar las dos cabezas de Alembic

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | CRITICA | DATABASE | Infraestructura | — |

**Descripción.** El grafo se bifurcó en `20260825_0001` y nunca se volvió a unir. Las
migraciones de permisos del Sprint 1 extendieron una de las dos ramas, así que el problema
sigue igual:

```text
$ alembic upgrade head
FAILED: Multiple head revisions are present for given argument 'head'

$ alembic heads
20260825_0002 (head)
20260907_0007 (head)
```

```text
                          ┌── 20260825_0002  (borrado_logico)                    ← cabeza 1
<base> ── 20260825_0001 ──┤
                          └── 20260830_0002 ── 7694bb109d4b ── 0d142a1a7539 ──
                              20260906_0003 ── 0004 ── 0005 ── 0006 ── 0007      ← cabeza 2
```

**Consecuencia práctica:** las migraciones `0005`, `0006` y `0007` **no se pueden aplicar**
con el comando documentado. Los 15 permisos nuevos existen en el código y no en la base, y
los 19 endpoints del Sprint 1 están protegidos por permisos que nadie tiene. El daily del
27/08 ya lo anticipaba: *«Coordinar con Jose Armando el orden de las migraciones de Alembic
(dos cabezas en paralelo)»*.

**Dependencias:** ninguna · **Endpoints:** —

**Criterios de aceptación**

- [ ] `alembic heads` devuelve **una** sola línea
- [ ] `alembic upgrade head --sql` termina sin error
- [ ] Los 43 permisos existen en la base después de aplicarla
- [ ] No se reescribió ninguna migración existente

```bash
alembic merge -m "unificar cabezas sprint0 y sprint1" 20260825_0002 20260907_0007
alembic heads && alembic upgrade head --sql > /dev/null
```

**Tests requeridos:** Integration

**Riesgos.** Local, Railway y las pruebas apuntan a la **misma** base de Supabase.
Verificar `DATABASE_URL`. Para migraciones, conexión directa (5432), no el pooler (6543).

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK SEC-001 — El rol RECLUTADOR sigue naciendo sin permisos

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | CRITICA | SECURITY | Empresas | PA-01 / CU-01 |

**Descripción.** Caso de libro de por qué el reparto entre agentes necesita un dueño de la
integración. Las migraciones del Sprint 1 crearon los permisos **granulares**
(`vacantes:ver|crear|editar|publicar|eliminar`), pero `provision_empresa.py` no se tocó y
sigue pidiendo el **grueso**:

```python
("RECLUTADOR", "Reclutador", ("vacantes:gestionar", "candidatos:gestionar")),
```

Ninguno de esos dos códigos existe entre los 43, y el filtro descarta lo que no encuentra
**sin avisar**:

```python
selected = [permission_by_code[c] for c in permission_codes if c in permission_by_code]
```

Comprobado sobre el árbol actual: `RECLUTADOR pide 2 → recibe 0`. El actor de CU-08, CU-09
y CU-12 no puede llamar a ninguno de los 19 endpoints nuevos, y no hay error que lo delate.

**Dependencias:** ninguna (coordinar con `TEST-006`) · **Endpoints:** —

**Reglas de negocio**

- Un rol de empresa **nunca** recibe permisos con prefijo `platform:`
- Un código de permiso que no existe es un error de programación, no un caso a ignorar

**Criterios de aceptación**

- [ ] RECLUTADOR recibe `vacantes:ver|crear|editar|publicar`, `postulaciones:ver|gestionar`, `postulantes:ver` y `habilidades:ver`
- [ ] Un código inexistente en `ROLE_DEFINITIONS` levanta una excepción
- [ ] Ningún rol de empresa recibe permisos `platform:*`

**Tests requeridos:** Unit · Integration (ver `TEST-006`)

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TOOL-001 — `pytest` no encuentra el paquete `ssas`

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | REFACTOR | Infraestructura | — |

**Descripción.** El paso 8 del protocolo de agentes manda ejecutar `pytest`, y falla:

```text
$ pytest -q                    -> ModuleNotFoundError: No module named 'ssas' · 8 errors
$ PYTHONPATH=src pytest -q     -> 39 passed, 3 skipped
```

`pip install -e .` **no** lo arregla (comprobado). Los 3 saltados llevan freno intencional
(`RUN_DATABASE_TESTS=1`): eso está bien y no se toca.

**Dependencias:** ninguna · **Endpoints:** —

**Criterios de aceptación**

- [ ] `pytest -q` a secas devuelve `39 passed, 3 skipped`
- [ ] El comando documentado en `README` y en `01` es el que funciona
- [ ] Los 3 tests con freno de base real siguen saltándose

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
pythonpath = ["src"]          # ← esta línea
```

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TOOL-002 — Dejar `ruff` en cero

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | REFACTOR | Transversal | — |

**Descripción.** `ruff check src tests` devuelve **15 errores**, 14 autocorregibles.
**8 están en archivos recién escritos del Sprint 1**, así que no es deuda vieja.

| Regla | Cuántos | Dónde |
|---|---|---|
| `UP037` comillas en anotaciones | 6 | modelos de `etapa_reclutamiento`, `motivo_rechazo`, `postulante` |
| `I001` imports desordenados | 6 | `main.py`, `database/base.py`, `database/session.py`, `cargo.py`, `vacante.py`, `local_cv_storage.py` |
| `RUF100` `noqa` sin usar | 1 | `database/base.py:29` |
| `RUF019` + `SIM102` | 2 | `cargos/…/actualizar_cargo.py:24` — `SIM102` es el único manual |

Aparte: `src/ssas/core/api/router.py` tiene **dos líneas indentadas con tabulación**
mientras el resto del proyecto usa cuatro espacios.

**Dependencias:** ninguna · **Endpoints:** —

**Criterios de aceptación**

- [ ] `ruff check src tests` dice `All checks passed`
- [ ] `pytest` sigue en verde
- [ ] `core/api/router.py` usa 4 espacios, no tabulaciones
- [ ] No se tocó nada que ruff no haya señalado

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK DOC-003 — Versionar el trabajo del sprint y normalizar finales de línea

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | DOCUMENTATION | Documentación | — |

**Descripción.** Dos problemas que rompen cualquier trabajo coordinado:

1. **Los 19 endpoints nuevos no están commiteados.** El último commit es `782ac60` y el
   árbol tiene 17 archivos nuevos o modificados sin versionar, incluidas las tres
   migraciones de permisos. Tampoco están versionados `docs/01`, `02`, `03`, `04`,
   `PROMPT_INICIO_MULTIAGENTE.md`, `tareas_sprint1.json` ni `scripts/` — y el paso 8 del
   protocolo manda ejecutar `scripts/verificar_documentacion.py`, que no existe en el
   repositorio.
2. **157 archivos de `src/` figuran como modificados por puro final de línea** (CRLF frente
   a LF). Comprobado: normalizando los saltos, el árbol local y el de GitHub son idénticos
   byte a byte. Cualquier diff de agente es hoy ilegible.

**Dependencias:** MIG-002, SEC-001, TOOL-001, TOOL-002 (es el último paso de la Ola 0)

**Criterios de aceptación**

- [ ] `git status` queda limpio salvo cambios reales
- [ ] Un clon nuevo trae los 65 endpoints y los cuatro documentos
- [ ] Existe `.gitattributes` con `* text=auto eol=lf`
- [ ] `python scripts/verificar_documentacion.py` se ejecuta desde un clon nuevo

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TEST-004 — Tests de vacantes y portal público

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | CRITICA | TEST | Vacantes | PA-02 / CU-08, CU-09 |

**Descripción.** Los 8 endpoints de vacantes y portal público existen y no tienen una sola
prueba. Hay que cubrir los casos que el propio perfil declara.

**Dependencias:** TOOL-001, TOOL-002 · **Endpoints:** API-P01 … API-P08

**Criterios de aceptación**

- [ ] `CP01` — `POST /vacantes` con datos válidos → 201, y la vacante aparece en el portal
- [ ] `CP02` — campos obligatorios vacíos → 422 con el detalle
- [ ] `CP03` — `fecha_cierre` anterior a hoy → error de validación
- [ ] `CP-S1-08` — el portal responde 200 sin token y muestra la marca de la empresa
- [ ] `CP-S1-09` — slug inexistente → 404 genérico, sin revelar información
- [ ] `CP-S1-10` — vacante con `fecha_cierre` vencida **no** aparece en el portal
- [ ] `CP-S1-11` — con `mostrar_salario` desactivado el detalle no expone el rango
- [ ] aislamiento — la empresa A no ve ni edita vacantes de la B (404)
- [ ] el test de aislamiento **falla** si alguien quita el filtro del repositorio

**Tests requeridos:** API · Unit

**Referencia:** `tests/unit/test_roles.py` para el estilo · el repositorio a probar es
`vacantes/infrastructure/persistence/repositories/vacante_repository.py` y sus condiciones
públicas están en `_public_conditions`.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TEST-005 — Tests del tablero, etapas y motivos de rechazo

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | CRITICA | TEST | Tablero | PA-03 / CU-12 |

**Descripción.** Los 5 endpoints del tablero existen sin pruebas. **Esta es la tarea que
cierra `BUG-001`:** el reporte del perfil marca `CP-S1-21` como FALLA (05/09/2026) y el
código nuevo **sí** responde 404 (`tablero_router.py:118-120`), pero nadie lo probó y nada
impide que el próximo cambio lo rompa.

**Dependencias:** TOOL-001, TOOL-002 · **Endpoints:** API-P11 … API-P16

**Criterios de aceptación**

- [ ] `CP-S1-19` — mover de etapa cambia la columna **y** escribe un evento en la bitácora
- [ ] `CP-S1-20` — rechazar sin motivo → 400
- [ ] `CP-S1-21` — la empresa B recibe **404** (no 403) al pedir el tablero de la A
- [ ] el motivo de rechazo debe pertenecer al catálogo de la empresa
- [ ] el tablero agrupa por etapa según `orden`, con contador por columna
- [ ] sin el permiso `postulaciones:ver` → 403
- [ ] el test de `CP-S1-21` **falla** si alguien quita el filtro por empresa

**Tests requeridos:** API · Integration

**DECISIÓN PENDIENTE.** La máquina de estados de las etapas: ¿se puede mover una
postulación hacia atrás? El código actual permite cualquier transición. Hay que decidirlo
antes de escribir el caso.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TEST-006 — Test de permisos de los roles base

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | CRITICA | TEST | Empresas | PA-01 / CU-01, CU-05 |

**Descripción.** El fallo de `SEC-001` —un rol base con cero permisos— es silencioso y
pudo entrar porque **nada lo verifica**. Este test es la red que impide que vuelva a pasar
cada vez que se agregue un permiso nuevo.

**Dependencias:** SEC-001 · **Endpoints:** —

**Criterios de aceptación**

- [ ] Falla si algún rol base declarado con permisos queda con cero
- [ ] Falla si `ROLE_DEFINITIONS` cita un código que no existe en el catálogo
- [ ] Falla si un rol de empresa recibe un permiso `platform:`
- [ ] RECLUTADOR queda con al menos los permisos de vacantes y postulaciones

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK ARCH-001 — Extraer el repositorio del tablero fuera del router

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | REFACTOR | Tablero | PA-03 / CU-12 |

**Descripción.** `tablero_router.py` hace **8 llamadas directas a `session.execute` /
`session.scalar` y no usa ningún repositorio**. Contradice dos reglas del propio proyecto:

> *«La lógica de negocio no vive en los routers.»*
> *«Todo repositorio de un recurso de empresa filtra por `empresa_id`. **En el repositorio,
> no en el router.**»* — regla 7 de `01_ESTADO_PROYECTO.md`

Hoy funciona. El problema es que el filtro de empresa es lo único que separa los datos de
dos clientes, y está en la capa donde es más fácil olvidarlo en el próximo endpoint.

**Dependencias:** TEST-005 · **Endpoints:** API-P11 … API-P16

**Reglas de negocio**

- El contrato HTTP de los 5 endpoints **no cambia**: mismas rutas, mismos códigos, mismos cuerpos
- Cada repositorio hereda de su puerto
- Patrón a copiar: el módulo `src/ssas/cargos/` completo

**Criterios de aceptación**

- [ ] Cero `session.execute` / `session.scalar` en `tablero_router.py`
- [ ] El filtro por `empresa_id` vive en el repositorio
- [ ] `TEST-005` sigue en verde **sin modificar los tests**

**Tests requeridos:** los de `TEST-005`, sin tocarlos

**Riesgos.** No iniciarla antes de que `TEST-005` esté en verde: esos tests son la única
red que garantiza que el contrato no cambie.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TAB-004 — Seed de etapas base al aprovisionar una empresa

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | USE_CASE | Tablero | PA-03 / CU-12 |

**Descripción.** `provision_empresa.py` no menciona `etapa` **ni una vez**. Una empresa
nueva nace **sin etapas de reclutamiento**, así que su tablero arranca vacío y
`PATCH /postulaciones/{id}/etapa` responde 404 para cualquier etapa. El perfil precarga
**siete etapas por defecto** (tarea T1-03 del sprint). El seed va donde ya se siembran los
roles base.

**Dependencias:** SEC-001 · **Endpoints:** API-P15

**Criterios de aceptación**

- [ ] Una empresa nueva nace con sus siete etapas base
- [ ] Exactamente una tiene `es_inicial`, una `es_contratado` y una `es_rechazado`
- [ ] El campo `orden` es único y consecutivo dentro de la empresa
- [ ] `GET /api/v1/etapas-reclutamiento` devuelve esas siete tras aprovisionar
- [ ] El seed es idempotente: aprovisionar dos veces no duplica etapas

**Tests requeridos:** Unit · Integration

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK AUTH-001 — Autenticación y sesión

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | CRITICA | API | Auth | PA-01 / CU-03 |

**Descripción.** Login único con y sin `empresa_slug`, refresh con rotación, logout con revocación, verificación de correo, recuperación de contraseña y bloqueo por intentos fallidos.

**Dependencias:** ninguna  
**Endpoints:** API-001, API-002, API-003, API-004, API-005, API-006, API-007, API-008, API-009 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- Login único para plataforma y empresa; el token lleva el alcance

**Criterios de aceptación**

- [ ] 9 endpoints responden según el contrato de 02
- [ ] 5 archivos de test cubren el módulo

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK BUG-001 — Corregir el aislamiento multi-tenant del tablero de candidatos

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | CRITICA | BUG | Tablero | PA-03 / CU-12 |

**Descripción.** El propio reporte de pruebas del perfil marca **CP-S1-21 como FALLA** (05/09/2026): «Usuario autenticado de la empresa B solicita el tablero de una vacante de la empresa A → no responde 404». Es un fallo de aislamiento entre empresas documentado y sin resolver, y es exactamente lo que evalúa la pregunta 3.d del examen final.

**Dependencias:** ninguna  
**Endpoints:** API-P11 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Reproducir el caso con dos empresas reales
- [ ] Filtrar por empresa_id en el repositorio, no en el router
- [ ] Test de regresión

**Reglas de negocio**

- Responder **404 y no 403**: un 403 confirmaría que esa vacante existe
- El filtro va en el repositorio; ningún router debe poder saltearlo

**Criterios de aceptación**

- [ ] CP-S1-21 pasa: la empresa B recibe 404 al pedir el tablero de la empresa A
- [ ] Existe un test automatizado que falla si alguien quita el filtro
- [ ] El reporte de pruebas del perfil se actualiza de FALLA a OK

**Tests requeridos:** Integration · API

**Riesgos.** Mientras no se corrija, el sistema filtra datos entre empresas. Es la tarea más urgente del backlog.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK INFRA-001 — Separar la base de pruebas de la de producción

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| BLOQUEADO | CRITICA | ARCHITECTURE | Infraestructura | — |

**Descripción.** Local, Railway y las pruebas apuntan a la misma base de Supabase. Un `alembic upgrade`, un seed o un `pytest` distraído impacta producción.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Base de pruebas separada (local o proyecto Supabase aparte)
- [x] `.env.test.example` documentado y selector `SETTINGS_ENV_FILE` disponible
- [ ] CI que use esa base

**Reglas de negocio**

- El freno de los tests e2e no se quita: se complementa con una base propia

**Criterios de aceptación**

- [ ] Existe una `DATABASE_URL` de pruebas distinta de la de producción
- [ ] `pytest` corre la suite completa sin saltear los e2e
- [ ] La documentación indica cuál usar en cada caso

**Tests requeridos:** Integration

**Riesgos.** Mientras no se resuelva, cualquier tarea que toque la base puede destruir datos reales.

**Bloqueo actual (2026-09-07).** Se implementó la selección segura de `.env.test`, pero no
existe todavía una base de pruebas provisionada ni credenciales/CI separados. No se ejecutan
migraciones ni pruebas de integración hasta recibir una `DATABASE_URL` de test distinta.

**Archivos modificados:** `.env.example`, `.env.test.example`, `.gitignore`,
`src/ssas/config/settings.py`, `tests/integration/test_database_connection.py`.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TEST-001 — Tests de aislamiento entre empresas

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | CRITICA | TEST | Transversal | PA-01 |

**Descripción.** 6 de los 9 módulos con endpoints no tienen ningún test. El aislamiento entre empresas —lo que la materia evalúa en la pregunta 3.d— no está verificado para departamentos, cargos, empresas ni postulaciones.

**Dependencias:** INFRA-001  
**Endpoints:** API-010..API-046 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Fixture con dos empresas reales
- [ ] Un test por módulo: A no ve datos de B

**Reglas de negocio**

- Cada endpoint de alcance empresa debe probar que un actor de la empresa A no alcanza datos de la B

**Criterios de aceptación**

- [ ] Un usuario de la empresa A recibe 403/404 al pedir recursos de la B en cada módulo
- [ ] El super administrador sí accede a ambas por el mismo endpoint
- [ ] La suite pasa en verde

**Tests requeridos:** Integration · API

**Riesgos.** Sin INFRA-001, estos tests no se pueden correr sin borrar producción.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK EMP-001 — Empresas y aprovisionamiento

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | ALTA | API | Empresas | PA-01 / CU-01, CU-02 |

**Descripción.** Alta de empresas con sus roles base y administrador inicial, suspensión, reactivación, borrado lógico y restauración.

**Dependencias:** ROL-001  
**Endpoints:** API-026, API-027, API-028, API-029, API-030, API-031, API-032, API-033 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- Operaciones exclusivas de plataforma: `require_platform_permission`

**Criterios de aceptación**

- [ ] 8 endpoints implementados
- [ ] Validación pendiente: ver TEST-003

**Tests requeridos:** API

**Riesgos.** Sin tests propios: el aprovisionamiento es el flujo más complejo del sistema.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK PERF-001 — Alinear el perfil del proyecto con el código

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | DOCUMENTATION | Documentación | — |

**Descripción.** El perfil (`Perfil_Proyecto_RRHH_Grupo12.docx`) tiene tres desviaciones respecto del código, y una de ellas rompe la trazabilidad que evalúa la materia.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Unificar la numeración de CU
- [ ] Actualizar el diseño de datos del Sprint 1
- [ ] Actualizar el reporte de CP-S1-21

**Reglas de negocio**

- La numeración de CU debe ser única en todo el documento

**Criterios de aceptación**

- [ ] §3.10.2 y el Capítulo 4 usan los mismos IDs para los mismos casos de uso
- [ ] El script SQL del Sprint 1 ya no incluye `plan_suscripcion` ni `suscripcion`, o el código las reincorpora
- [ ] CP-S1-21 figura como OK con su evidencia

**Tests requeridos:** Documentation

**Riesgos.** La numeración incoherente de CU es el defecto que la docente detecta primero: impide verificar qué se entregó.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK POR-001 — Portal público de empleos

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | API | Portal | PA-02 / CU-09 |

**Descripción.** Listado y detalle de vacantes publicadas por empresa, sin autenticación, en `/publico/{empresa_slug}/vacantes`. Corresponde a **T-09** (HU-04). Hoy solo existe `/publico/postulaciones`.

**Dependencias:** VAC-003  
**Endpoints:** API-P07, API-P08 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Schema de salida reducido
- [ ] Router público
- [ ] Alta en `PUBLIC_PATHS` del middleware
- [ ] Filtros por ciudad y modalidad

**Reglas de negocio**

- Solo vacantes publicadas y con fecha de cierre vigente (paso 4 del plan CU-09)
- Respetar `mostrar_salario`: si está desactivado, no exponer el rango salarial (paso 3)
- Un slug inexistente responde **404 con mensaje genérico**, sin revelar información (paso 5)
- No exponer `empresa_id` crudo ni campos de gestión

**Criterios de aceptación**

- [ ] GET /publico/{slug}/vacantes responde 200 sin token y muestra la marca de la empresa
- [ ] Los filtros de ciudad y modalidad reducen la lista
- [ ] Una vacante con fecha de cierre vencida no aparece
- [ ] Un slug inexistente responde 404 genérico
- [ ] El detalle oculta el salario cuando `mostrar_salario` está desactivado

**Tests requeridos:** API

**Riesgos.** Superficie pública sin autenticación: revisar límite de tasa y qué campos se exponen.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK POS-001 — Postulación pública

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | ALTA | API | Postulaciones | PA-02 / CU-09, CU-12 |

**Descripción.** Un candidato se postula sin cuenta y consulta el estado con un código de seguimiento.

**Dependencias:** ninguna  
**Endpoints:** API-044, API-045 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- Endpoint público: declarado en `PUBLIC_PATHS` del middleware
- El código de seguimiento evita exponer identificadores internos

**Criterios de aceptación**

- [ ] 2 endpoints públicos implementados
- [ ] Falta la gestión interna: ver POS-003

**Tests requeridos:** API

**Riesgos.** Superficie pública sin autenticación: revisar límites de tasa.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK ROL-001 — Roles y permisos

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | ALTA | API | Roles | PA-01 / CU-05 |

**Descripción.** CRUD de roles y asignación de permisos. Catálogo de 28 permisos, 8 de ellos con prefijo `platform:`.

**Dependencias:** USR-001  
**Endpoints:** API-020, API-021, API-022, API-023, API-024, API-025 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- Un rol de empresa nunca recibe permisos `platform:*`

**Criterios de aceptación**

- [ ] 6 endpoints implementados
- [ ] 2 archivos de test cubren el módulo

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TAB-001 — Catálogos de etapas y motivos de rechazo

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | API | Tablero | PA-03 / CU-12 |

**Descripción.** Las tablas `etapa_reclutamiento` y `motivo_rechazo` están migradas y sin uso. El tablero las necesita para agrupar columnas y para exigir motivo al rechazar.

**Dependencias:** ninguna  
**Endpoints:** API-P15, API-P16 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Repositorios
- [ ] Casos de uso de consulta
- [ ] Endpoints de solo lectura
- [ ] Seed de etapas base por empresa

**Reglas de negocio**

- Ambos catálogos son por empresa (`empresa_id`)
- Al aprovisionar una empresa se siembran sus etapas base

**Criterios de aceptación**

- [ ] GET /api/v1/etapas-reclutamiento devuelve las etapas de la empresa del token, ordenadas
- [ ] Una empresa nueva nace con sus etapas base sembradas

**Tests requeridos:** API

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TAB-002 — Tablero de candidatos por etapas

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | API | Tablero | PA-03 / CU-12 |

**Descripción.** Vista Kanban de las postulaciones de una vacante, agrupadas por etapa y con contador por columna. Corresponde a **T-12** (HU-06).

**Dependencias:** TAB-001, VAC-003, BUG-001  
**Endpoints:** API-P11, API-P12 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Caso de uso de agrupación
- [ ] Endpoint del tablero
- [ ] Listado interno de postulaciones

**Reglas de negocio**

- Agrupa por etapa según su orden, con contador por columna
- Filtra por `empresa_id` en el repositorio

**Criterios de aceptación**

- [ ] GET /api/v1/vacantes/{id}/tablero agrupa por etapa con contador
- [ ] Un usuario de otra empresa recibe 404 (CP-S1-21)
- [ ] Responde 403 sin el permiso

**Tests requeridos:** API

**Riesgos.** Depende de BUG-001: no cerrar esta tarea sin el test de aislamiento en verde.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TAB-003 — Mover de etapa y rechazar con motivo

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | API | Tablero | PA-03 / CU-12 |

**Descripción.** Acciones del tablero: cambiar la etapa de una postulación y rechazarla exigiendo un motivo del catálogo (T-12 / HU-06).

**Dependencias:** TAB-002  
**Endpoints:** API-P13, API-P14 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Casos de uso
- [ ] Endpoints PATCH
- [ ] Registro en bitácora

**Reglas de negocio**

- **Cada cambio de etapa queda registrado en la bitácora** (criterio del perfil)
- Rechazar **exige** un motivo del catálogo: sin él, 400
- Las transiciones válidas entre etapas son `DECISIÓN PENDIENTE`

**Criterios de aceptación**

- [ ] Mover de etapa cambia la columna y escribe un evento en la bitácora (CP-S1-19)
- [ ] Rechazar sin motivo responde 400 (CP-S1-20)
- [ ] Un usuario de otra empresa recibe 404 (CP-S1-21)

**Tests requeridos:** API

**Riesgos.** La máquina de estados de las etapas no está definida: acordarla antes de implementar.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TEST-002 — Tests de departamentos y cargos

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | TEST | Organización | PA-04 / CU-19 |

**Descripción.** Ambos módulos tienen 4 endpoints cada uno y cero tests.

**Dependencias:** INFRA-001  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Unit de casos de uso
- [ ] API
- [ ] Aislamiento entre empresas

**Reglas de negocio**

- Todo endpoint de empresa prueba el aislamiento

**Criterios de aceptación**

- [ ] Éxito, 401, 403 y aislamiento cubiertos en los 8 endpoints

**Tests requeridos:** Unit · API

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK TEST-003 — Tests de empresas (platform)

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | TEST | Empresas | PA-01 / CU-01 |

**Descripción.** 8 endpoints de plataforma sin tests, incluido el aprovisionamiento de empresas.

**Dependencias:** INFRA-001  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] API
- [ ] Verificar que un admin de empresa recibe 403

**Reglas de negocio**

- Ningún actor de empresa alcanza los endpoints de plataforma

**Criterios de aceptación**

- [ ] Aprovisionar una empresa crea sus roles base y su administrador
- [ ] Un ADMIN_EMPRESA recibe 403 en todos los endpoints `/empresas`

**Tests requeridos:** API

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK USR-001 — Gestión de usuarios

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | ALTA | API | Usuarios | PA-01 / CU-04 |

**Descripción.** CRUD de usuarios con borrado lógico, restauración, activación, desbloqueo y cambio de contraseña. Guard de doble alcance empresa/plataforma.

**Dependencias:** AUTH-001  
**Endpoints:** API-010, API-011, API-012, API-013, API-014, API-015, API-016, API-017, API-018, API-019 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- `empresa_id` sale del token, no del cuerpo

**Criterios de aceptación**

- [ ] 10 endpoints implementados
- [ ] Validación pendiente: ver TEST-001

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK VAC-001 — Repositorio de vacantes

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | REPOSITORY | Vacantes | PA-02 / CU-08 |

**Descripción.** Los modelos `vacante` y `vacante_habilidad` están migrados pero no hay forma de leerlos ni escribirlos. Corresponde a la tarea **T-08** del cronograma (HU-03).

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Puerto `VacanteRepository`
- [ ] Adaptador `SqlAlchemyVacanteRepository`
- [ ] Entidad de dominio

**Reglas de negocio**

- Todas las consultas filtran por `empresa_id` dentro del repositorio

**Criterios de aceptación**

- [ ] `listar(empresa_id)` devuelve solo vacantes de esa empresa
- [ ] Ninguna consulta del repositorio omite el filtro de empresa

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK VAC-002 — Casos de uso de vacantes

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | USE_CASE | Vacantes | PA-02 / CU-08 |

**Descripción.** CRUD y publicación de vacantes (T-08 / HU-03).

**Dependencias:** VAC-001  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] ListarVacantes
- [ ] CrearVacante
- [ ] ObtenerVacante
- [ ] ActualizarVacante
- [ ] PublicarVacante
- [ ] EliminarVacante

**Reglas de negocio**

- `empresa_id` lo fija quien llama, nunca viene del cuerpo
- La fecha de cierre debe ser igual o posterior a hoy (CP02/CP03 del perfil)
- Una vacante de otra empresa se responde como inexistente

**Criterios de aceptación**

- [ ] Publicar con la fecha de cierre vencida devuelve un error de validación
- [ ] Publicar sin campos obligatorios devuelve 422 con el detalle
- [ ] Crear una vacante en otra empresa es imposible manipulando el JSON

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK VAC-003 — Endpoints de vacantes

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | API | Vacantes | PA-02 / CU-08 |

**Descripción.** Exponer el CRUD y la publicación siguiendo el patrón de `cargos` y `departamentos` (T-08 / HU-03).

**Dependencias:** VAC-002, VAC-004  
**Endpoints:** API-P01, API-P02, API-P03, API-P04, API-P05, API-P06 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Schemas
- [ ] Router
- [ ] Guard `require_scoped_permission`
- [ ] Manejo de errores

**Reglas de negocio**

- `require_scoped_permission('vacantes:X', 'platform:organizacion:gestionar')`
- La lógica de negocio no vive en el router

**Criterios de aceptación**

- [ ] POST /api/v1/vacantes responde 201 con datos válidos (CP01 del perfil)
- [ ] Responde 401 sin token y 403 sin permiso
- [ ] Un admin de la empresa A no ve vacantes de la B
- [ ] El response coincide con el contrato de 02_API_ENDPOINTS.md

**Tests requeridos:** API

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK VAC-004 — Permisos `vacantes:*` en el catálogo

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | ALTA | SECURITY | Vacantes | PA-02 / CU-08 |

**Descripción.** El catálogo tiene 28 permisos y ninguno de vacantes. Sin ellos los endpoints no se pueden proteger.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Migración con `vacantes:ver|crear|editar|publicar|eliminar`
- [ ] Asignarlos al rol base ADMIN_EMPRESA

**Reglas de negocio**

- Los permisos de empresa nunca llevan prefijo `platform:`
- La migración es idempotente

**Criterios de aceptación**

- [ ] Los 5 permisos existen tras `alembic upgrade head`
- [ ] ADMIN_EMPRESA los recibe al aprovisionar una empresa nueva

**Tests requeridos:** Integration

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK BIT-001 — Bitácora de auditoría

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | MEDIA | API | Bitácora | PA-01 / CU-06 |

**Descripción.** Consulta de la auditoría de empresa y de plataforma sobre una sola tabla, separadas por `empresa_id IS NULL`.

**Dependencias:** USR-001  
**Endpoints:** API-034, API-035 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- Información sensible: exige permiso explícito, no solo autenticación

**Criterios de aceptación**

- [ ] 2 endpoints implementados
- [ ] 1 archivo de test

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK CAR-001 — Cargos

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | MEDIA | API | Cargos | PA-04 / CU-19 |

**Descripción.** CRUD de cargos, asociados a departamentos.

**Dependencias:** DEP-001  
**Endpoints:** API-040, API-041, API-042, API-043 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- Filtrado por empresa en el repositorio

**Criterios de aceptación**

- [ ] 4 endpoints implementados
- [ ] Validación pendiente: ver TEST-002

**Tests requeridos:** API

**Riesgos.** Sin tests.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK DEP-001 — Departamentos

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | MEDIA | API | Departamentos | PA-04 / CU-19 |

**Descripción.** CRUD de la estructura organizativa de la empresa.

**Dependencias:** EMP-001  
**Endpoints:** API-036, API-037, API-038, API-039 → ver `02_API_ENDPOINTS.md`

**Reglas de negocio**

- Filtrado por empresa en el repositorio

**Criterios de aceptación**

- [ ] 4 endpoints implementados
- [ ] Validación pendiente: ver TEST-002

**Tests requeridos:** API

**Riesgos.** Sin tests.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK DOC-001 — Retirar el esquema SQL escrito a mano

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | MEDIA | DOCUMENTATION | Documentación | — |

**Descripción.** `docs/database/schema_sprint0_sprint1.sql` es una segunda fuente de verdad del esquema que compite con Alembic y se desincroniza sin aviso.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Verificar si coincide con el esquema real
- [ ] Reemplazarlo por un volcado generado o archivarlo

**Reglas de negocio**

- El esquema real lo define Alembic, no un .sql a mano

**Criterios de aceptación**

- [ ] O el archivo se genera automáticamente, o queda archivado con nota de obsolescencia

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK HAB-001 — Capa de aplicación de habilidades

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | MEDIA | USE_CASE | Habilidades | PA-02 / apoyo CU-08 |

**Descripción.** El modelo `habilidad` y la relación `vacante_habilidad` existen sin repositorio ni casos de uso.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Repositorio
- [ ] Casos de uso de catálogo

**Reglas de negocio**

- DECISIÓN PENDIENTE: ¿el catálogo es global o por empresa? Verificar el modelo antes de implementar

**Criterios de aceptación**

- [ ] El catálogo se puede listar y mantener
- [ ] La decisión de alcance queda documentada

**Tests requeridos:** Unit

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK MIG-001 — Normalizar la numeración de migraciones

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | MEDIA | REFACTOR | Infraestructura | — |

**Descripción.** Hay dos migraciones `0002` y dos con hash autogenerado. Alembic funciona por `down_revision`, pero el nombre confunde a quien lee el historial.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Renombrar archivos manteniendo los `revision` intactos

**Reglas de negocio**

- **No cambiar los identificadores `revision` ni `down_revision`**: rompería las bases ya migradas
- Solo se renombra el archivo

**Criterios de aceptación**

- [ ] Los nombres siguen `AAAAMMDD_NNNN_descripcion.py` sin duplicados
- [ ] `alembic upgrade head` sigue funcionando sobre una base ya migrada
- [ ] `alembic history` muestra la cadena completa

**Tests requeridos:** Integration

**Riesgos.** Renombrar mal deja bases existentes sin poder migrar.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK NOT-001 — Servicio de notificaciones y cola asíncrona

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| BLOQUEADO | MEDIA | INTEGRATION | Notificaciones | PA-02 / CU-35 |

**Descripción.** Corresponde a **T-13** del cronograma. **No existe nada en el código**: ni Celery, ni Redis, ni broker, ni servicio de notificaciones. El perfil exige notificar al candidato el avance de su proceso (RF-29, relación «include» de PA-02).

**Dependencias:** POR-001  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Elegir broker
- [ ] Tareas asíncronas de envío
- [ ] Plantillas de correo
- [ ] Reintentos y registro en bitácora

**Reglas de negocio**

- El envío no puede bloquear la petición HTTP
- Un fallo de envío no debe revertir la operación de negocio

**Criterios de aceptación**

- [ ] Postular dispara una notificación al candidato sin bloquear la respuesta
- [ ] Un cambio de etapa dispara la notificación correspondiente
- [ ] Los fallos de envío quedan registrados y se reintentan

**Tests requeridos:** Integration

**Riesgos.** BLOQUEADO: Railway no tiene worker ni broker aprovisionado. Es una DECISIÓN PENDIENTE de infraestructura y costo.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK PTE-001 — Repositorio y casos de uso de postulantes

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | MEDIA | REPOSITORY | Postulantes | PA-02 / CU-11 |

**Descripción.** El modelo `postulante` existe con `cv_url` pero sin capa de aplicación. Es el banco de talentos.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Puerto y adaptador
- [ ] Casos de uso de consulta

**Reglas de negocio**

- DECISIÓN PENDIENTE: un postulante llega del portal público sin empresa. Definir si `empresa_id` es nullable o si la relación es a través de la postulación

**Criterios de aceptación**

- [ ] Listar y obtener postulantes de la empresa funciona
- [ ] La decisión de alcance queda escrita

**Tests requeridos:** Unit

**Riesgos.** El modelo del postulante frente a la multitenencia no está resuelto.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK PTE-003 — Endpoints de postulantes

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | MEDIA | API | Postulantes | PA-02 / CU-11 |

**Descripción.** Consulta del banco de talentos.

**Dependencias:** PTE-001  
**Endpoints:** API-P09, API-P10 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Schemas
- [ ] Router
- [ ] Permisos `postulantes:*`

**Reglas de negocio**

- Datos personales: exponer lo mínimo necesario

**Criterios de aceptación**

- [ ] GET /api/v1/postulantes responde 200 con permiso y 403 sin él
- [ ] Un reclutador de la empresa A no ve postulantes exclusivos de la B

**Tests requeridos:** API

**Riesgos.** Contiene datos personales.

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK SYS-001 — Healthcheck

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| IMPLEMENTADO | MEDIA | API | Sistema | — |

**Descripción.** `GET /health` para el healthcheck de Railway. No consulta la base a propósito: si lo hiciera, una caída de PostgreSQL reiniciaría el contenedor.

**Dependencias:** ninguna  
**Endpoints:** API-046 → ver `02_API_ENDPOINTS.md`

**Criterios de aceptación**

- [ ] Responde 200 sin tocar la base de datos

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK DOC-002 — Regenerar la colección Postman desde el OpenAPI

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | BAJA | DOCUMENTATION | Documentación | — |

**Descripción.** La colección se llama `SSAH_RRHH` (nombre anterior al rename) y se mantiene a mano.

**Dependencias:** ninguna  
**Endpoints:** — → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Generarla desde /openapi.json
- [ ] Renombrar a SSAS

**Criterios de aceptación**

- [ ] La colección cubre los 46 endpoints y su nombre coincide con el proyecto

**Al terminar:** archivos modificados · resultado · fecha · agente

---

### TASK HAB-003 — Endpoints de habilidades

| Estado | Prioridad | Tipo | Módulo | PA / CU |
|---|---|---|---|---|
| PENDIENTE | BAJA | API | Habilidades | PA-02 / apoyo CU-08 |

**Descripción.** Exponer el catálogo para asociarlo a vacantes.

**Dependencias:** HAB-001  
**Endpoints:** API-P17, API-P18 → ver `02_API_ENDPOINTS.md`

**Componentes**

- [ ] Schemas
- [ ] Router
- [ ] Permisos

**Reglas de negocio**

- Coherente con la decisión de alcance de HAB-001

**Criterios de aceptación**

- [ ] GET /api/v1/habilidades responde 200
- [ ] Una vacante puede referenciar habilidades existentes

**Tests requeridos:** API

**Al terminar:** archivos modificados · resultado · fecha · agente

---

```text
==================================================
PROTOCOLO PARA AGENTES
==================================================

ANTES DE TRABAJAR
 1. git fetch y confirmar que trabajás sobre el HEAD actual.
 2. Leer docs/01_ESTADO_PROYECTO.md.
 3. Leer la TASK asignada completa.
 4. Leer el endpoint relacionado en docs/02_API_ENDPOINTS.md.
 5. Revisar solo el módulo afectado y sus dependencias.
 6. Verificar a que base apunta DATABASE_URL antes de cualquier comando que escriba.

DURANTE
 7. Respetar la arquitectura y las convenciones documentadas.
 8. Implementar solo el alcance de la TASK.
 9. No modificar arquitectura sin autorizacion explicita.
10. No romper endpoints existentes ni duplicar funcionalidad.
11. Todo endpoint de empresa filtra por empresa_id EN EL REPOSITORIO.
12. Ningun rol de empresa recibe permisos platform:*.

DESPUES
13. pytest
14. ruff check src tests
15. python scripts/verificar_documentacion.py
16. Actualizar 02_API_ENDPOINTS.md (estado del endpoint).
17. Actualizar 03_BACKLOG_IMPLEMENTACION.md (estado, archivos, resultado).
18. Actualizar 01_ESTADO_PROYECTO.md si cambio el estado de un area.
19. No modificar tareas ajenas ni reformatear archivos completos.
==================================================
```

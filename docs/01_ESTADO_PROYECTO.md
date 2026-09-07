# 01 — ESTADO DEL PROYECTO

> **Este es el primer documento que debe leer cualquier agente.**
> Sincronizado el **2026-09-07** contra el commit `782ac60`.
> Verificar con `python scripts/verificar_documentacion.py` antes de confiar en él.

---

## 1. Información general

| | |
|---|---|
| Proyecto | **backend_ssas_rrhh** — Sistema de Gestión de RRHH, SaaS multi-tenant |
| Materia | Sistemas de Información 2 (INF 412-SA) · UAGRM · Grupo N.° 12 |
| Lenguaje | Python 3.12 |
| Framework | FastAPI |
| Base de datos | PostgreSQL sobre **Supabase** · 19 tablas |
| ORM | SQLAlchemy 2.0 async (`psycopg`) |
| Migraciones | Alembic |
| Paquete | `src/ssas/` |
| Prefijo de API | `/api/v1` |
| Arquitectura | Vertical Slicing + Hexagonal pragmática |
| Despliegue | Railway (`railway.json`) |

```bash
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn ssas.main:app --app-dir src --reload   #  /docs
pytest && ruff check src tests
```

---

## 2. Estado por área

| Área | Estado | PA | Endpoints | Tests | Observaciones |
|---|---|---|---|---|---|
| Arquitectura | IMPLEMENTADO | — | — | 2 | Vertical slicing + hexagonal; `core/` transversal |
| Base de datos | IMPLEMENTADO | — | — | 3 | **19 tablas** · Supabase compartida entre local y Railway |
| Migraciones | PARCIAL | — | — | 1 | 7 migraciones con **numeración inconsistente**: dos `0002` y dos con hash |
| Auth | IMPLEMENTADO | PA-01 | 9 | 5 | JWT access+refresh con rotación, verificación de correo, bloqueo por intentos |
| Usuarios | IMPLEMENTADO | PA-01 | 10 | 2 | CRUD + borrado lógico + restaurar + desbloquear |
| Roles y permisos | IMPLEMENTADO | PA-01 | 6 | 2 | 28 permisos en catálogo; asignación por rol |
| Empresas / Tenants | IMPLEMENTADO | PA-01 | 8 | 0 | **Sin tests propios** |
| Multitenencia | IMPLEMENTADO | PA-01 | — | 0 | Tenant implícito en el token; guards de doble alcance |
| Bitácora | IMPLEMENTADO | PA-01 | 2 | 1 | Auditoría de empresa y de plataforma en una sola tabla |
| Departamentos | IMPLEMENTADO | PA-04 | 4 | 0 | **Sin tests** |
| Cargos | IMPLEMENTADO | PA-04 | 4 | 0 | **Sin tests** |
| Vacantes | PENDIENTE | PA-02 | 0 | 0 | CU-08 · T-08. Modelos migrados; **sin repositorio, casos de uso ni endpoints** |
| Postulantes | PARCIAL | PA-02 | 0 | 0 | CU-11. Modelo con `cv_url`; **sin capa de aplicación ni HTTP** |
| Habilidades | PENDIENTE | PA-02 | 0 | 0 | Apoyo de CU-08. Modelo y relación `vacante_habilidad` migrados, sin uso |
| Portal público | PENDIENTE | PA-02 | 0 | 0 | CU-09 · T-09. Falta `/publico/{empresa_slug}/vacantes` |
| Postulaciones | PARCIAL | PA-02 | 2 | 0 | CU-10 y CU-11. Postular con CV y consultar por código **sí** funcionan; falta la gestión interna |
| Tablero de candidatos | PENDIENTE | PA-03 | 0 | 0 | CU-12 · T-12. `etapa_reclutamiento` y `motivo_rechazo` migradas, sin uso. **CP-S1-21 marcado FALLA** |
| Notificaciones | PENDIENTE | PA-02 | 0 | 0 | T-13. **No existe nada**: ni Celery, ni broker, ni servicio de envío |
| Administración de Personal | PENDIENTE | PA-04 | 0 | 0 | Solo la estructura organizativa (departamentos, cargos) |
| Capacitación | PENDIENTE | PA-05 | 0 | 0 | No iniciado |
| Inteligencia Artificial | PENDIENTE | PA-06 | 0 | 0 | No iniciado |
| Reportes e Indicadores | PENDIENTE | PA-07 | 0 | 0 | No iniciado |
| Tests | PARCIAL | — | — | 10 | 10 archivos; **6 de 9 módulos con endpoints no tienen tests** |
| Documentación | PARCIAL | — | — | — | Este sistema de control; docs previos parcialmente desactualizados |

**Resumen:** 46 endpoints implementados en 8 módulos · 4 áreas PARCIAL · 5 PENDIENTE.

---

## 2 bis. Alcance del Sprint 1 y su estado real

Según el Capítulo 4 del perfil, el Sprint 1 entrega *«el primer flujo completo de valor:
publicar una vacante, exponerla en un portal público, permitir la postulación con carga de
hoja de vida desde web y móvil, y visualizar a los postulantes en el tablero»*.

| CU | Caso de uso | Tarea | HU | Backend | Qué falta |
|---|---|---|---|---|---|
| CU-07 | Gestionar departamentos y cargos | T-07 | HU-02 | **IMPLEMENTADO** | Tests (`TEST-002`) |
| CU-08 | Gestionar vacantes | T-08 | HU-03 | **PENDIENTE** | Repositorio, casos de uso, endpoints y permisos → `VAC-001`…`VAC-004` |
| CU-09 | Explorar el portal público | T-09 | HU-04 | **PENDIENTE** | `/publico/{empresa_slug}/vacantes` → `POR-001` |
| CU-10 | Postular con hoja de vida | T-10 | HU-05 | **IMPLEMENTADO** | `POST /publico/postulaciones` acepta CV multipart. Falta validar tamaño/formato en tests |
| CU-11 | Consultar estado de la postulación | T-11 | HU-09 | **IMPLEMENTADO** | `GET /publico/postulaciones/{codigo}` |
| CU-12 | Gestionar tablero de candidatos | T-12 | HU-06 | **PENDIENTE** | Catálogos, tablero y acciones → `TAB-001`…`TAB-003`. **Con un fallo abierto: `BUG-001`** |
| — | Notificaciones y cola asíncrona | T-13 | — | **PENDIENTE** | No existe nada en el código → `NOT-001` (BLOQUEADO) |

**Balance:** de las 6 tareas de backend del Sprint 1, **3 están terminadas** (departamentos
y cargos, postulación con CV, consulta por código) y **3 no tienen una sola línea**
(vacantes, portal público, tablero). La T-13 tampoco.

> El flujo de valor prometido está **cortado en el medio**: se puede postular a una vacante
> que no se puede crear ni publicar, y no hay dónde ver a los postulantes.

## 2 ter. Verificación ejecutada — 2026-09-07

Resultado real de los comandos del protocolo, sobre el commit `782ac60`. **Cuatro de los
cinco están en rojo**, y eso bloquea a cualquier agente antes de que empiece.

| Comando | Resultado | Tarea |
|---|---|---|
| `APP_SECRET_KEY=x PYTHONPATH=src python -c "from ssas.main import app"` | **OK** — 46 operaciones (37 protegidas, 9 públicas) | — |
| `PYTHONPATH=src pytest -q` | **OK** — 39 passed, 3 skipped | — |
| `pytest -q` | **FALLA** — 8 errores: `ModuleNotFoundError: No module named 'ssas'` | `TOOL-001` |
| `ruff check src tests` | **FALLA** — 15 errores preexistentes (14 autocorregibles) | `TOOL-002` |
| `alembic upgrade head` | **FALLA** — `Multiple head revisions are present` | `MIG-002` |
| `alembic heads` | **DOS cabezas** — `20260825_0002` y `20260906_0004` | `MIG-002` |
| `python scripts/verificar_documentacion.py` | **NO SE PUEDE** — `scripts/` no está versionado | `DOC-003` |

Dos hallazgos más, verificados leyendo y ejecutando el código:

- **El rol RECLUTADOR se aprovisiona con 0 permisos.** `ROLE_DEFINITIONS` le asigna
  `vacantes:gestionar` y `candidatos:gestionar`; ninguno existe en el catálogo de 28, y el
  filtro descarta los códigos desconocidos sin avisar. El actor protagonista del Sprint 1
  no puede hacer nada, y el fallo es silencioso → `SEC-001` (CRÍTICA).
- **157 archivos de `src/` figuran como modificados por puro final de línea** (CRLF frente
  a LF). Normalizando los saltos, el árbol local y el de GitHub son idénticos byte a byte.
  Falta `.gitattributes` → `DOC-003`.

El plan de ejecución de todo esto está en
[`04_EJECUCION_MULTIAGENTE_SPRINT1.md`](04_EJECUCION_MULTIAGENTE_SPRINT1.md).

## 3. Arquitectura real

```text
src/ssas/
├── main.py                  FastAPI · CORS · middleware de tenant · router /api/v1
├── config/settings.py       24 variables, todas en uso
├── core/
│   ├── api/router.py        agrega los routers de cada módulo
│   ├── security/            JWT · hashing · dependencias de autorización
│   └── tenancy/             ContextVar del tenant + middleware
├── infrastructure/database/ Base declarativa única · sesión async
│
├── auth/                 PA-01 · 9 endpoints
├── usuarios/             PA-01 · 10 endpoints
├── roles/                PA-01 · 6 endpoints
├── platform/             PA-01 · 8 endpoints
├── bitacora/             PA-01 · 2 endpoints
├── departamentos/        PA-04 · 4 endpoints
├── cargos/               PA-04 · 4 endpoints
├── vacantes/             PA-02 · SIN endpoints
├── postulantes/          PA-02 · SIN endpoints
├── habilidades/          PA-02 · SIN endpoints
├── postulaciones/        PA-02 · 2 endpoints
```

Cada módulo repite la misma disposición interna:

```text
<modulo>/
├── domain/           entidades y excepciones · sin FastAPI, SQLAlchemy ni Pydantic
├── application/      casos de uso
├── ports/            contratos hacia dependencias externas
└── infrastructure/   http/ (router, schemas) · persistence/ (models, repositories)
```

---

## 4. Reglas que los agentes deben respetar

### Multitenencia — el invariante central

```text
usuario.empresa_id  IS NULL  ->  administrador de la plataforma
rol.empresa_id      IS NULL  ->  rol global (SUPER_ADMIN)
bitacora.empresa_id IS NULL  ->  evento de la plataforma
```

1. El tenant es **implícito en el token**, nunca viaja en la URL.
2. Login único `POST /api/v1/auth/login`: **con** `empresa_slug` para usuarios de
   empresa, **sin** él para administradores de plataforma.
3. Un rol de empresa **nunca** recibe permisos `platform:*`. Bloqueado en
   `AssignPermissions` y en `ProvisionEmpresa`.
4. `require_platform_permission` exige además `es_plataforma`: defensa en profundidad.
5. `SUPER_ADMIN` no tiene excepción codificada; sus permisos están en la base.
6. PostgreSQL trata dos `NULL` como distintos: los índices únicos de email, username,
   código y nombre de rol son **parciales** (`WHERE empresa_id IS NULL`).
7. Todo repositorio de un recurso de empresa filtra por `empresa_id`. **En el
   repositorio, no en el router.**

### Guards de autorización disponibles

| Guard | Uso | Endpoints |
|---|---|---|
| `require_scoped_permission(emp, plat)` | El actor de empresa usa el 1.º, el de plataforma el 2.º | 26 |
| `require_platform_permission(perm)` | Solo plataforma | 6 |
| `require_empresa_permission(emp, plat)` | Recurso de empresa accesible por plataforma | 2 |
| `get_authenticated_user` | Solo autenticación, sin permiso | 4 |
| — | Público, declarado en `PUBLIC_PATHS` del middleware | 8 |

### Arquitectura

- La lógica de negocio no vive en los routers.
- Entidad de dominio ≠ modelo ORM. Adaptadores: `SqlAlchemy<Cosa>Repository`.
- Nombres de negocio en español; capas técnicas en inglés.
- No agregar capas nuevas ni renombrar las existentes sin autorización.
- Un módulo se crea cuando entra su primera historia de usuario, no antes.

### Operación — el riesgo más grande del proyecto

- **Local y Railway usan la MISMA base de Supabase.** Cualquier `alembic upgrade`,
  seed o prueba local impacta producción.
- Las pruebas e2e ejecutan `TRUNCATE` y llevan un freno que las saltea si
  `DATABASE_URL` no apunta a un host local. **No quitar ese freno.**
- `scripts/reiniciar_base.py` borra tabla por tabla dentro de `public` y nunca hace
  `DROP SCHEMA`: eso destruiría los esquemas propios de Supabase.
- Para migraciones, conexión directa (5432), no el pooler de transacciones (6543).

---

## 5. Mapa de módulos

| ID | Módulo | Responsabilidad | PA / CU | Estado | Endpoints | Ruta |
|---|---|---|---|---|---|---|
| MOD-001 | auth | Autenticación y sesión | PA-01 / CU-03 | IMPLEMENTADO | 9 | `src/ssas/auth/` |
| MOD-002 | usuarios | Gestión de usuarios | PA-01 / CU-04 | IMPLEMENTADO | 10 | `src/ssas/usuarios/` |
| MOD-003 | roles | Roles y permisos | PA-01 / CU-05 | IMPLEMENTADO | 6 | `src/ssas/roles/` |
| MOD-004 | platform | Empresas, planes y suscripciones | PA-01 / CU-01, CU-02 | IMPLEMENTADO | 8 | `src/ssas/platform/` |
| MOD-005 | bitacora | Auditoría | PA-01 / CU-06 | IMPLEMENTADO | 2 | `src/ssas/bitacora/` |
| MOD-006 | departamentos | Estructura organizativa | PA-04 / CU-19 | IMPLEMENTADO | 4 | `src/ssas/departamentos/` |
| MOD-007 | cargos | Cargos | PA-04 / CU-19 | IMPLEMENTADO | 4 | `src/ssas/cargos/` |
| MOD-008 | vacantes | Vacantes | PA-02 / CU-07 | PARCIAL | 0 | `src/ssas/vacantes/` |
| MOD-009 | postulantes | Banco de talentos | PA-02 / CU-11 | PARCIAL | 0 | `src/ssas/postulantes/` |
| MOD-010 | habilidades | Catálogo de habilidades | PA-02 / DESCONOCIDO | PARCIAL | 0 | `src/ssas/habilidades/` |
| MOD-011 | postulaciones | Postulaciones | PA-02 / CU-09, CU-12 | PARCIAL | 2 | `src/ssas/postulaciones/` |

---

## 6. Dependencias entre módulos

```text
core (security · tenancy)
 └── auth ── usuarios ── roles ── permisos
                │
           platform (empresas)
                │
        departamentos ── cargos
                │
     vacantes ── habilidades
         │
   postulaciones ── postulantes

bitacora  <- transversal: todos los módulos generan eventos, ninguno depende de él
```

---

## 7. Inconsistencias detectadas

| # | Inconsistencia | Impacto |
|---|---|---|
| 1 | Migraciones con numeración duplicada: dos `0002` (`20260825_0002_borrado_logico` y `20260830_0002_crear_departamentos_y_cargos`) | Confunde el orden real; Alembic se guía por `down_revision`, no por el nombre |
| 2 | Dos migraciones conservan el hash autogenerado (`0d142a1a7539`, `7694bb109d4b`) | Rompe la convención de nombres del resto |
| 3 | `docs/database/schema_sprint0_sprint1.sql` documenta **23 tablas**; el ORM define 19. Cuatro (`parametro_legal`, `parametro_valor`, `plan_suscripcion`, `suscripcion`) no existen ni en las migraciones ni en el código | Segunda fuente de verdad ya desincronizada. Archivado en `docs/_archivo/` |
| 3b | La funcionalidad de **planes y suscripciones** se retiró: `/platform/planes` y `/platform/suscripciones` ya no existen entre los 46 endpoints | Si el alcance del SaaS los necesita, es una `DECISIÓN PENDIENTE`; si no, hay que quitarlos del perfil del proyecto |
| 4 | La colección Postman se llama `SSAH_RRHH` y el proyecto es `SSAS` | Nombre heredado del rename |
| 5 | `vacantes`, `postulantes` y `habilidades` tienen modelos y migración aplicada pero ninguna capa de aplicación | Tablas en producción sin forma de usarlas |
| 6 | 6 de 9 módulos con endpoints no tienen ningún test | El aislamiento entre empresas no está verificado en la mayoría |
| 7 | **El perfil usa dos numeraciones de CU distintas.** En §3.10.2: CU-07 Gestionar vacante, CU-08 Consultar portal, CU-09 Postularse, CU-10 Cargar hoja de vida, CU-11 Banco de talentos. En el Capítulo 4 (Sprint 1): CU-07 Departamentos y cargos, CU-08 Vacantes, CU-09 Portal, CU-10 Postular, CU-11 Estado, CU-12 Tablero | **El defecto más grave.** Impide verificar qué se entregó; es el primer error que detecta la docente. Esta documentación usa la numeración del **Capítulo 4**, por ser la del sprint en ejecución → `PERF-001` |
| 8 | **CP-S1-21 figura como FALLA** en el reporte de pruebas del perfil (05/09/2026): un usuario de la empresa B accede al tablero de la empresa A sin recibir 404 | Fallo de aislamiento multi-tenant documentado y sin resolver → `BUG-001` (CRÍTICA) |
| 9 | El diseño de datos del Sprint 1 en el perfil todavía crea `plan_suscripcion` y `suscripcion`, y el código las eliminó | El script del perfil no se puede ejecutar contra el esquema actual → `PERF-001` |
| 10 | El portal público del perfil es `/publico/{empresa_slug}/vacantes`; el código solo expone `/publico/postulaciones` | La ruta documentada no existe → `POR-001` |
| 11 | **El grafo de Alembic tiene dos cabezas.** `alembic upgrade head` falla con `Multiple head revisions are present`; `alembic heads` devuelve `20260825_0002` y `20260906_0004`, ambas descendientes de `20260825_0001` | **Bloqueador duro.** Un clon nuevo no puede construir el esquema, y ninguna migración nueva se puede añadir sin elegir cabeza. Es más grave que la numeración de la inconsistencia 1 → `MIG-002` (CRÍTICA) |
| 12 | **El rol RECLUTADOR se aprovisiona con cero permisos.** `ROLE_DEFINITIONS` le pide `vacantes:gestionar` y `candidatos:gestionar`; ninguno existe en el catálogo de 28, y `if code_ in permission_by_code` los descarta en silencio | El actor de CU-08, CU-09 y CU-12 no puede operar, y no hay error visible → `SEC-001` (CRÍTICA) |
| 13 | El backlog planea permisos granulares (`vacantes:ver|crear|…`) y `provision_empresa.py` espera uno grueso (`vacantes:gestionar`) | Si `VAC-004` y `SEC-001` no usan el mismo vocabulario, el rol vuelve a quedar vacío. `DECISIÓN PENDIENTE` → §6 del documento 04 |
| 14 | `pytest` a secas falla con 8 errores de colección; sólo funciona con `PYTHONPATH=src`. `pip install -e .` no lo arregla | El paso 8 de este protocolo es inejecutable como está escrito → `TOOL-001` |
| 15 | `ruff check src tests` devuelve 15 errores preexistentes | Un agente no puede distinguir sus errores de los heredados → `TOOL-002` |
| 16 | Los documentos `01`, `02`, `03`, `04` y `scripts/` **no están versionados** en git | Un agente que clona el repositorio no ve la documentación que este protocolo le manda leer → `DOC-003` |
| 17 | 157 archivos de `src/` aparecen modificados sólo por el final de línea (CRLF frente a LF); falta `.gitattributes` | Los diffs de los agentes son ilegibles y cada commit arrastra ruido → `DOC-003` |

---

## 8. Protocolo para agentes

1. `git fetch` y confirmar que trabajás sobre el HEAD actual.
2. Leer este documento.
3. Leer la TASK asignada completa en `03_BACKLOG_IMPLEMENTACION.md`.
4. Leer el endpoint relacionado en `02_API_ENDPOINTS.md`.
5. Revisar solo el módulo afectado y sus dependencias.
6. Verificar a qué base apunta `DATABASE_URL` antes de cualquier comando que escriba.
7. Implementar solo el alcance de la tarea.
8. `pytest` · `ruff check` · `python scripts/verificar_documentacion.py`.
9. Actualizar los tres documentos.
10. No modificar tareas ajenas ni reformatear archivos completos.

---

## 9. Documentación relacionada

| Documento | Contenido |
|---|---|
| `02_API_ENDPOINTS.md` | Contrato de los 46 endpoints + los 18 pendientes |
| `03_BACKLOG_IMPLEMENTACION.md` | Las 36 tareas, dependencias y criterios de aceptación |
| `04_EJECUCION_MULTIAGENTE_SPRINT1.md` | Olas, reparto de archivos entre agentes, contrato del agente y decisiones pendientes |
| `tareas_sprint1.json` | Las mismas tareas en formato consumible por un orquestador |
| `arquitectura/ARQUITECTURA_BACKEND_FASTAPI.md` | Documento de diseño (entregable del Capítulo 2) |
| `arquitectura/CONTRATO_OPENAPI_Y_VERSIONADO.md` | Convenciones de OpenAPI y versionado |
| `guias/GUIA_DESARROLLO.md` | Puesta en marcha y flujo de trabajo |
| `guias/AUTH_Y_USUARIOS.md` · `guias/PLATFORM_ADMINISTRACION.md` | Guías funcionales |
| `sprints/SPRINT_0_ADAPTACION_ORM.md` | Registro histórico |

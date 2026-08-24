# Backend SSAS RRHH

API del **Sistema de Gestión de Recursos Humanos** — plataforma ERP modular comercializada como
**SaaS multi-tenant**, con énfasis en Reclutamiento y Selección de Personal.

**Materia:** Sistemas de Información 2 (INF 412-SA) · UAGRM · Semestre 2-2026
**Grupo:** N.° 12 · **Docente:** M.Sc. Ing. Angélica Garzón Cuéllar
**Marco de trabajo:** SCRUM (sprints de 2 semanas) · **Arquitectura documentada con:** modelo C4

---

## Tabla de contenido

1. [Estado del proyecto](#1-estado-del-proyecto)
2. [Stack tecnológico](#2-stack-tecnológico)
3. [Requisitos previos](#3-requisitos-previos)
4. [Instalación](#4-instalación)
5. [Ejecución](#5-ejecución)
6. [Variables de entorno](#6-variables-de-entorno)
7. [Estructura del proyecto](#7-estructura-del-proyecto)
8. [Arquitectura](#8-arquitectura)
9. [Convenciones de código](#9-convenciones-de-código)
10. [Módulos y trazabilidad](#10-módulos-y-trazabilidad)
11. [Base de datos y migraciones](#11-base-de-datos-y-migraciones)
12. [Pruebas](#12-pruebas)
13. [Endpoints](#13-endpoints)
14. [Flujo de trabajo con Git](#14-flujo-de-trabajo-con-git)
15. [Problemas conocidos](#15-problemas-conocidos)
16. [Equipo](#16-equipo)

---

## 1. Estado del proyecto

> **Sprint 0 — andamiaje.** El paquete Python ya vive en `src/ssas`, los routers se montan bajo
> `/api/v1` y la capa de persistencia queda preparada para validarse cuando PostgreSQL esté conectado.
> Esta tabla se actualiza al cierre de cada sprint.

| Componente | Estado | Nota |
|---|---|---|
| Estructura de módulos y capas | ✅ Definida | Ver [§7](#7-estructura-del-proyecto) |
| Contratos (puertos) de `auth` y `bitacora` | ✅ Definidos | `application/ports/` |
| Casos de uso de `auth` | ✅ Implementados | Login por empresa, refresh, logout, perfil y recuperación |
| Conexión a PostgreSQL | ✅ Validada | SQLAlchemy async + Psycopg contra Supabase |
| Repositorios reales | ✅ Implementados | Auth, usuarios, roles, permisos, empresa y bitácora |
| Migraciones (Alembic) | ✅ Aplicadas | Base remota en `20260824_0002` |
| Autenticación JWT funcional | ✅ Implementada | PyJWT + Argon2id y refresh con rotación |
| Multi-tenant | 🟡 Base implementada | Aislamiento por `empresa_id`; falta aprovisionamiento y superadmin |
| RBAC (roles y permisos) | ✅ Implementado | Permisos globales y roles por empresa |
| Pruebas | 🟡 En crecimiento | 10 unitarias y conexión real validada |

`GET /` y `GET /health` funcionan sin consultar la base. Los endpoints de negocio se montan bajo
`/api/v1` y requieren PostgreSQL configurado.

---

## 2. Stack tecnológico

| Capa | Tecnología | Decisión |
|---|---|---|
| Lenguaje | Python 3.12 | Adoptado |
| Framework web | FastAPI | Adoptado |
| ORM | SQLAlchemy 2.0 (modo **async**) | Adoptado |
| Migraciones | Alembic | Adoptado |
| Base de datos | PostgreSQL 15+ | Adoptado |
| Validación / configuración | Pydantic 2 · pydantic-settings | Adoptado |
| Autenticación | JWT propio (access + refresh con rotación) | Adoptado |
| Hasheo de contraseñas | Argon2id | Adoptado |
| Pruebas | pytest · pytest-asyncio · httpx | Adoptado |
| Linting / formato | Ruff | Adoptado |
| Estrategia multi-tenant | *por definir* | Ver [§15](#15-problemas-conocidos) |
| Redis / caché | No, hasta que exista una necesidad real | Descartado por ahora |

---

## 3. Requisitos previos

- **Python 3.12** — `python --version`
- **PostgreSQL 15 o superior** en ejecución, con una base creada para el proyecto
- **Git**

Verificación rápida:

```bash
python --version     # 3.12
psql --version       # >= 15
git --version
```

---

## 4. Instalación

```bash
git clone <url-del-repositorio>
cd backend_ssas_rrhh

# 1. Entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell / CMD)
source .venv/bin/activate       # Linux / macOS

# 2. Dependencias (se leen de pyproject.toml)
pip install -U pip
pip install -e ".[dev]"

# 3. Configuración
copy .env.example .env          # Windows
cp .env.example .env            # Linux / macOS
# editar .env con los valores locales
```

> El paquete importable del backend es `ssas` y vive dentro de `src/`. Trabajar desde la raíz del
> repositorio mantiene consistente la carga de `.env`, Alembic y los comandos de desarrollo.

---

## 5. Ejecución

Desde la **raíz del repositorio**, con el entorno virtual activo:

```bash
uvicorn ssas.main:app --reload
```

| Recurso | URL |
|---|---|
| API | http://localhost:8000 |
| Documentación interactiva (Swagger) | http://localhost:8000/docs |
| Documentación alternativa (ReDoc) | http://localhost:8000/redoc |
| Esquema OpenAPI | http://localhost:8000/openapi.json |

> El módulo es `ssas.main:app` — **no** `src.app.main:app`. La carpeta `src/app/` no existe: el
> documento de arquitectura (§6) decidió explícitamente no usarla.

---

## 6. Variables de entorno

Se declaran en `.env` (nunca versionado) y se documentan sin valores reales en `.env.example`.

| Variable | Descripción | Ejemplo |
|---|---|---|
| `APP_ENV` | Entorno de ejecución | `development` · `production` |
| `APP_DEBUG` | Modo depuración | `true` · `false` |
| `APP_SECRET_KEY` | Clave de firma de los JWT | *(generar, ver abajo)* |
| `APP_ALGORITHM` | Algoritmo de firma | `HS256` |
| `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del access token | `15` |
| `APP_REFRESH_TOKEN_EXPIRE_DAYS` | Vigencia del refresh token | `7` |
| `DATABASE_URL` | Cadena de conexión a PostgreSQL | `postgresql+psycopg://usuario:clave@localhost:5432/ssas_rrhh` |
| `DB_ECHO` | Mostrar SQL ejecutado | `false` |
| `DB_POOL_SIZE` | Conexiones permanentes del pool | `5` |
| `DB_MAX_OVERFLOW` | Conexiones adicionales permitidas | `10` |
| `DB_POOL_RECYCLE_SECONDS` | Reciclado preventivo de conexiones | `1800` |

**Reglas de manejo de secretos:**

- `.env` está en `.gitignore` y **nunca** debe commitearse. Si alguna vez se subió, hay que rotar
  la clave, no solo borrar el archivo.
- Ninguna clave, token ni contraseña va escrita en el código fuente ni en `pyproject.toml`.
- `.env.example` documenta **qué** variables hacen falta, con valores de relleno, nunca reales.
- Cada integrante genera su propia `APP_SECRET_KEY` local:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

- Para el despliegue, la clave se inyecta como variable del entorno del servidor, no desde un archivo.

Las variables se cargan mediante `pydantic-settings`; `APP_SECRET_KEY` es obligatoria.

---

## 7. Estructura del proyecto

```
backend_ssas_rrhh/
├── src/
│   └── ssas/                    Paquete Python principal
│       ├── main.py              Punto de entrada: FastAPI, routers y middleware
│       ├── config/              Configuración centralizada
│       ├── infrastructure/      Base de datos y servicios transversales
│       ├── auth/                Autenticación y sesiones
│       ├── usuarios/            Administración de usuarios
│       ├── roles/               Roles y permisos
│       ├── empresas/            Empresa y parámetros legales
│       └── bitacora/            Auditoría del sistema
│
├── migrations/versions/        Migraciones Alembic
├── tests/{unit,integration,e2e}/
├── ARQUITECTURA_BACKEND_FASTAPI.md   Documento de diseño (50 secciones)
├── ANALISIS_Y_PROPUESTA_BACKEND.md   Auditoría del backend y estructura propuesta
├── pyproject.toml · .env.example · .gitignore
```

Cada módulo de negocio repite la misma disposición interna:

```
<modulo>/
├── domain/           Reglas del negocio. Sin FastAPI, SQLAlchemy, Pydantic ni JWT.
├── application/      Casos de uso: qué puede hacer el sistema.
├── ports/            Contratos: qué necesita la aplicación, sin decir con qué tecnología.
└── infrastructure/   Cómo se resuelve: FastAPI, SQLAlchemy, PostgreSQL, JWT.
```

---

## 8. Arquitectura

Combinación de cuatro principios, documentados en detalle en
**[`ARQUITECTURA_BACKEND_FASTAPI.md`](./ARQUITECTURA_BACKEND_FASTAPI.md)**:

- **Vertical Slicing** — el sistema se organiza por funcionalidades de negocio, no por capas técnicas.
  `auth/`, `bitacora/`, `planilla/`… en lugar de `controllers/`, `services/`, `models/`.
- **Screaming Architecture** — los nombres del código dicen qué hace el sistema. Al abrir `src/` se
  ve el negocio, no el framework.
- **Hexagonal (puertos y adaptadores)** — el núcleo no depende de tecnologías externas. Se comunica
  con el exterior mediante contratos que la infraestructura implementa.
- **Domain / Application / Infrastructure** — separación de responsabilidades dentro de cada módulo.

**Regla de dependencias** — la flecha apunta siempre hacia adentro:

```
Infrastructure  ──▶  Application  ──▶  Domain
```

El dominio no conoce a nadie. La infraestructura conoce a todos.

**Recorrido de una petición** (`POST /auth/login`):

```
Cliente HTTP → Router (FastAPI) → Schema → DTO → Caso de uso → Dominio
                                                       │
                                                       ├─▶ UserRepository (puerto)
                                                       │       └─▶ Adapter → SQLAlchemy → PostgreSQL
                                                       ├─▶ PasswordHasher (puerto) → Argon2
                                                       └─▶ TokenService (puerto) → JWT
```

**Regla que gobierna todas las demás** (§44 y §50 del documento de arquitectura):

> No se agrega una abstracción solo porque sea habitual en una arquitectura avanzada.
> Cada componente debe justificar qué problema resuelve.
>
> *La arquitectura está al servicio del sistema, no el sistema al servicio de la arquitectura.*

---

## 9. Convenciones de código

| Aspecto | Convención | Ejemplo |
|---|---|---|
| Idioma — negocio | **Español**, igual que los casos de uso del documento | `bitacora/`, `planilla/`, `vacantes/` |
| Idioma — capas técnicas | **Inglés**, son términos de arquitectura | `domain/`, `application/`, `infrastructure/` |
| Archivos y funciones | `snake_case` | `login_user.py`, `get_by_email()` |
| Clases | `PascalCase` | `LoginUser`, `AuditLog` |
| Casos de uso | Verbo + sustantivo, una acción por archivo | `register_user.py`, `list_audit_logs.py` |
| Puertos (contratos) | Sustantivo, sin prefijo tecnológico | `UserRepository` |
| Adaptadores | Tecnología + contrato | `SqlAlchemyUserRepository`, `Argon2PasswordHasher` |
| Entidad vs. modelo ORM | Nombres distintos, archivos distintos | `User` (dominio) vs. `UserModel` (tabla) |
| Excepciones | Del dominio, nunca `HTTPException` fuera de la capa HTTP | `InvalidCredentialsError` |
| Anotaciones de tipo | Obligatorias en firmas públicas | `async def execute(self, email: str) -> User:` |
| Longitud de línea | 100 caracteres (Ruff) | |

Antes de cada commit:

```bash
ruff check src tests --fix
ruff format src tests
pytest
```

---

## 10. Módulos y trazabilidad

Cada módulo declara a qué **paquete de análisis (PA)** y a qué **casos de uso (CU)** responde. Esto
mantiene la trazabilidad **RF → CU → HU → código → prueba** exigida por la materia.

| Paquete | Módulos | Casos de uso |
|---|---|---|
| **PA-01** Seguridad y Administración | `tenants` · `auth` · `usuarios` · `roles` · `bitacora` | CU-01 … CU-06 |
| **PA-02** Reclutamiento | `vacantes` · `postulaciones` · `portal_empleo` | CU-07 … CU-11 |
| **PA-03** Selección | `seleccion` · `entrevistas` · `ofertas` | CU-12 … CU-16 |
| **PA-04** Administración de Personal | `colaboradores` · `contratos` · `planilla` · `asistencia` · `ausencias` | CU-17 … CU-25 |
| **PA-05** Capacitación | `capacitacion` | CU-26 … CU-28 |
| **PA-06** Inteligencia Artificial | `ia` (documentos · ranking · chatbot · rotación) | CU-29 … CU-32 |
| **PA-07** Reportes e Indicadores | `reportes` · `notificaciones` | CU-33 … CU-35 |

> **Un módulo se crea cuando entra su primera historia de usuario**, no antes. Hoy existen `auth` y
> `bitacora`; el resto aparece sprint a sprint.

Cada módulo lleva esta cabecera en su `__init__.py`:

```python
"""Módulo de autenticación.

Paquete:  PA-01 · Seguridad y Administración
Casos de uso:  CU-03 Autenticar usuario
Historias:  HU-02
"""
```

---

## 11. Base de datos y migraciones

**El esquema se modifica únicamente mediante migraciones.** Nunca con `CREATE TABLE` a mano ni con
`Base.metadata.create_all()`: sin migración versionada, el resto del equipo no puede reproducir el cambio.

```bash
# Generar una migración a partir de los modelos
alembic revision --autogenerate -m "crear tabla usuarios"

# Aplicar migraciones
alembic upgrade head

# Revertir la última
alembic downgrade -1

# Ver el estado actual
alembic current
alembic history

# Comprobar que ORM y base no tienen diferencias pendientes
alembic check
```

Revisiones aplicadas en Supabase:

- `20260820_0001`: esquema inicial multiempresa.
- `20260824_0002`: bitácora funcional, unicidad case-insensitive y datos base.

**Reglas:**

- Todos los modelos ORM heredan de una **única `Base` declarativa** compartida. Si cada módulo define
  la suya, Alembic solo detecta una y las claves foráneas entre módulos dejan de ser posibles.
- Toda tabla de negocio multiempresa lleva `empresa_id` desde su primera migración. Agregarlo después obliga a
  reescribir el esquema completo.
- Toda migración autogenerada se **revisa a mano** antes de commitear: Alembic no siempre acierta con
  renombres, índices ni tipos.

---

## 12. Pruebas

```bash
pytest                               # todo
pytest tests/unit                    # solo unitarias
pytest -k login                      # por nombre
pytest -x -vv                        # detenerse en el primer fallo, salida detallada

# Cobertura (requiere agregar pytest-cov a las dependencias dev)
pytest --cov=src --cov-report=term-missing
```

| Nivel | Qué prueba | Dependencias |
|---|---|---|
| `tests/unit/` | Casos de uso en aislamiento | Puertos falsos (*fakes*), sin base de datos |
| `tests/integration/` | Repositorios contra el motor real | PostgreSQL de prueba |
| `tests/e2e/` | La API de punta a punta | Aplicación completa vía `httpx` |

**Mínimo por historia de usuario:** una prueba unitaria del caso de uso y una prueba e2e del endpoint.
Los resultados alimentan la sección *2.3 Pruebas* de la plantilla de sprint del documento del proyecto.

---

## 13. Endpoints

**Disponible hoy:**

| Método | Ruta | Descripción | CU |
|---|---|---|---|
| `GET` | `/` | Mensaje de estado del servicio | — |
| `GET` | `/health` | Estado del servicio | — |
| `POST` | `/api/v1/auth/login` | Autenticar usuario | CU-03 |
| `POST` | `/api/v1/auth/refresh` | Renovar el par de tokens | CU-03 |
| `POST` | `/api/v1/auth/logout` | Cerrar sesión y revocar el refresh | CU-03 |
| `GET` | `/api/v1/auth/me` | Datos del usuario autenticado | CU-03 |
| `POST` | `/api/v1/auth/password/forgot` | Solicitar recuperación | CU-03 |
| `POST` | `/api/v1/auth/password/reset` | Restablecer contraseña | CU-03 |
| `POST` | `/api/v1/usuarios` | Crear usuario dentro de la empresa | CU-04 |
| `GET/POST` | `/api/v1/roles` | Consultar y crear roles | CU-05 |
| `PATCH/DELETE` | `/api/v1/roles/{id}` | Actualizar o eliminar un rol | CU-05 |
| `PUT` | `/api/v1/roles/{id}/permissions` | Asignar permisos | CU-05 |
| `GET` | `/api/v1/bitacora` | Listar eventos de auditoría (con filtros) | CU-06 |
| `GET` | `/api/v1/bitacora/{id}` | Consultar un evento | CU-06 |

Eventos mapeados inicialmente: login exitoso/fallido, logout, recuperación de contraseña y cambios
de roles/permisos. Cada evento conserva `empresa_id`, actor, módulo, acción, nivel, IP y user-agent.

> La bitácora contiene información sensible: sus endpoints requieren permiso explícito, no basta
> con estar autenticado.

---

## 14. Flujo de trabajo con Git

Somos 6 personas sobre el mismo repositorio; el Vertical Slicing ayuda, pero la convención hace el resto.

**Ramas:**

```
main                    Estable. Solo recibe merges desde develop.
develop                 Integración del sprint en curso.
feature/HU-07-vacantes  Una rama por historia de usuario.
fix/login-token-expira  Correcciones.
```

**Commits** — [Conventional Commits](https://www.conventionalcommits.org/), con el identificador de la historia:

```
feat(auth): implementar caso de uso LoginUser [HU-02]
fix(bitacora): corregir filtro por rango de fechas [HU-05]
docs(readme): documentar variables de entorno
test(auth): agregar prueba e2e de POST /auth/login [HU-02]
refactor(shared): extraer Base declarativa a core/db
```

**Antes de abrir un Pull Request:**

1. `ruff check src tests --fix && ruff format src tests`
2. `pytest` en verde
3. La migración correspondiente está incluida y revisada
4. `.env` **no** está en el diff

Cada PR se revisa por al menos un integrante distinto del autor. Esto también genera evidencia de
participación distribuida, que se anexa a la documentación del sprint.

---

## 15. Problemas conocidos

Pendientes antes de ampliar los módulos de negocio:

1. Crear el aprovisionamiento transaccional de empresa, suscripción, roles base y primer administrador.
2. Definir la identidad y endpoints exclusivos del superadministrador de plataforma.
3. Conectar un proveedor de correo para recuperación de contraseña.
4. Añadir rate limiting y política de bloqueo por intentos fallidos.
5. Completar pruebas E2E con al menos dos empresas para demostrar aislamiento.
6. Rotar cualquier secreto que haya aparecido en registros locales.

---

## 16. Equipo

**Grupo N.° 12** — 6 integrantes. Los roles SCRUM rotan por sprint y se registran en el documento
del proyecto.

| Rol | Sprint en curso |
|---|---|
| Product Owner | *a completar* |
| Scrum Master | *a completar* |
| Development Team | *a completar* |

---

## Documentación relacionada

| Documento | Contenido |
|---|---|
| [`ARQUITECTURA_BACKEND_FASTAPI.md`](./ARQUITECTURA_BACKEND_FASTAPI.md) | Diseño del backend: 50 secciones, principios y decisiones adoptadas |
| [`ANALISIS_Y_PROPUESTA_BACKEND.md`](./ANALISIS_Y_PROPUESTA_BACKEND.md) | Auditoría del estado actual y estructura propuesta |
| Diagramas UML del Grupo 12 | Paquetes PA-01 … PA-07 y los 35 casos de uso |

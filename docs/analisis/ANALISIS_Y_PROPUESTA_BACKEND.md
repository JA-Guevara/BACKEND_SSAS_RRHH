# Análisis del backend y propuesta de estructura

**Proyecto:** SSAS RRHH — Plataforma SaaS de Gestión de Recursos Humanos · Grupo N.° 12
**Materia:** Sistemas de Información 2 (INF 412-SA) · 2-2026
**Repositorio analizado:** `D:\Uagrm\2 - 2026\Sistemas de Informacion II\backend_ssas_rrhh`
**Fecha del análisis:** 18/08/2026

> **Estado actualizado al 24/08/2026:** este documento conserva el diagnóstico histórico del
> estado inicial. Desde entonces se implementaron la conexión asincrónica a PostgreSQL/Supabase,
> Alembic, Auth, RBAC, bitácora persistente y aislamiento por `empresa_id`. Las migraciones 0001 y
> 0002 están aplicadas, las pruebas vigentes pasan y `alembic check` no detecta diferencias. Para
> conocer el estado operativo actual, consultar la
> [guía de desarrollo](../guias/GUIA_DESARROLLO.md) y el
> [resumen del Sprint 0](../sprints/SPRINT_0_ADAPTACION_ORM.md).

> Este documento distingue **hechos verificados** (reproducidos en sandbox o leídos del código),
> **juicios de diseño** (opinión fundamentada) y **recomendaciones**. Los hallazgos citan archivo y línea.

---

## 0. Veredicto en una página

La **estructura conceptual está bien** y el documento `ARQUITECTURA_BACKEND_FASTAPI.md` está muy por
encima del promedio: define Vertical Slicing, Hexagonal, la regla de dependencias y —lo más raro y
lo más valioso— dos reglas anti-sobrearquitectura (§44 y §50). Ese documento se puede defender.

El problema no es el diseño: es que **lo implementado no es lo documentado, y lo poco implementado
no funciona**. Concretamente:

| | Estado |
|---|---|
| Carpetas creadas | 100 % del árbol del documento |
| Código que se ejecuta hoy | Un `GET /` que devuelve un mensaje |
| Routers montados en la app | **0 de 2** |
| Repositorios reales | **0** (uno es un stub que devuelve datos inventados) |
| Conexión a base de datos | **No existe** (no hay engine, ni sesión, ni `Base` compartida) |
| Alembic | **No inicializado** (`migrations/` vacía, sin `env.py` ni `alembic.ini`) |
| Pruebas | **0** |
| Multi-tenant | **0** — y es la pregunta 3.d del examen final |
| RBAC / permisos (CU-05) | **0** |

Y tres defectos **confirmados ejecutando código**, no inferidos:

1. **Ninguna variable de entorno se lee.** La app arranca siempre con la clave de firma de ejemplo
   y apuntando a `localhost/app_db`, aunque el `.env` diga otra cosa. (§2.1)
2. **El hasheo de contraseñas revienta.** `passlib` 1.7.4 + `bcrypt` 5.0.0 lanzan `ValueError`.
   Registro y login son inejecutables hoy. (§2.2)
3. **El comando de arranque del README apunta a una ruta inexistente**, y el empaquetado deja el
   mismo módulo importable bajo dos nombres, con riesgo de duplicar objetos globales. (§2.3)

**Lo que hay que decidir antes de escribir una línea más** son cinco cosas (§5): dónde vive la capa de
plataforma, sync vs async, DTO vs Schema, dónde va `tenant_id`, y el nombre real del paquete Python.
Las cinco son baratas hoy y caras en el Sprint 3.

---

## 1. Inventario: lo documentado vs. lo implementado

### 1.1 Lo que existe en disco

```
backend_ssas_rrhh/
├── ARQUITECTURA_BACKEND_FASTAPI.md   34 KB · 50 secciones · el documento de diseño
├── pyproject.toml · README.md · .env · .env.example · .gitignore
├── migrations/versions/              ← VACÍA (sin alembic.ini, sin env.py)
├── tests/{unit,integration,e2e}/     ← VACÍAS (0 pruebas)
└── src/
    ├── main.py                       ← 8 líneas, no monta ningún router
    ├── config/settings.py
    ├── shared/{exceptions,types}/    ← VACÍAS
    ├── auth/
    │   ├── domain/{entities/user.py, exceptions.py, value_objects/ ← VACÍA}
    │   ├── application/{dto/×2, use_cases/×4}
    │   ├── ports/outgoing/×3
    │   └── infrastructure/
    │       ├── http/{router.py, schemas.py}
    │       ├── security/{jwt_service.py, password_hasher.py}
    │       └── persistence/{models/ ← VACÍA, repositories/ ← VACÍA}
    └── bitacora/
        ├── domain/{entities/audit_log.py, exceptions.py, value_objects/ ← VACÍA}
        ├── application/{dto/×2, use_cases/×3}
        ├── ports/outgoing/audit_log_repository.py
        └── infrastructure/{http/×2, persistence/{models/×1, repositories/×1}}
```

Total: 34 archivos, de los cuales **29 son Python: 334 líneas, 9,2 KB**. `frontend_ssah_rrhh/` está
completamente vacía.

### 1.2 Contradicciones entre el documento y el código

| # | El documento dice | El código hace |
|---|---|---|
| D1 | §47: *"No se crearán todas las carpetas anticipadamente"* | Se creó el árbol completo por adelantado; 6 carpetas quedaron vacías |
| D2 | §7: `main.py` debe *"registrar routers"* | `main.py` no importa ni monta ningún router |
| D3 | §9: el dominio y la aplicación no deben depender de **Pydantic** | `application/dto/login.py:1` → `from pydantic import BaseModel, EmailStr` |
| D4 | §18: el adapter transforma *Schema Pydantic → DTO de Application* | No hay mapper; `LoginRequest` (DTO) y `LoginSchema` (Schema) son **la misma clase duplicada** |
| D5 | §21: el adapter se llama `PostgresUserRepository` | El adapter de bitácora se llama `AuditLogRepository`, **idéntico al puerto** |
| D6 | §11: el dominio define sus excepciones | `login_user.py:10` lanza `ValueError("Credenciales inválidas")`; `InvalidCredentialsError` existe y **nadie la usa** |
| D7 | §39: el registro *"registra evento de auditoría"* | `RegisterUser` no toca bitácora; los dos módulos están desconectados |
| D8 | §6: se decide **no** usar `src/app/` | El README instruye `uvicorn src.app.main:app` |
| D9 | §34: migraciones `001_create_users.py`, etc. | Alembic no está inicializado |

D1 merece un comentario aparte: es exactamente el patrón de fallo §6.1 del contexto maestro
(*"secciones tituladas y vacías"*) trasladado del documento Word al código fuente. Es el defecto que
la docente detecta primero, y aquí ya está reproducido en el repositorio.

---

## 2. Defectos confirmados ejecutando código

Los tres siguientes no son opinión: se reprodujeron en un entorno limpio.

### 2.1 CRÍTICO — Ninguna variable de entorno se lee

`src/config/settings.py:15` declara `env_prefix="APP_"` sobre campos que **ya empiezan con `app_`**.

```python
class Settings(BaseSettings):
    app_secret_key: str = "change-me-in-production"
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/app_db"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", case_sensitive=False)
```

pydantic-settings concatena prefijo + nombre de campo. Por lo tanto busca:

| Campo | Variable que busca | Variable que existe en `.env` | Resultado |
|---|---|---|---|
| `app_secret_key` | `APP_APP_SECRET_KEY` | `APP_SECRET_KEY` | ❌ default |
| `app_access_token_expire_minutes` | `APP_APP_ACCESS_TOKEN_EXPIRE_MINUTES` | `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ default |
| `database_url` | `APP_DATABASE_URL` | `DATABASE_URL` | ❌ default |

**Reproducción** (sandbox limpio, `.env` con valores reales de producción):

```
app_env                 = development                 ← el .env decía production
app_secret_key          = change-me-in-production      ← el .env traía otro secreto
app_access_token_expire = 60                           ← el .env decía 15
database_url            = postgresql+psycopg://user:password@localhost:5432/app_db
```

**Impacto:** los JWT se firman en todos los entornos con la cadena pública `change-me-in-production`,
que además está versionada en `.env.example`. Cualquiera puede forjar un token válido. Y la app nunca
apuntará a la base de datos real.

**Corrección:** eliminar `env_prefix` y volver el secreto obligatorio (sin default) —
verificado funcionando:

```python
class Settings(BaseSettings):
    app_env: str = "development"
    app_secret_key: str                # sin default: si falta, la app NO arranca
    database_url: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

> Nota de seguridad: el `.env` real está correctamente excluido por `.gitignore`. Conviene además
> confirmar con `git log --all -- .env` que nunca se haya commiteado, y rotar el secreto antes del
> despliegue. Nunca fijar claves en el código ni en el `pyproject.toml`.

### 2.2 CRÍTICO — El hasheo de contraseñas no se ejecuta

`src/auth/infrastructure/security/password_hasher.py:8` usa
`CryptContext(schemes=["bcrypt"], deprecated="auto")`, y `pyproject.toml` fija `passlib[bcrypt]>=1.7.4`.

**Reproducción** con las versiones que instala hoy ese `pyproject.toml`
(`passlib 1.7.4`, última publicación **08/10/2020**; `bcrypt 5.0.0`):

```
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
  passlib/handlers/bcrypt.py:380  in detect_wrap_bug
  passlib/handlers/bcrypt.py:655  in _calc_checksum
```

`passlib` ejecuta una rutina interna de detección de bugs que envía una sonda de más de 72 bytes;
las versiones modernas de `bcrypt` la rechazan en vez de truncarla. **Registro y login son
inejecutables hoy**, no por un error de ustedes sino porque `passlib` lleva casi seis años sin release.

**Corrección:** la documentación oficial vigente de FastAPI ya **no** recomienda `passlib` ni
`python-jose`; recomienda **`pwdlib[argon2]`** y **`PyJWT`**. Verificado funcionando
(`pwdlib 0.3.1`, `pyjwt 2.12.1`):

```python
from pwdlib import PasswordHash
hasher = PasswordHash.recommended()      # Argon2id
h = hasher.hash("secreto123")            # $argon2id$v=19$m=65536,t=3,p=4$...
hasher.verify("secreto123", h)           # True
```

Cambiar ahora cuesta ~20 líneas. Cambiarlo con usuarios ya registrados cuesta una migración de hashes.

### 2.3 ALTO — El comando de arranque del README no existe, y el empaquetado es ambiguo

Dos fallos encadenados:

- El README indica `uvicorn src.app.main:app`, pero el archivo está en `src/main.py`, y el documento
  de arquitectura §6 decide explícitamente **no** usar `src/app/`. El comando correcto hoy es
  `uvicorn src.main:app`.
- `pip install -e .` con *src-layout* y sin `__init__.py` hace que setuptools ponga `src/` en el path.
  El paquete instalado expone `auth`, `config` y `bitacora` como módulos de **primer nivel**, mientras
  todo el código importa `from src.config.settings import ...`. **Reproducido, ejecutando desde fuera
  de la raíz del repositorio:**

```
import src                 → ModuleNotFoundError: No module named 'src'
import src.config.settings → ModuleNotFoundError: No module named 'src'
import config              → OK
import auth                → OK
```

Ejecutando **desde la raíz** sí funciona, porque el directorio actual entra al path y `src` resuelve
como *namespace package* (PEP 420). Pero entonces aparece un riesgo más sutil, también reproducido:
**el mismo archivo queda importable bajo dos nombres**, `src.config.settings` y `config.settings`, y
Python los trata como **dos módulos distintos**. Un objeto global como `settings` —o la `Base`
declarativa de SQLAlchemy— puede terminar instanciado dos veces con estado independiente. Es la clase
de fallo que aparece recién en integración y cuesta horas de diagnóstico.

**Corrección (§4.1):** dar al paquete un nombre real — `src/ssas/` — y declararlo en `pyproject.toml`.

---

## 3. Hallazgos de diseño e implementación

Ordenados por severidad. Los de §2 no se repiten.

### 3.1 Seguridad

| ID | Severidad | Hallazgo |
|---|---|---|
| S1 | **Alta** | **El logout es cosmético.** `logout_user.py:2-3` devuelve `{"message": "Sesión cerrada", "token": token}` sin invalidar nada. Además **refleja el token en la respuesta**, lo que lo expone en logs, proxies y en el historial del navegador. Sin lista de revocación, la sesión sigue viva hasta la expiración. |
| S2 | **Alta** | **El refresh no rota.** `refresh_token.py:5-15` decodifica el token y emite un par nuevo, pero **el refresh viejo sigue siendo válido 7 días**. Un token robado se puede reutilizar indefinidamente. Elegiste "rotación con revocación": esto todavía no lo es. |
| S3 | **Alta** | **Un access token sirve como refresh token.** `jwt_service.py` firma ambos con el mismo payload `{sub, exp}`; `decode_token` no distingue. Faltan los claims `type`, `jti` e `iat`. |
| S4 | Media | `datetime.utcnow()` (`jwt_service.py:11` y `:17`) está deprecado desde Python 3.12 y devuelve un datetime *naive*. Usar `datetime.now(timezone.utc)`. |
| S5 | Media | Sin límite de intentos de login, sin bloqueo de cuenta, sin registro de `LOGIN_FAILED` en bitácora — pese a que el documento §23 lista ese evento explícitamente. |
| S6 | Media | Ningún endpoint está protegido: no existe `get_current_user` ni ninguna dependencia de autorización. |
| S7 | Media | Sin CORS configurado. El frontend Angular/React no podrá consumir la API. |

### 3.2 Arquitectura y corrección

| ID | Severidad | Hallazgo |
|---|---|---|
| A1 | **Alta** | **`Base` declarativa local.** `bitacora/.../models/audit_log.py:4` hace `Base = declarative_base()` dentro del archivo. Si cada módulo repite el patrón, habrá una `Base` por módulo: Alembic `--autogenerate` solo verá una, y **no se podrán declarar claves foráneas entre módulos** (por ejemplo `audit_logs.user_id → users.id`). Con 19 módulos previstos esto se vuelve irreparable. |
| A2 | **Alta** | **Sync vs async incoherente.** Los routers son `async def`, pero los casos de uso y los puertos son síncronos. Elegiste **SQLAlchemy 2.0 async**: un adapter `async def get_by_email` **no puede** implementar un puerto `def get_by_email`. Hay que decidirlo ahora, no después de escribir 35 casos de uso. |
| A3 | **Alta** | **DTO y Schema son la misma clase duplicada.** `application/dto/login.py::LoginRequest` y `infrastructure/http/schemas.py::LoginSchema` tienen los mismos campos y ambos heredan de `BaseModel`. Viola §9 (aplicación sin Pydantic), §18 (debía haber transformación) y §44 (anti-sobrearquitectura) del propio documento. Lo mismo en bitácora. |
| A4 | Media | **`JWTService` no implementa su puerto.** `BcryptPasswordHasher` sí hereda de `PasswordHasher`, pero `JWTService` no hereda de `TokenService`. El contrato no está garantizado por el tipo. |
| A5 | Media | **`JWTService` lee la configuración global** en vez de recibirla por constructor → no se puede inyectar otra clave ni otra expiración en las pruebas unitarias. |
| A6 | Media | **Colisión de nombres.** `ports/outgoing/audit_log_repository.py::AuditLogRepository` y `infrastructure/persistence/repositories/audit_log_repository.py::AuditLogRepository`: mismo nombre de archivo **y** de clase. Importar ambos en el mismo módulo obliga a renombrar con `as`. |
| A7 | Media | **El adapter de bitácora es un stub falso.** `add` devuelve lo que recibe, `list` devuelve `[]` y `get_by_id` devuelve `{"action": "login", "description": "Registro de ejemplo"}`. Un endpoint sobre esto *parece* funcionar sin tocar la base — es el tipo de "funcionalidad decorativa" que el enunciado del 2.º parcial rechaza explícitamente. |
| A8 | Media | **Excepciones de dominio definidas y no usadas** (D6). Sin ellas no hay forma de mapear a HTTP 401 vs 409 sin comparar cadenas de texto. Falta además el manejador global de errores que §7 asigna a `main.py`. |
| A9 | Media | **El modelo ORM no coincide con la entidad ni con el documento.** `AuditLog` (dominio) tiene `created_at: str`; `AuditLogResponse` (DTO) lo tipa `datetime`; y `AuditLogModel` (tabla) **no tiene la columna**. El §24 del documento lista `resource`, `resource_id`, `timestamp`, `metadata`: ninguno existe. Tampoco `ip`, `user_agent` ni `tenant_id`. |
| A10 | Baja | `AuditLogModel` usa el estilo **SQLAlchemy 1.x** (`Column`, `declarative_base`) habiendo elegido 2.0 (`Mapped[...]`, `mapped_column`, `DeclarativeBase`). |
| A11 | Baja | `id = Column(String, primary_key=True, index=True)` sin default: nadie genera el identificador (y el `index=True` es redundante, la PK ya está indexada). Usar `UUID` de PostgreSQL con default. |
| A12 | Baja | `RegisterUser.execute` recibe un `dict` y devuelve lo que devuelva el repositorio: el caso de uso no tiene tipo de retorno definido. Toda la capa de aplicación carece de anotaciones de tipo. |

### 3.3 Faltantes estructurales frente a lo que exige SI2

Esto es lo que más pesa en la nota, y no es código: es diseño ausente.

| ID | Hallazgo |
|---|---|
| **F1** | **Multi-tenant: cero.** No hay tabla `tenants`, ni columna `tenant_id`, ni claim de tenant en el JWT, ni middleware. Es **CU-01 (Aprovisionar empresa)** y la **pregunta 3.d del examen final** (*"¿por qué un SaaS necesita multi-tenant y cuáles son los pasos para implementarlo?"*). El contexto maestro documenta que el Grupo 1 lo declaró en prosa sin implementarlo y el Grupo 7 lo metió tarde: es el error más repetido de la materia. Debe estar en el **primer** `CREATE TABLE`. |
| **F2** | **RBAC: cero.** `CU-05 Gestionar roles y permisos` no tiene ni entidad ni tabla. El JWT solo lleva `sub`. Sin esto no se puede proteger `GET /bitacora`, que el propio documento §28 marca como información sensible. |
| **F3** | **Bitácora desconectada.** Los §39 y §40 del documento describen `Auth → Bitácora`; en el código no hay ninguna llamada. La bitácora es `CU-06` y aparece en el paquete PA-01. |
| **F4** | **Sin capa de persistencia viva:** no existen `engine`, `async_sessionmaker`, `get_session()`, ni unidad de trabajo (transacción por request). Es la razón de fondo por la que las carpetas `persistence/` de `auth` están vacías. |
| **F5** | **Sin composición de dependencias.** Ningún `Depends`, ningún archivo `dependencies.py`. Los cuatro casos de uso de auth están escritos y **nadie los instancia**. |
| **F6** | **Sin versionado de API.** Todo cuelga de la raíz. Debería ser `/api/v1/...`. |
| **F7** | **Sin Docker, sin CI, sin seed de datos.** Con 6 integrantes, "en mi máquina funciona" es garantía de fricción. El contexto maestro §6.5 marca la falta de evidencia verificable (repo, despliegue, QR) como defecto recurrente. |
| **F8** | **Sin trazabilidad módulo → paquete → CU.** Ningún módulo declara a qué PA y a qué CU responde. Es justamente el diferenciador que ningún grupo anterior tuvo y que la docente enfatiza (trazabilidad ocupa 2 de 24 láminas de su material). |

---

## 4. Propuesta de nueva estructura

Mantiene las decisiones que ya tomaron (Vertical Slicing, Screaming Architecture, Hexagonal,
Repository, Alembic, JWT) y corrige lo que falta. Los cambios son **cinco**, no un rediseño.

### 4.1 Cambio 1 — Nombre real de paquete: `src/ssas/`

Resuelve §2.3. El *src-layout* necesita un paquete importable dentro de `src/`.

```toml
# pyproject.toml
[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Los imports pasan de `from src.config.settings import settings` a
`from ssas.config.settings import settings`, y el arranque a `uvicorn ssas.main:app`.
La decisión §6 del documento (*no usar `src/app/`*) se mantiene: `ssas` no es `app`, es el nombre del sistema.

> **Alternativa de menor fricción**, si no quieren tocar los imports: dejar `src/` como está, quitar
> `pip install -e .` del README, agregar `pythonpath = ["."]` a la configuración de pytest y arrancar
> siempre con `uvicorn src.main:app` desde la raíz. Funciona, pero el paquete deja de ser instalable.

### 4.2 Cambio 2 — Capa `core/`: lo que falta y explica la mitad de los huecos

El documento de arquitectura nunca dice dónde viven el engine, la sesión, la `Base`, el middleware de
tenant ni la composición de dependencias. Por eso hoy no existen. Esta es la adición más importante:

```
src/ssas/core/
├── db/
│   ├── base.py            # DeclarativeBase ÚNICA + convención de nombres de constraints
│   ├── session.py         # async engine + async_sessionmaker + get_session()
│   └── mixins.py          # TimestampMixin · TenantMixin(tenant_id) · SoftDeleteMixin
├── security/
│   ├── jwt.py             # PyJWT: claims sub, tid, type, jti, iat, exp
│   ├── hashing.py         # pwdlib Argon2id
│   └── dependencies.py    # get_current_user() · require_permission("usuarios:crear")
├── tenancy/
│   ├── context.py         # ContextVar con el tenant activo
│   └── middleware.py      # resuelve el tenant del JWT y lo fija en el contexto + SET LOCAL app.tenant_id
├── errors/
│   ├── base.py            # AppError, NotFound, Conflict, Forbidden
│   └── handlers.py        # AppError -> JSONResponse (registrado en main.py)
└── api/
    └── router.py          # APIRouter raíz /api/v1 que agrega todos los módulos
```

`core/` es infraestructura transversal **técnica**. `shared/` se mantiene como lo pide §30 del
documento —pequeño, solo tipos y excepciones de negocio compartidos— y no se mezcla con `core/`.

### 4.3 Cambio 3 — Módulos alineados a los paquetes PA-01 … PA-07

Cada módulo declara en su `__init__.py` a qué paquete y a qué casos de uso responde. Esto cierra F8
y da la matriz de trazabilidad RF → CU → HU → código que ningún grupo anterior tuvo.

| Paquete UML | Módulos en `src/ssas/` | CU cubiertos |
|---|---|---|
| **PA-01** Seguridad y Administración | `tenants` · `auth` · `usuarios` · `roles` · `bitacora` | CU-01 … CU-06 |
| **PA-02** Reclutamiento | `vacantes` · `postulaciones` · `portal_empleo` | CU-07 … CU-11 |
| **PA-03** Selección | `seleccion` · `entrevistas` · `ofertas` | CU-12 … CU-16 |
| **PA-04** Administración de Personal | `colaboradores` · `contratos` · `planilla` · `asistencia` · `ausencias` | CU-17 … CU-25 |
| **PA-05** Capacitación | `capacitacion` | CU-26 … CU-28 |
| **PA-06** Inteligencia Artificial | `ia` (`documentos`, `ranking`, `chatbot`, `rotacion`) | CU-29 … CU-32 |
| **PA-07** Reportes e Indicadores | `reportes` · `notificaciones` | CU-33 … CU-35 |

**Convención de idioma** (para no repetir la contradicción §6.6 del contexto maestro): nombres de
**negocio en español**, porque así están escritos los CU que lee la docente y así la trazabilidad es
directa; nombres de **capa técnica en inglés** (`domain`, `application`, `api`), porque son términos
de arquitectura. Regla escrita, aplicada sin excepciones. Hoy el documento §46 mezcla los dos criterios
(`bitacora` junto a `employees`, `recruitment`, `payroll`).

Los 19 módulos **no se crean ahora**: se crean cuando entra su primera historia de usuario
(es la regla §47 del propio documento, que hoy está incumplida).

### 4.4 Cambio 4 — Estructura interna del módulo, simplificada

El punto sensible es **A3**: hoy cada dato se escribe dos veces (DTO + Schema), ambos en Pydantic,
sin transformación entre ellos. Con 35 casos de uso eso son ~70 clases redundantes.

**Regla propuesta:** un DTO de aplicación existe **solo cuando el caso de uso se invoca desde más de
un adaptador** (HTTP + worker de notificaciones + tarea programada). Si solo lo llama HTTP, el schema
Pydantic del router basta y el DTO es la sobrearquitectura que §44 prohíbe. Cuando sí exista, el DTO
es un `@dataclass(frozen=True)` **sin Pydantic** — así se cumple §9 de verdad.

```
src/ssas/auth/
├── __init__.py                     # Paquete: PA-01 · CU: CU-03, CU-04
├── domain/
│   ├── entities/user.py            # dataclass puro, sin Pydantic ni SQLAlchemy
│   ├── value_objects/email.py      # solo si encapsula reglas propias (§10)
│   └── exceptions.py               # InvalidCredentials, UserAlreadyExists... y SE USAN
├── application/
│   ├── ports/                      # ← movido desde ports/outgoing/
│   │   ├── user_repository.py
│   │   └── refresh_token_repository.py
│   └── use_cases/
│       ├── login_user.py           # async def execute(...)
│       ├── register_user.py
│       ├── refresh_token.py
│       └── logout_user.py
├── infrastructure/
│   ├── persistence/
│   │   ├── models/user.py                        # Mapped[...] sobre la Base ÚNICA de core.db
│   │   ├── mappers/user_mapper.py                # ORM ↔ entidad de dominio
│   │   └── repositories/sqlalchemy_user_repository.py
│   └── (security/ ya no: JWT y hashing viven en core/security, son transversales)
└── api/
    ├── routes.py                   # POST /api/v1/auth/login|register|refresh|logout
    ├── schemas.py                  # Pydantic, solo entrada/salida HTTP
    └── dependencies.py             # composición: arma el caso de uso con sus adapters
```

Dos ajustes menores respecto al documento actual:

- **`ports/` pasa a `application/ports/`.** Un puerto es una necesidad *de la capa de aplicación*;
  como carpeta hermana de `domain/` y `application/` queda ambiguo quién lo posee. Y se elimina el
  nivel `outgoing/`: el §49 ya decidió que no habrá puertos *incoming*, así que una carpeta
  `outgoing/` sin hermana es ruido. (Es una decisión discutible, no un error — lo importante es
  fijarla por escrito y no cambiarla en el Sprint 3.)
- **`infrastructure/http/` pasa a `api/`.** Más corto, y `routes.py` deja claro que ahí hay endpoints.
  Si prefieren respetar el documento al pie de la letra, `infrastructure/http/` es igual de válido:
  lo único que no se puede es tener las dos convenciones conviviendo.

### 4.5 Cambio 5 — Multi-tenant desde la primera tabla

Aunque la estrategia todavía no está decidida (quedó pendiente), la estructura debe soportarla desde
ya. El costo de dejar el hueco preparado es cero; el de retrofitear 40 tablas, altísimo:

1. `core/db/mixins.py::TenantMixin` con `tenant_id: Mapped[UUID]` indexado → **toda** tabla de negocio
   lo hereda desde su primera migración.
2. El JWT lleva el claim `tid` además de `sub` (`core/security/jwt.py`).
3. `core/tenancy/middleware.py` resuelve el tenant del token y lo deja en un `ContextVar`.
4. El repositorio base lee ese `ContextVar` y filtra — y, si adoptan RLS, además emite
   `SET LOCAL app.tenant_id` al abrir la transacción, para que la aislación la garantice PostgreSQL
   y no la disciplina del programador.

Con eso, la pregunta 3.d del examen final ("los pasos para implementarlo") se responde señalando
cuatro archivos del repositorio.

### 4.6 Árbol resultante

```
backend_ssas_rrhh/
├── pyproject.toml · README.md · .env.example · .gitignore
├── docker-compose.yml            # postgres + api (opcional pero recomendado, cierra F7)
├── alembic.ini
├── migrations/
│   ├── env.py                    # target_metadata = Base.metadata  ← la Base ÚNICA
│   └── versions/
├── tests/
│   ├── conftest.py               # fixtures: engine de test, sesión, cliente httpx
│   ├── unit/                     # casos de uso con puertos falsos
│   ├── integration/              # repositorios contra PostgreSQL real
│   └── e2e/                      # POST /api/v1/auth/login de punta a punta
└── src/ssas/
    ├── main.py                   # FastAPI + CORS + handlers + router /api/v1
    ├── config/settings.py
    ├── core/                     # db · security · tenancy · errors · api   ← §4.2
    ├── shared/                   # tipos y excepciones de negocio (pequeño)
    │
    ├── tenants/                  # PA-01 · CU-01, CU-02
    ├── auth/                     # PA-01 · CU-03
    ├── usuarios/                 # PA-01 · CU-04
    ├── roles/                    # PA-01 · CU-05
    ├── bitacora/                 # PA-01 · CU-06
    └── ...                       # los demás módulos entran cuando entra su HU
```

---

## 5. Las cinco decisiones a cerrar antes de seguir

| # | Decisión | Recomendación | Por qué ahora |
|---|---|---|---|
| 1 | Nombre del paquete Python | `src/ssas/` + `packages.find` | Después son 34+ archivos de imports a tocar |
| 2 | Sync o async de punta a punta | **Async** (ya elegiste SQLAlchemy 2.0 async) | Los puertos definen la firma; cambiarla después toca los 35 casos de uso |
| 3 | DTO vs Schema | DTO **solo** con más de un adaptador; dataclass, no Pydantic | Es la diferencia entre 35 y 70 clases nuevas |
| 4 | Estrategia multi-tenant | `tenant_id` + RLS de PostgreSQL | Va en la primera migración o no va |
| 5 | Convención de idioma y de nombres de adapter | Negocio en español, capa técnica en inglés; adapters `SqlAlchemy*Repository` | Evita el defecto §6.6 del contexto maestro |

---

## 6. Plan de trabajo sugerido (Sprint 0)

Antes de escribir el primer endpoint real:

1. **Arreglar los tres bloqueantes de §2** — settings, hashing, packaging. Es media jornada y hoy
   nada funciona sin eso.
2. **Levantar `core/db`**: `Base` única con convención de nombres de constraints, engine async,
   `get_session()` con transacción por request.
3. **Inicializar Alembic** (`alembic init -t async migrations`) apuntando `target_metadata` a esa Base.
4. **Migración 001**: `tenants`, `usuarios`, `roles`, `permisos`, `rol_permiso`, `usuario_rol`,
   `refresh_tokens`, `audit_logs` — todas con `tenant_id` salvo `tenants`.
5. **Cerrar `auth` de verdad**: `SqlAlchemyUserRepository`, `RefreshTokenRepository` (para rotación
   y revocación), `core/security/jwt.py` con `type` + `jti`, `get_current_user`, `require_permission`.
6. **Conectar bitácora a auth**: `LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `USER_CREATED`.
7. **Tres pruebas mínimas** — una por nivel: `LoginUser` con puertos falsos (unit), el repositorio
   contra PostgreSQL (integration), `POST /api/v1/auth/login` completo (e2e). No para tener cobertura,
   sino para que la sección "2.3 Pruebas" de la plantilla de sprint tenga contenido real (§6.1 del
   contexto maestro: es la sección que todos los grupos dejan vacía).
8. **Actualizar `ARQUITECTURA_BACKEND_FASTAPI.md`** con las cinco decisiones de §5. El documento es
   un entregable del Capítulo 2; que quede desalineado del código es exactamente el defecto §6.6.

---

## 7. Lo que este backend hace bien

Para que el balance sea justo:

- El documento de arquitectura **existe, es coherente internamente y es defendible**. Las secciones
  §41 (entidad vs modelo ORM), §42 (repository vs ORM), §43 (regla de dependencias), §44 y §50
  (anti-sobrearquitectura) son material directo para el Capítulo 2 y para la defensa.
- La separación en puertos y adapters está **bien entendida**: `BcryptPasswordHasher` implementando
  `PasswordHasher` es el ejemplo canónico, correcto.
- Las excepciones de dominio están **bien diseñadas** (jerarquía con base `AuthError`); solo falta usarlas.
- La elección de `pyproject.toml` sobre `requirements.txt`, y de `.env.example` versionado con `.env`
  ignorado, es la práctica correcta.
- Vertical Slicing es **la decisión acertada** para un sistema de 7 paquetes y 35 casos de uso
  repartido entre 6 personas: permite que dos integrantes trabajen en `planilla` y `reclutamiento`
  sin tocarse los mismos archivos. Un backend organizado por `controllers/services/models` habría
  generado conflictos de merge todas las semanas.

El trabajo pendiente es de implementación y de cinco decisiones, no de rediseño.

---

### Fuentes

- `backend_ssas_rrhh/` — código y `ARQUITECTURA_BACKEND_FASTAPI.md` (34 archivos analizados)
- `Sistemas de Informacion 2/CONTEXTO_MAESTRO_SI2.md` — patrones de fallo, evaluación y calendario
- `Diagramas_UML_Grupo12/PA-01…PA-07.puml` — paquetes y casos de uso del Grupo 12
- Documentación oficial de FastAPI — [Security: OAuth2 with JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) (`PyJWT`, `pwdlib[argon2]`)
- [PyPI · passlib](https://pypi.org/project/passlib/) — última publicación 1.7.4, 08/10/2020
- Verificaciones ejecutadas en sandbox: pydantic-settings 2.x, passlib 1.7.4 + bcrypt 5.0.0,
  setuptools src-layout, pwdlib 0.3.1 + PyJWT 2.12.1

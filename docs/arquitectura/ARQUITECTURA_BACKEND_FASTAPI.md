# Arquitectura Backend --- Python + FastAPI

## Documento de arquitectura y guía de trabajo

**Proyecto:** Backend API\
**Tecnologías base:** Python + FastAPI\
**Estilo arquitectónico:** Vertical Slicing + Screaming Architecture +
Hexagonal Architecture\
**Persistencia:** ORM + Repository Pattern + PostgreSQL\
**Migraciones:** Alembic\
**Seguridad:** Autenticación, JWT y hashing de contraseñas\
**Módulos iniciales:** Auth y Bitácora

------------------------------------------------------------------------

# 1. Objetivo del documento

Este documento define cómo se organizará y desarrollará el backend.

La intención no es solamente establecer carpetas. Cada componente debe
tener una responsabilidad clara y debe existir porque resuelve una
necesidad concreta.

La arquitectura combinará:

-   **Vertical Slicing:** el sistema se organiza por funcionalidades de
    negocio.
-   **Screaming Architecture:** los nombres del código deben mostrar qué
    hace el sistema.
-   **Hexagonal Architecture:** el núcleo de la aplicación no debe
    depender directamente de tecnologías externas.
-   **Domain / Application / Infrastructure:** separación de
    responsabilidades dentro de cada módulo.
-   **DTOs:** transporte de datos entre fronteras.
-   **Ports:** contratos para comunicarse con dependencias externas.
-   **Adapters:** implementaciones concretas de esos contratos.
-   **ORM:** representación de persistencia mediante modelos.
-   **Repositories:** acceso abstracto a los datos.
-   **Migrations:** evolución controlada del esquema de la base de
    datos.
-   **Testing:** pruebas unitarias, de integración y end-to-end.

La regla principal será:

> No se agregará una abstracción únicamente porque sea habitual en una
> arquitectura avanzada. Cada componente deberá justificar qué problema
> resuelve.

------------------------------------------------------------------------

# 2. Estructura general

``` text
backend/
│
├── src/
│   │
│   ├── auth/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   ├── value_objects/
│   │   │   └── exceptions.py
│   │   │
│   │   ├── application/
│   │   │   ├── dto/
│   │   │   │   ├── login.py
│   │   │   │   └── register.py
│   │   │   │
│   │   │   └── use_cases/
│   │   │       ├── login_user.py
│   │   │       ├── register_user.py
│   │   │       ├── refresh_token.py
│   │   │       └── logout_user.py
│   │   │
│   │   ├── ports/
│   │   │   └── outgoing/
│   │   │       ├── user_repository.py
│   │   │       ├── password_hasher.py
│   │   │       └── token_service.py
│   │   │
│   │   └── infrastructure/
│   │       ├── http/
│   │       │   ├── router.py
│   │       │   └── schemas.py
│   │       │
│   │       ├── persistence/
│   │       │   ├── models/
│   │       │   └── repositories/
│   │       │
│   │       └── security/
│   │           ├── password_hasher.py
│   │           └── jwt_service.py
│   │
│   ├── bitacora/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   └── audit_log.py
│   │   │   ├── value_objects/
│   │   │   └── exceptions.py
│   │   │
│   │   ├── application/
│   │   │   ├── dto/
│   │   │   │   ├── audit_log_response.py
│   │   │   │   └── audit_log_filter.py
│   │   │   │
│   │   │   └── use_cases/
│   │   │       ├── register_audit_event.py
│   │   │       ├── list_audit_logs.py
│   │   │       └── get_audit_log.py
│   │   │
│   │   ├── ports/
│   │   │   └── outgoing/
│   │   │       └── audit_log_repository.py
│   │   │
│   │   └── infrastructure/
│   │       ├── http/
│   │       │   ├── router.py
│   │       │   └── schemas.py
│   │       │
│   │       └── persistence/
│   │           ├── models/
│   │           │   └── audit_log.py
│   │           └── repositories/
│   │               └── audit_log_repository.py
│   │
│   ├── shared/
│   │   ├── exceptions/
│   │   └── types/
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── main.py
│
├── migrations/
│   └── versions/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

------------------------------------------------------------------------

# 3. Principio principal: Vertical Slicing

La primera decisión arquitectónica es organizar el sistema por
funcionalidades.

Por ejemplo:

``` text
src/
├── auth/
├── bitacora/
├── users/
├── roles/
├── empleados/
├── reclutamiento/
└── ...
```

Cada módulo representa una capacidad funcional.

Esto es diferente de organizar todo el proyecto así:

``` text
controllers/
services/
repositories/
models/
```

En la organización por Vertical Slicing, todo lo relacionado con una
funcionalidad permanece cerca.

Por ejemplo:

``` text
auth/
├── domain/
├── application/
├── ports/
└── infrastructure/
```

Por lo tanto, `auth` es una unidad funcional y dentro de ella se aplican
las responsabilidades de la arquitectura hexagonal.

------------------------------------------------------------------------

# 4. Screaming Architecture

Screaming Architecture no es una carpeta específica.

Es un principio de organización y nomenclatura.

El proyecto debe comunicar qué hace el sistema.

Por ejemplo, esto:

``` text
src/
├── auth/
├── bitacora/
├── users/
└── empleados/
```

comunica más información de negocio que:

``` text
src/
├── controllers/
├── services/
├── repositories/
└── models/
```

Dentro de `auth` también utilizaremos nombres que expresen acciones
reales:

``` text
register_user.py
login_user.py
refresh_token.py
logout_user.py
```

Estos nombres representan casos de uso.

La regla será:

> El código debe hablar en términos del negocio y no solamente en
> términos técnicos.

------------------------------------------------------------------------

# 5. Hexagonal Architecture

La arquitectura hexagonal busca que el núcleo de la aplicación no
dependa directamente de tecnologías externas.

El flujo conceptual es:

``` text
Cliente HTTP
     │
     ▼
Incoming Adapter
     │
     ▼
DTO
     │
     ▼
Use Case
     │
     ▼
Domain
     │
     ▼
Outgoing Port
     │
     ▼
Outgoing Adapter
     │
     ▼
Base de datos / servicio externo
```

En nuestro backend:

``` text
FastAPI
   ↓
HTTP Adapter
   ↓
DTO
   ↓
Use Case
   ↓
Domain
   ↓
Repository Port
   ↓
Repository Adapter
   ↓
ORM
   ↓
PostgreSQL
```

------------------------------------------------------------------------

# 6. `src/`

## Responsabilidad

`src/` contiene el código fuente principal del backend.

No representa una funcionalidad del negocio.

Es simplemente la frontera del código Python de la aplicación.

Por eso decidimos no utilizar:

``` text
backend/src/app/
```

La carpeta `app` sería redundante para nuestro contexto porque este
repositorio contiene exclusivamente nuestro backend.

Utilizaremos:

``` text
backend/src/
```

directamente.

------------------------------------------------------------------------

# 7. `src/main.py`

Es el punto de entrada de FastAPI.

Responsabilidades principales:

-   Crear la instancia de FastAPI.
-   Registrar routers.
-   Registrar handlers globales.
-   Configurar middleware cuando sea necesario.
-   Ejecutar la composición inicial de dependencias.

No debe contener:

-   Reglas de negocio.
-   Consultas SQL.
-   Lógica de autenticación.
-   Lógica de usuarios.
-   Reglas de bitácora.

Conceptualmente:

``` text
main.py
   │
   ├── FastAPI()
   ├── registrar auth router
   ├── registrar bitacora router
   └── configuración general
```

------------------------------------------------------------------------

# 8. Módulo `auth`

``` text
src/auth/
```

Representa la funcionalidad de autenticación y seguridad relacionada con
la sesión del usuario.

Inicialmente tendrá:

-   Registro.
-   Login.
-   Refresh token.
-   Logout.
-   Hash/verificación de contraseñas.
-   Generación/verificación de tokens.

El módulo está dividido internamente en:

``` text
auth/
├── domain/
├── application/
├── ports/
└── infrastructure/
```

------------------------------------------------------------------------

# 9. `auth/domain/`

El dominio representa las reglas y conceptos propios del negocio.

Debe mantenerse independiente de:

-   FastAPI.
-   SQLAlchemy.
-   PostgreSQL.
-   JWT.
-   Redis.
-   Pydantic.

## `auth/domain/entities/`

Contiene entidades de dominio.

Una entidad tiene identidad y representa un concepto del negocio.

Ejemplo conceptual:

``` text
User
├── id
├── email
├── password
└── status
```

La entidad no debe convertirse simplemente en un modelo ORM.

------------------------------------------------------------------------

# 10. `auth/domain/value_objects/`

Los Value Objects representan conceptos cuyo valor y reglas son
importantes para el dominio.

Ejemplos:

``` text
Email
Password
```

Un Value Object puede encapsular validaciones propias.

La idea es evitar que todas las reglas terminen dispersas por los casos
de uso.

No se debe crear un Value Object solamente para cada dato simple.

Debe existir cuando el concepto tenga comportamiento o reglas propias
que justifiquen su existencia.

------------------------------------------------------------------------

# 11. `auth/domain/exceptions.py`

Contiene excepciones propias del dominio de autenticación.

Ejemplos conceptuales:

``` text
InvalidCredentials
InvalidEmail
UserAlreadyExists
InvalidAuthenticationState
```

Las excepciones de dominio no deberían depender de HTTP.

El dominio no debería lanzar directamente:

``` text
HTTPException
```

porque eso acoplaría el dominio a FastAPI.

------------------------------------------------------------------------

# 12. `auth/application/`

La capa Application coordina los casos de uso.

Aquí está la respuesta a:

> ¿Qué puede hacer el sistema?

Ejemplos:

``` text
LoginUser
RegisterUser
RefreshToken
LogoutUser
```

Application utiliza el dominio y los puertos, pero no debe depender
directamente de implementaciones concretas de infraestructura.

------------------------------------------------------------------------

# 13. `auth/application/dto/`

DTO significa Data Transfer Object.

Su función es transportar información entre fronteras.

Ejemplo:

``` text
Register DTO

name
email
password
```

El DTO no representa necesariamente la entidad completa.

Un DTO puede representar específicamente la información que necesita una
operación.

Por ejemplo:

``` text
Login DTO

email
password
```

mientras:

``` text
Register DTO

name
email
password
```

Esto evita utilizar un único objeto gigante para todas las operaciones.

------------------------------------------------------------------------

# 14. `auth/application/use_cases/`

Aquí están las acciones concretas del sistema.

``` text
login_user.py
register_user.py
refresh_token.py
logout_user.py
```

Cada archivo representa un caso de uso.

## `login_user.py`

Responsabilidad conceptual:

``` text
1. Recibir credenciales.
2. Buscar usuario.
3. Verificar contraseña.
4. Crear token.
5. Devolver resultado.
```

## `register_user.py`

Responsabilidad conceptual:

``` text
1. Recibir datos.
2. Comprobar existencia del usuario.
3. Crear entidad.
4. Proteger contraseña.
5. Persistir usuario.
6. Generar resultado.
```

## `refresh_token.py`

Renueva el acceso cuando el flujo de autenticación lo requiera.

## `logout_user.py`

Implementa la lógica necesaria para cerrar la sesión según el mecanismo
de autenticación elegido.

------------------------------------------------------------------------

# 15. `auth/ports/outgoing/`

Aquí aparecen los puertos de salida de Hexagonal Architecture.

Un puerto define una necesidad de la aplicación sin especificar la
tecnología concreta que la resolverá.

Tenemos:

``` text
user_repository.py
password_hasher.py
token_service.py
```

## `user_repository.py`

Dice:

> Necesito una forma de buscar y persistir usuarios.

No dice:

> Necesito SQLAlchemy.

El caso de uso puede trabajar conceptualmente con:

``` text
get_by_email()
get_by_id()
save()
update()
```

La implementación concreta estará en Infrastructure.

------------------------------------------------------------------------

## `password_hasher.py`

Dice:

> Necesito proteger y verificar contraseñas.

El caso de uso no necesita conocer los detalles de Argon2, bcrypt u otra
implementación.

Conceptualmente:

``` text
hash(password)
verify(password, hash)
```

La implementación concreta estará en:

``` text
auth/infrastructure/security/
```

------------------------------------------------------------------------

## `token_service.py`

Dice:

> Necesito crear y verificar tokens de autenticación.

El caso de uso no necesita conocer los detalles de JWT.

La implementación concreta estará en:

``` text
auth/infrastructure/security/jwt_service.py
```

------------------------------------------------------------------------

# 16. `auth/infrastructure/`

Infrastructure contiene detalles tecnológicos.

Aquí sí pueden aparecer:

-   FastAPI.
-   SQLAlchemy.
-   PostgreSQL.
-   JWT.
-   Librerías de hashing.
-   Configuración específica de infraestructura.

La infraestructura implementa los contratos que necesita Application.

------------------------------------------------------------------------

# 17. `auth/infrastructure/http/`

Es el adaptador de entrada HTTP.

## `router.py`

Define endpoints FastAPI.

Ejemplo conceptual:

``` text
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
```

El router no debe contener toda la lógica de negocio.

Su función es traducir:

``` text
HTTP Request
```

hacia:

``` text
DTO + Use Case
```

y posteriormente transformar el resultado en:

``` text
HTTP Response
```

------------------------------------------------------------------------

# 18. `auth/infrastructure/http/schemas.py`

Aquí viven los esquemas específicos de FastAPI/Pydantic para HTTP.

Es importante distinguir:

``` text
DTO
```

de:

``` text
HTTP Schema
```

El schema puede conocer Pydantic/FastAPI porque está en Infrastructure.

El DTO representa el contrato que necesita Application.

Cuando sea conveniente, el adapter transforma:

``` text
Pydantic Request Schema
        ↓
Application DTO
```

De esta forma el dominio y la aplicación no necesitan conocer FastAPI.

------------------------------------------------------------------------

# 19. `auth/infrastructure/persistence/`

Contiene la implementación concreta de persistencia.

Aquí entra:

``` text
ORM
Repository
Database Mapping
```

------------------------------------------------------------------------

# 20. `auth/infrastructure/persistence/models/`

Aquí están los modelos ORM.

Por ejemplo:

``` text
UserModel
```

Este modelo conoce:

-   tablas.
-   columnas.
-   claves.
-   relaciones.
-   índices.
-   configuración ORM.

Este objeto es diferente de la entidad de dominio.

Conceptualmente:

``` text
Domain User
       ↕
     Mapper
       ↕
ORM UserModel
```

La separación evita contaminar el dominio con detalles de SQLAlchemy.

------------------------------------------------------------------------

# 21. `auth/infrastructure/persistence/repositories/`

Aquí están las implementaciones concretas de los repositories.

Ejemplo:

``` text
PostgresUserRepository
```

Implementa el contrato:

``` text
auth/ports/outgoing/user_repository.py
```

El flujo es:

``` text
Use Case
   ↓
UserRepository PORT
   ↑
PostgresUserRepository
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

Esta es una de las aplicaciones principales de Hexagonal Architecture.

------------------------------------------------------------------------

# 22. `auth/infrastructure/security/`

Aquí están las implementaciones tecnológicas relacionadas con seguridad.

## `password_hasher.py`

Implementa el puerto:

``` text
auth/ports/outgoing/password_hasher.py
```

Puede utilizar el algoritmo/librería de hashing que decidamos.

## `jwt_service.py`

Implementa:

``` text
auth/ports/outgoing/token_service.py
```

y contiene los detalles de generación/verificación de JWT.

------------------------------------------------------------------------

# 23. Módulo `bitacora`

``` text
src/bitacora/
```

Representa la auditoría del sistema.

No debe confundirse con un simple archivo de logs técnicos.

La bitácora registra eventos de negocio/auditoría.

Ejemplos:

``` text
LOGIN_SUCCESS
LOGIN_FAILED
LOGOUT
USER_CREATED
USER_UPDATED
ROLE_ASSIGNED
```

y posteriormente eventos de otros módulos.

------------------------------------------------------------------------

# 24. `bitacora/domain/entities/audit_log.py`

Representa el evento de auditoría como concepto del dominio.

Conceptualmente puede contener:

``` text
id
user_id
action
resource
resource_id
timestamp
metadata
```

La estructura final dependerá del modelo funcional que definamos.

------------------------------------------------------------------------

# 25. `bitacora/application/dto/`

Contiene DTOs relacionados con Bitácora.

## `audit_log_response.py`

Representa la información que Application necesita entregar como
resultado.

## `audit_log_filter.py`

Representa criterios para consultar la bitácora.

Ejemplos:

``` text
fecha_inicio
fecha_fin
usuario
acción
recurso
```

------------------------------------------------------------------------

# 26. `bitacora/application/use_cases/`

Contiene las acciones de la bitácora.

## `register_audit_event.py`

Registra un evento.

Ejemplo:

``` text
LOGIN_FAILED
```

## `list_audit_logs.py`

Consulta múltiples registros y permite aplicar filtros.

## `get_audit_log.py`

Obtiene un evento específico.

------------------------------------------------------------------------

# 27. `bitacora/ports/outgoing/`

Contiene el contrato:

``` text
audit_log_repository.py
```

Dice:

> Necesito una forma de persistir y consultar eventos de auditoría.

No conoce SQLAlchemy ni PostgreSQL.

------------------------------------------------------------------------

# 28. `bitacora/infrastructure/http/`

Contiene el adaptador HTTP.

Ejemplos conceptuales:

``` text
GET /bitacora
GET /bitacora/{id}
```

La bitácora deberá tener especial cuidado con autorización y permisos
porque contiene información sensible.

------------------------------------------------------------------------

# 29. `bitacora/infrastructure/persistence/`

Contiene:

``` text
models/
repositories/
```

## `models/audit_log.py`

Modelo ORM de la tabla de auditoría.

## `repositories/audit_log_repository.py`

Implementación concreta del puerto:

``` text
AuditLogRepository
```

utilizando el ORM.

------------------------------------------------------------------------

# 30. `shared/`

Debe ser pequeño.

Contendrá elementos realmente compartidos entre módulos.

``` text
shared/
├── exceptions/
└── types/
```

No debe convertirse en un depósito general de código.

Regla:

> Si algo pertenece claramente a `auth`, permanece en `auth`. Si
> pertenece a `bitacora`, permanece en `bitacora`.

Solo se mueve a `shared` cuando realmente existe una responsabilidad
común.

------------------------------------------------------------------------

# 31. `config/`

Contiene configuración de la aplicación.

``` text
config/
└── settings.py
```

Aquí se centralizarán configuraciones como:

``` text
DATABASE_URL
JWT_SECRET
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE
ENVIRONMENT
```

Los valores sensibles se obtendrán desde `.env` y no se escribirán
directamente en el código.

------------------------------------------------------------------------

# 32. `.env`

Contendrá variables de entorno locales.

Ejemplo conceptual:

``` text
DATABASE_URL=...
JWT_SECRET=...
```

Nunca debe subirse al repositorio si contiene secretos reales.

------------------------------------------------------------------------

# 33. `.env.example`

Documenta las variables necesarias sin contener secretos reales.

Ejemplo:

``` text
DATABASE_URL=
JWT_SECRET=
JWT_ALGORITHM=
```

Sirve para que otro desarrollador pueda saber qué configuración
necesita.

------------------------------------------------------------------------

# 34. `migrations/`

Contiene la evolución del esquema de base de datos.

Utilizaremos Alembic.

``` text
migrations/
└── versions/
```

Cada archivo representa una modificación controlada del esquema.

Ejemplo:

``` text
001_create_users.py
002_create_roles.py
003_create_audit_logs.py
```

Las migraciones son diferentes de los modelos ORM.

``` text
ORM Model
   │
   │ representa
   ▼
Estructura esperada

Migration
   │
   │ transforma
   ▼
Base de datos actual
```

------------------------------------------------------------------------

# 35. `tests/`

Separamos las pruebas según su alcance.

``` text
tests/
├── unit/
├── integration/
└── e2e/
```

## `unit/`

Prueban componentes aislados.

Ejemplo:

``` text
LoginUser
```

utilizando dobles/mocks/fakes para los puertos.

No necesita necesariamente PostgreSQL real.

## `integration/`

Comprueban que componentes reales trabajen juntos.

Ejemplo:

``` text
Repository
+
SQLAlchemy
+
PostgreSQL
```

## `e2e/`

Prueban el sistema desde el punto de vista de un cliente.

Ejemplo:

``` text
POST /auth/login
       ↓
FastAPI
       ↓
Use Case
       ↓
Repository
       ↓
Database
```

------------------------------------------------------------------------

# 36. `pyproject.toml`

Será el archivo principal de configuración del proyecto Python.

Aquí podremos definir:

-   nombre del proyecto.
-   versión.
-   dependencias.
-   herramientas.
-   configuración de testing.
-   configuración de linting/formatting cuando corresponda.

Preferiremos `pyproject.toml` frente a depender exclusivamente de un
`requirements.txt`.

------------------------------------------------------------------------

# 37. `README.md`

Documentará:

-   objetivo del backend.
-   instalación.
-   configuración.
-   ejecución.
-   arquitectura.
-   variables de entorno.
-   migraciones.
-   pruebas.
-   endpoints principales.

Este documento de arquitectura complementará al README.

------------------------------------------------------------------------

# 38. Flujo completo de una petición

Ejemplo:

``` text
POST /auth/login
```

El flujo esperado es:

``` text
┌─────────────────────┐
│ Cliente HTTP        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FastAPI Router      │
│ Infrastructure      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ HTTP Schema         │
│ Pydantic            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Application DTO     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ LoginUser           │
│ Use Case            │
└──────────┬──────────┘
           │
           ├──────────────► UserRepository PORT
           │                         │
           │                         ▼
           │                  Repository Adapter
           │                         │
           │                         ▼
           │                       ORM
           │                         │
           │                         ▼
           │                    PostgreSQL
           │
           ├──────────────► PasswordHasher PORT
           │                         │
           │                         ▼
           │                    Hash Adapter
           │
           └──────────────► TokenService PORT
                                     │
                                     ▼
                                JWT Adapter
```

------------------------------------------------------------------------

# 39. Flujo de registro

``` text
POST /auth/register
        │
        ▼
HTTP Schema
        │
        ▼
Register DTO
        │
        ▼
RegisterUser
        │
        ├── comprobar usuario existente
        │
        ├── crear entidad User
        │
        ├── hash password
        │
        ├── guardar mediante UserRepository
        │
        └── registrar evento de auditoría
                    │
                    ▼
                Bitácora
```

Este flujo muestra por qué existen los puertos.

El caso de uso no necesita conocer directamente PostgreSQL, JWT o el
algoritmo de hashing.

------------------------------------------------------------------------

# 40. Relación Auth → Bitácora

Bitácora será un módulo transversal.

Ejemplo:

``` text
Auth
 │
 │ genera evento
 ▼
Bitácora
 │
 ▼
AuditLogRepository
 │
 ▼
ORM
 │
 ▼
PostgreSQL
```

Otros módulos también podrán generar eventos:

``` text
Users ──────────┐
Auth ───────────┤
Roles ──────────┤
Employees ──────┤
Recruitment ────┤
Payroll ────────┤
                 ▼
              Bitácora
```

Bitácora no debe depender de cada módulo.

Los módulos generan eventos; Bitácora se encarga de registrarlos.

------------------------------------------------------------------------

# 41. ORM vs Domain Entity

No se deben confundir.

## Domain Entity

Representa el negocio.

``` text
User
```

## ORM Model

Representa la persistencia.

``` text
UserModel
```

Conceptualmente:

``` text
Domain Entity
     │
     ▼
   Mapper
     │
     ▼
 ORM Model
     │
     ▼
Database
```

Esto permite cambiar detalles de persistencia sin modificar las reglas
del dominio.

------------------------------------------------------------------------

# 42. Repository vs ORM

Tampoco son lo mismo.

### Repository

Es una abstracción para acceder a datos.

``` text
UserRepository
```

### ORM

Es una tecnología/mecanismo para mapear objetos a tablas.

``` text
SQLAlchemy
```

### Implementación

``` text
PostgresUserRepository
```

puede utilizar SQLAlchemy.

Por tanto:

``` text
Use Case
   ↓
Repository Port
   ↓
Repository Adapter
   ↓
SQLAlchemy
   ↓
PostgreSQL
```

------------------------------------------------------------------------

# 43. Regla de dependencias

La dirección conceptual será:

``` text
Infrastructure
       ↓
Application
       ↓
Domain
```

El dominio no debe depender de infraestructura.

Por ejemplo:

### Incorrecto

``` text
Domain User
   ↓
SQLAlchemy
```

### Correcto

``` text
Domain User

Infrastructure
   ↓
SQLAlchemy
```

La infraestructura implementa los mecanismos externos que necesita la
aplicación.

------------------------------------------------------------------------

# 44. Regla contra la sobrearquitectura

No se crearán archivos o interfaces solamente para aumentar la cantidad
de capas.

Antes de agregar algo preguntaremos:

1.  ¿Qué problema resuelve?
2.  ¿Qué dependencia estamos aislando?
3.  ¿Qué responsabilidad tiene?
4.  ¿Qué parte del sistema lo necesita?
5.  ¿Podemos resolverlo sin introducir otra abstracción?

Ejemplo:

Si `LoginUser` necesita un servicio de tokens, `TokenService` tiene
sentido.

Pero crear:

``` text
TokenFactory
TokenBuilder
TokenManager
TokenProvider
TokenHelper
```

sin una necesidad real no tiene sentido.

------------------------------------------------------------------------

# 45. Principio final de diseño

La arquitectura debe cumplir:

``` text
Negocio visible
      +
Responsabilidades separadas
      +
Dependencias controladas
      +
Persistencia desacoplada
      +
Pruebas posibles
      +
Capacidad de crecimiento
```

No buscamos la mayor cantidad de carpetas.

Buscamos que cada carpeta y cada archivo tenga una razón clara para
existir.

------------------------------------------------------------------------

# 46. Evolución prevista

Inicialmente:

``` text
src/
├── auth/
└── bitacora/
```

Posteriormente podrán aparecer módulos funcionales:

``` text
src/
├── auth/
├── bitacora/
├── users/
├── roles/
├── employees/
├── recruitment/
├── selection/
├── training/
├── payroll/
└── vacations/
```

Cada módulo seguirá el mismo principio:

``` text
module/
├── domain/
├── application/
├── ports/
└── infrastructure/
```

Pero la estructura interna se ajustará a la complejidad real del módulo.

No todos los módulos necesariamente necesitarán exactamente los mismos
componentes.

------------------------------------------------------------------------

# 47. Regla de trabajo para el desarrollo

Construiremos el backend de forma incremental.

Para cada nueva funcionalidad:

``` text
1. Definir el caso de uso.
2. Identificar las reglas de dominio.
3. Definir DTO si es necesario.
4. Identificar dependencias externas.
5. Crear Ports para las dependencias que necesiten abstracción.
6. Implementar Adapters.
7. Implementar ORM Models.
8. Implementar Repository.
9. Crear/actualizar Migration.
10. Crear endpoint FastAPI.
11. Probar unitariamente.
12. Probar integración.
13. Probar E2E cuando corresponda.
```

No se crearán todas las carpetas anticipadamente.

------------------------------------------------------------------------

# 48. Arquitectura resumida

``` text
                    BACKEND
                       │
                      src
                       │
          ┌────────────┴────────────┐
          │                         │
         AUTH                    BITÁCORA
          │                         │
      Vertical                   Vertical
       Slice                      Slice
          │                         │
   ┌──────┼──────┐           ┌──────┼──────┐
   ▼      ▼      ▼           ▼      ▼      ▼
Domain Application Infra    Domain Application Infra
          │                         │
         DTO                       DTO
          │                         │
       Use Case                  Use Case
          │                         │
        Ports                    Ports
          │                         │
       Adapters                 Adapters
          │                         │
         ORM                       ORM
          │                         │
      Repository                Repository
          │                         │
          └──────────┬──────────────┘
                     ▼
                 PostgreSQL
                     ▲
                     │
                 Alembic
```

------------------------------------------------------------------------

# 49. Decisiones arquitectónicas adoptadas

  Decisión                 Estado
  ------------------------ -----------------------------------------------------
  Python                   Adoptado
  FastAPI                  Adoptado
  `backend/src`            Adoptado
  `src/app`                No utilizar
  Vertical Slicing         Adoptado
  Screaming Architecture   Adoptado
  Hexagonal Architecture   Adoptado
  Domain                   Adoptado
  Application              Adoptado
  Infrastructure           Adoptado
  DTO                      Adoptado
  Outgoing Ports           Adoptado cuando exista una dependencia que abstraer
  Incoming Ports           No obligatorios; evitar duplicación innecesaria
  ORM                      Adoptado
  Repository Pattern       Adoptado
  PostgreSQL               Base de persistencia prevista
  Alembic                  Migraciones
  JWT                      Autenticación
  Password hashing         Seguridad
  Redis                    Solo cuando exista una necesidad real
  Unit tests               Adoptado
  Integration tests        Adoptado
  E2E tests                Adoptado

------------------------------------------------------------------------

# 50. Regla más importante

> **La arquitectura está al servicio del sistema. No el sistema al
> servicio de la arquitectura.**

Si una decisión mejora separación, mantenibilidad, testabilidad o
independencia tecnológica, la utilizamos.

Si solamente agrega carpetas, interfaces o abstracciones sin resolver un
problema real, no la utilizamos.

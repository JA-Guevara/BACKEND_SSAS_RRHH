RESUMEN DE ADAPTACION ORM - SPRINT 0
SSAS RRHH

Objetivo
========
Se adapto el backend al diseno de base de datos del Sprint 0, usando empresa como tenant principal del sistema SaaS multiempresa.

Se valido la conexion real con PostgreSQL/Supabase.
Se ejecutaron y verificaron las migraciones Alembic.
La base quedo en la revision 20260824_0002.
No se borraron datos.

Cambios Principales
===================

1. Nuevo modulo empresas
------------------------
Se creo el modulo:

src/ssas/empresas/

Dentro se agregaron modelos ORM para:

- empresa
- plan_suscripcion
- suscripcion
- parametro_legal
- parametro_valor

Estos modelos representan la base multiempresa, la suscripcion SaaS y los parametros legales por empresa.

2. Empresa como tenant
----------------------
Se decidio usar empresa como entidad tenant principal, en vez de crear una tabla tenants.

Esto significa que el aislamiento multiempresa se maneja con:

empresa_id

Las tablas que ahora tienen empresa_id son:

- usuario
- rol
- refresh_token
- password_reset_token
- bitacora
- parametro_valor

3. Permisos globales
--------------------
Se dejo permiso como tabla global del sistema, sin empresa_id.

Razon:
Los permisos son capacidades tecnicas del sistema completo, por ejemplo:

- usuarios:crear
- usuarios:editar
- roles:gestionar
- bitacora:ver
- vacantes:gestionar
- candidatos:gestionar
- aprobaciones:gestionar

Luego cada empresa puede tener sus propios roles y asignarles esos permisos globales.

4. Roles por empresa
--------------------
La tabla rol ahora pertenece a empresa mediante empresa_id.

Esto permite que cada empresa tenga sus propios roles, por ejemplo:

Empresa A:
- Administrador de Empresa
- Reclutador
- Jefe de Area

Empresa B:
- Administrador de Empresa
- Analista RRHH

5. Renombrado de tablas al diseno del Sprint 0
----------------------------------------------
Los modelos ORM dejaron de apuntar a nombres en ingles y fueron alineados al diagrama/base en espanol.

Antes -> Ahora

users -> usuario
roles -> rol
permissions -> permiso
user_roles -> usuario_rol
role_permissions -> rol_permiso
audit_logs -> bitacora
refresh_tokens -> refresh_token
password_reset_tokens -> password_reset_token

6. Modelos existentes modificados
---------------------------------
Se actualizaron estos modelos ORM:

- src/ssas/auth/infrastructure/persistence/models/user.py
- src/ssas/auth/infrastructure/persistence/models/refresh_token.py
- src/ssas/auth/infrastructure/persistence/models/password_reset_token.py
- src/ssas/roles/infrastructure/persistence/models/role.py
- src/ssas/roles/infrastructure/persistence/models/permission.py
- src/ssas/roles/infrastructure/persistence/models/role_permission.py
- src/ssas/roles/infrastructure/persistence/models/user_role.py
- src/ssas/bitacora/infrastructure/persistence/models/audit_log.py

7. Modelos nuevos creados
-------------------------
Se agregaron estos modelos:

- src/ssas/empresas/infrastructure/persistence/models/empresa.py
- src/ssas/empresas/infrastructure/persistence/models/plan_suscripcion.py
- src/ssas/empresas/infrastructure/persistence/models/suscripcion.py
- src/ssas/empresas/infrastructure/persistence/models/parametro_legal.py
- src/ssas/empresas/infrastructure/persistence/models/parametro_valor.py

8. Base unica
-------------
Todos los modelos siguen heredando de la Base unica existente:

ssas.infrastructure.database.base.Base

Esto es importante para que Alembic pueda detectar todas las tablas desde un solo metadata.

9. Migraciones aplicadas
------------------------
Se aplico la migracion inicial:

migrations/versions/20260820_0001_initial_schema.py

Ahora la migracion prepara el esquema base con estas tablas:

- empresa
- plan_suscripcion
- suscripcion
- usuario
- rol
- permiso
- usuario_rol
- rol_permiso
- parametro_legal
- parametro_valor
- refresh_token
- password_reset_token
- bitacora

Esta migracion tambien prepara:

- extension pgcrypto
- funcion set_updated_at
- triggers updated_at
- indices principales
- constraints de unicidad
- constraints de fechas
- datos base del sistema

Luego se aplico:

migrations/versions/20260824_0002_auditoria_y_unicidad_multitenant.py

La segunda migracion agrega:

- modulo, descripcion, nivel y actor_etiqueta en bitacora
- indices para consultar la bitacora por modulo
- unicidad sin distinguir mayusculas/minusculas para slug de empresa
- unicidad por empresa para email y username de usuario
- unicidad por empresa para codigo y nombre de rol
- carga idempotente de permisos y parametros legales base

Revision actual de la base:

20260824_0002 (head)

10. Datos base incluidos en la migracion
----------------------------------------
La migracion incluye datos base para:

- Plan Inicial
- permisos globales
- parametros legales base de Bolivia

Permisos globales incluidos:

- usuarios:crear
- usuarios:editar
- roles:gestionar
- bitacora:ver
- vacantes:gestionar
- candidatos:gestionar
- aprobaciones:gestionar

Parametros legales base incluidos:

- AFP_APORTE_LABORAL
- APORTE_SOLIDARIO
- RC_IVA

11. Datos de demo no incluidos
------------------------------
No se agregaron Empresa A ni Empresa B dentro de la migracion.

Razon:
Empresa A y Empresa B son datos de prueba/demo. Es mejor crearlas despues mediante:

- endpoint de aprovisionamiento de empresa
- seed especifico de desarrollo
- script aparte de datos demo

No conviene meter clientes ficticios en una migracion estructural.

12. Alembic actualizado
-----------------------
Se actualizo:

migrations/env.py

Ahora Alembic importa los nuevos modelos para que la metadata conozca:

- empresa
- plan_suscripcion
- suscripcion
- parametro_legal
- parametro_valor
- usuario
- rol
- permiso
- usuario_rol
- rol_permiso
- refresh_token
- password_reset_token
- bitacora

13. Verificacion realizada
--------------------------
Se verifico el estado real del backend y de PostgreSQL/Supabase:

- conexion real a la base: OK
- alembic upgrade head: OK
- revision remota: 20260824_0002
- alembic check: no detecta operaciones pendientes
- modelos ORM: alineados con el esquema migrado
- 10 pruebas unitarias: OK
- 1 prueba de integracion de conexion real: OK
- GET /health mediante FastAPI TestClient: OK
- OpenAPI: 20 rutas registradas
- Ruff: sin errores

Estado Actual
=============

Quedo implementado y verificado:

- Modelo multiempresa con empresa como tenant
- Modelos ORM alineados al diagrama Sprint 0
- Permisos globales
- Roles por empresa
- Bitacora por empresa
- Parametros legales por empresa y vigencia
- Conexion asincrona a PostgreSQL/Supabase
- Login y repositorios principales delimitados por empresa
- Migraciones Alembic 0001 y 0002 aplicadas
- Registro persistente de eventos de Auth y Roles en bitacora
- Esquema ORM sincronizado con Alembic

Queda pendiente:

1. Crear el endpoint de aprovisionamiento de empresa.
2. Crear el usuario administrador inicial por empresa.
3. Crear roles base por empresa durante el aprovisionamiento.
4. Integrar un proveedor real para correos de restablecimiento.
5. Definir el alcance y los permisos del superadministrador de plataforma.
6. Agregar pruebas E2E con dos empresas para demostrar el aislamiento.
7. Agregar rate limiting y bloqueo progresivo de intentos de acceso.
8. Rotar la contrasena de Supabase expuesta durante las pruebas.

Comandos de mantenimiento
=========================

Para consultar la revision actual:

alembic current

Para consultar el historial:

alembic history

Para comprobar que modelos y migraciones coinciden:

alembic check

Para ver el SQL que Alembic generaria sin aplicarlo:

alembic upgrade head --sql

Para aplicar futuras migraciones:

alembic upgrade head

Nota para futuras migraciones
============================
La migracion actual ya fue aplicada. Antes de aplicar una migracion nueva se debe revisar el SQL,
confirmar DATABASE_URL, disponer de respaldo y validar primero en un ambiente no productivo.

# Administración global de SSAS

## Separación de alcances

La revisión `20260825_0004` separa dos contextos de seguridad:

- `scope=platform`: superadministradores globales, sin `empresa_id`.
- `scope=tenant`: usuarios empresariales con `tid=empresa_id`.

Un token empresarial nunca es aceptado por `/api/v1/platform/*`; un token de plataforma tampoco
sirve para las rutas internas de una empresa.

En Railway, permitir el frontend mediante:

```env
APP_CORS_ORIGINS=https://frontendssasrrhh-production.up.railway.app
```

En producción, `APP_SECRET_KEY` debe tener al menos 32 caracteres y ser igual para tokens de
plataforma y tenant.

## Creación inicial del superadministrador

No existe registro público. Después de configurar `DATABASE_URL`, ejecutar:

```powershell
.\.venv\Scripts\python.exe -m ssas.platform.infrastructure.cli.create_admin `
  --nombre "Jose Armando" `
  --apellido "Guevara Caballero" `
  --email "jose.guevara1caballero@gmail.com" `
  --username "ja.guevara"
```

La contraseña y su confirmación se solicitan de forma oculta. Debe cumplir la política segura del
módulo Auth. El comando rechaza emails o usernames duplicados y registra el bootstrap en la
bitácora global.

## Autenticación global

| Método | Ruta | Función |
|---|---|---|
| POST | `/api/v1/platform/auth/login` | Iniciar sesión global |
| POST | `/api/v1/platform/auth/refresh` | Rotar refresh token |
| POST | `/api/v1/platform/auth/logout` | Revocar sesión |
| GET | `/api/v1/platform/auth/me` | Perfil del superadministrador |
| POST | `/api/v1/platform/auth/password/change` | Cambiar contraseña global |

La cuenta se bloquea temporalmente bajo la misma política de intentos fallidos configurada para
Auth. Los refresh tokens son independientes de los tokens empresariales.

## Empresas y aprovisionamiento

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/v1/platform/empresas` | Listar y buscar empresas |
| POST | `/api/v1/platform/empresas` | Aprovisionar empresa completa |
| GET | `/api/v1/platform/empresas/{id}` | Consultar empresa |
| PATCH | `/api/v1/platform/empresas/{id}` | Actualizar empresa |
| PATCH | `/api/v1/platform/empresas/{id}/activar` | Activar empresa |
| PATCH | `/api/v1/platform/empresas/{id}/suspender` | Suspender empresa |

El aprovisionamiento se ejecuta en una sola transacción y crea:

1. Empresa.
2. Suscripción inicial.
3. Roles `ADMIN_EMPRESA`, `RRHH`, `RECLUTADOR` y `EMPLEADO`.
4. Asignaciones de permisos.
5. Primer administrador empresarial.
6. Token y correo de verificación.
7. Evento de bitácora global.

Si falla una operación de base de datos, toda la transacción se revierte.

## Planes y suscripciones

| Método | Ruta | Función |
|---|---|---|
| GET/POST | `/api/v1/platform/planes` | Listar o crear planes |
| GET/PATCH | `/api/v1/platform/planes/{id}` | Consultar o actualizar plan |
| GET | `/api/v1/platform/suscripciones` | Listar suscripciones |
| GET | `/api/v1/platform/empresas/{id}/suscripcion` | Suscripción activa |
| PUT | `/api/v1/platform/empresas/{id}/suscripcion` | Reemplazar plan/vigencia |

Reemplazar una suscripción desactiva la anterior y crea una nueva, conservando el historial.

## Bitácora global

```text
GET /api/v1/platform/bitacora
GET /api/v1/platform/bitacora/{id}
```

La tabla `bitacora_plataforma` está separada de la bitácora empresarial. Registra accesos globales,
aprovisionamientos, cambios de empresa, planes y suscripciones.

## Gestión de la propia empresa

Los usuarios empresariales utilizan:

```text
GET   /api/v1/mi-empresa
PATCH /api/v1/mi-empresa
GET   /api/v1/mi-empresa/suscripcion
GET   /api/v1/mi-empresa/parametros
PUT   /api/v1/mi-empresa/parametros/{codigo}
```

Las rutas antiguas `/api/v1/empresa/parametros` se conservan temporalmente por compatibilidad. El
administrador empresarial no puede cambiar su plan, suspender su empresa ni consultar otros tenants.

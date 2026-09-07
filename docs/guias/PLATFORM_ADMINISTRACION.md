# Superadministración y empresas

## Modelo único de identidad

SSAS utiliza una sola tabla `usuario`, un solo Auth y un solo formato JWT:

- `usuario.empresa_id IS NULL`: administrador global.
- `usuario.empresa_id = UUID`: usuario de una empresa.
- `rol.empresa_id IS NULL`: rol global, como `SUPER_ADMIN`.
- `rol.empresa_id = UUID`: rol perteneciente a esa empresa.

No existen tablas ni endpoints paralelos de autenticación para plataforma. Tampoco forman parte del
alcance actual los planes, suscripciones o parámetros legales.

## Autenticación

Todos utilizan `/api/v1/auth/*`. En login, `empresa_slug` decide el ámbito:

- Sin `empresa_slug`: busca una cuenta global.
- Con `empresa_slug`: busca una cuenta dentro de esa empresa.

El primer superadministrador se crea por consola después de aplicar la migración:

```powershell
.\.venv\Scripts\python.exe -m ssas.platform.infrastructure.cli.create_admin `
  --nombre "Nombre" --apellido "Apellido" `
  --email "admin@example.com" --username "admin"
```

## Empresas

| Método | Ruta | Alcance |
|---|---|---|
| GET/POST | `/api/v1/empresas` | Solo superadministrador |
| GET/PATCH | `/api/v1/empresas/{id}` | Superadmin: cualquiera; admin empresa: la propia |
| PATCH | `/api/v1/empresas/{id}/activar` | Solo superadministrador |
| PATCH | `/api/v1/empresas/{id}/suspender` | Solo superadministrador |
| DELETE | `/api/v1/empresas/{id}` | Solo superadministrador |
| PATCH | `/api/v1/empresas/{id}/restaurar` | Solo superadministrador |

Crear una empresa genera sus roles base, el primer `ADMIN_EMPRESA`, su verificación de correo y el
evento correspondiente de bitácora, todo dentro de la misma transacción.

Eliminar una empresa es una operación lógica: suspende la empresa, desactiva sus usuarios, revoca
sus sesiones y conserva todos los datos y la bitácora. Restaurarla no reactiva automáticamente ni la
empresa ni sus usuarios; primero se activa la empresa y después se decide qué cuentas reactivar.
El listado excluye eliminadas por defecto y admite `incluir_eliminadas=true` para su administración.

## Usuarios y roles

Los endpoints son compartidos. Para un superadministrador, `empresa_id` selecciona el ámbito:

- `empresa_id` omitido: usuarios o roles globales.
- `empresa_id=<uuid>`: usuarios o roles de esa empresa.

Para un administrador empresarial, el backend fuerza el `empresa_id` del token. Enviar el de otra
empresa responde `403`. Un superadministrador puede crear otro superadministrador usando
`POST /api/v1/usuarios`, sin `empresa_id`, y asignando el rol global `SUPER_ADMIN`.

## Bitácora

Existe una sola tabla y una sola ruta `/api/v1/bitacora`:

- Evento global: `empresa_id IS NULL`.
- Evento empresarial: contiene el `empresa_id` correspondiente.
- Superadministrador: consulta global o selecciona una empresa.
- Administrador empresarial: únicamente consulta su empresa.

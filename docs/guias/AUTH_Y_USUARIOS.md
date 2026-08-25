# Autenticación y gestión de usuarios

## Estado

La migración inicial limpia `20260825_0001` está preparada para una base vacía. Una sola identidad
atiende cuentas globales y empresariales; toda cuenta nueva debe verificar su correo.

## Política de contraseña

Toda contraseña nueva o restablecida debe tener entre 12 y 72 caracteres e incluir una mayúscula,
una minúscula, un número y un símbolo. No puede contener espacios, ser una contraseña común ni
incluir el username o la parte local del correo.

## Protección del acceso

- El quinto intento fallido activa un bloqueo temporal de 15 minutos.
- Un administrador puede desbloquear la cuenta antes del vencimiento.
- El inicio correcto reinicia el contador y actualiza el último acceso.
- Usuarios, empresas, correos y roles inactivos impiden el acceso.
- Los endpoints protegidos rechazan cuentas bloqueadas o sin correo verificado.
- El cambio o restablecimiento de contraseña revoca todos los refresh tokens.
- Una contraseña temporal obliga al usuario a cambiarla antes de utilizar módulos protegidos.

Los límites se configuran con `APP_MAX_LOGIN_ATTEMPTS` y `APP_LOGIN_LOCK_MINUTES`.

## Endpoints de autenticación

| Método | Ruta | Acceso | Función |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Público | Inicia sesión global o por empresa |
| POST | `/api/v1/auth/refresh` | Público | Rota el refresh token |
| POST | `/api/v1/auth/logout` | Bearer | Revoca la sesión |
| GET | `/api/v1/auth/me` | Bearer | Devuelve el usuario actual |
| POST | `/api/v1/auth/password/forgot` | Público | Envía recuperación por correo |
| POST | `/api/v1/auth/password/reset` | Público | Restablece usando token de un solo uso |
| POST | `/api/v1/auth/password/change` | Bearer | Cambia la contraseña propia |
| POST | `/api/v1/auth/email/verification/resend` | Público | Reenvía la verificación |
| POST | `/api/v1/auth/email/verify` | Público | Confirma el correo con un token |

Las respuestas de recuperación y reenvío no revelan si una cuenta existe. Los tokens se guardan
como huellas criptográficas, tienen vencimiento y solo pueden utilizarse una vez.

## Endpoints administrativos de usuarios

| Método | Ruta | Permiso |
|---|---|---|
| GET | `/api/v1/usuarios` | `usuarios:ver` |
| GET | `/api/v1/usuarios/{id}` | `usuarios:ver` |
| POST | `/api/v1/usuarios` | `usuarios:crear` |
| PATCH | `/api/v1/usuarios/{id}` | `usuarios:editar` |
| PATCH | `/api/v1/usuarios/{id}/activar` | `usuarios:editar` |
| PATCH | `/api/v1/usuarios/{id}/desactivar` | `usuarios:editar` |
| PUT | `/api/v1/usuarios/{id}/password` | `usuarios:cambiar_password` |
| PATCH | `/api/v1/usuarios/{id}/desbloquear` | `usuarios:desbloquear` |

El listado acepta `empresa_id`, `search`, `is_active`, `page` y `per_page`. Para cuentas globales,
`empresa_id` selecciona una empresa o, si se omite, el ámbito global. Para cuentas empresariales el
backend fuerza el `empresa_id` del token. No se permite desactivar al último administrador activo.

## Configuración SMTP

La recuperación y verificación requieren estas variables en local y Railway:

```env
APP_FRONTEND_URL=https://frontend.example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=usuario-smtp
SMTP_PASSWORD=secreto-smtp
SMTP_FROM_EMAIL=no-reply@example.com
SMTP_FROM_NAME=SSAS RRHH
SMTP_USE_TLS=true
```

`APP_FRONTEND_URL` debe apuntar al frontend que recibirá las rutas
`/restablecer-contrasena?token=...` y `/verificar-correo?token=...`.

## Auditoría

Se registran inicios correctos y fallidos, logout, solicitudes y finalizaciones de recuperación,
cambio de contraseña, verificación de correo, creación y modificación de usuarios, activación,
desactivación, desbloqueo y asignación administrativa de contraseña.

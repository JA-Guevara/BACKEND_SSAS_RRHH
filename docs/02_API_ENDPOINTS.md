# 02 — CONTRATO DE ENDPOINTS

> **Generado desde el código**, no escrito a mano: los contratos salen del OpenAPI que
> produce la propia aplicación y los permisos del AST de los routers.
> Última sincronización: **2026-09-07** · commit `782ac60`

> Regenerar y verificar con: `python scripts/verificar_documentacion.py`

Estados: `IMPLEMENTADO` · `PARCIAL` · `PENDIENTE` · `BLOQUEADO` · `DEPRECADO`

---



## Matriz general

| ID | Método | Endpoint | Módulo | PA / CU | Estado | Alcance | Permiso | Task |
|---|---|---|---|---|---|---|---|---|
| API-001 | POST | `/api/v1/auth/email/verification/resend` | Auth | PA-01 / CU-03 | IMPLEMENTADO | público | — | AUTH-001 |
| API-002 | POST | `/api/v1/auth/email/verify` | Auth | PA-01 / CU-03 | IMPLEMENTADO | público | — | AUTH-001 |
| API-003 | POST | `/api/v1/auth/login` | Auth | PA-01 / CU-03 | IMPLEMENTADO | público | — | AUTH-001 |
| API-004 | POST | `/api/v1/auth/logout` | Auth | PA-01 / CU-03 | IMPLEMENTADO | autenticado | solo autenticación | AUTH-001 |
| API-005 | GET | `/api/v1/auth/me` | Auth | PA-01 / CU-03 | IMPLEMENTADO | autenticado | solo autenticación | AUTH-001 |
| API-006 | POST | `/api/v1/auth/password/change` | Auth | PA-01 / CU-03 | IMPLEMENTADO | autenticado | solo autenticación | AUTH-001 |
| API-007 | POST | `/api/v1/auth/password/forgot` | Auth | PA-01 / CU-03 | IMPLEMENTADO | público | — | AUTH-001 |
| API-008 | POST | `/api/v1/auth/password/reset` | Auth | PA-01 / CU-03 | IMPLEMENTADO | público | — | AUTH-001 |
| API-009 | POST | `/api/v1/auth/refresh` | Auth | PA-01 / CU-03 | IMPLEMENTADO | público | — | AUTH-001 |
| API-034 | GET | `/api/v1/bitacora` | Bitácora | PA-01 / CU-06 | IMPLEMENTADO | empresa + plataforma | `bitacora:ver` (empresa) o `platform:bitacora:ver` (plataforma) | BIT-001 |
| API-035 | GET | `/api/v1/bitacora/{audit_log_id}` | Bitácora | PA-01 / CU-06 | IMPLEMENTADO | empresa + plataforma | `bitacora:ver` (empresa) o `platform:bitacora:ver` (plataforma) | BIT-001 |
| API-040 | GET | `/api/v1/cargos` | Cargos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `cargos:ver` (empresa) o `platform:organizacion:gestionar` (plataforma) | CAR-001 |
| API-041 | POST | `/api/v1/cargos` | Cargos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `cargos:crear` (empresa) o `platform:organizacion:gestionar` (plataforma) | CAR-001 |
| API-042 | DELETE | `/api/v1/cargos/{cargo_id}` | Cargos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `cargos:eliminar` (empresa) o `platform:organizacion:gestionar` (plataforma) | CAR-001 |
| API-043 | PUT | `/api/v1/cargos/{cargo_id}` | Cargos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `cargos:editar` (empresa) o `platform:organizacion:gestionar` (plataforma) | CAR-001 |
| API-036 | GET | `/api/v1/departamentos` | Departamentos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `departamentos:ver` (empresa) o `platform:organizacion:gestionar` (plataforma) | DEP-001 |
| API-037 | POST | `/api/v1/departamentos` | Departamentos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `departamentos:crear` (empresa) o `platform:organizacion:gestionar` (plataforma) | DEP-001 |
| API-038 | DELETE | `/api/v1/departamentos/{departamento_id}` | Departamentos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `departamentos:eliminar` (empresa) o `platform:organizacion:gestionar` (plataforma) | DEP-001 |
| API-039 | PUT | `/api/v1/departamentos/{departamento_id}` | Departamentos | PA-04 / CU-19 | IMPLEMENTADO | empresa + plataforma | `departamentos:editar` (empresa) o `platform:organizacion:gestionar` (plataforma) | DEP-001 |
| API-026 | GET | `/api/v1/empresas` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | plataforma | `platform:empresas:ver` | EMP-001 |
| API-027 | POST | `/api/v1/empresas` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | plataforma | `platform:empresas:crear` | EMP-001 |
| API-028 | DELETE | `/api/v1/empresas/{empresa_id}` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | plataforma | `platform:empresas:eliminar` | EMP-001 |
| API-029 | GET | `/api/v1/empresas/{empresa_id}` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | empresa + plataforma | `empresa:ver` (empresa) o `platform:empresas:ver` (plataforma) | EMP-001 |
| API-030 | PATCH | `/api/v1/empresas/{empresa_id}` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | empresa + plataforma | `empresa:editar` (empresa) o `platform:empresas:editar` (plataforma) | EMP-001 |
| API-031 | PATCH | `/api/v1/empresas/{empresa_id}/activar` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | plataforma | `platform:empresas:suspender` | EMP-001 |
| API-032 | PATCH | `/api/v1/empresas/{empresa_id}/restaurar` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | plataforma | `platform:empresas:restaurar` | EMP-001 |
| API-033 | PATCH | `/api/v1/empresas/{empresa_id}/suspender` | Empresas | PA-01 / CU-01, CU-02 | IMPLEMENTADO | plataforma | `platform:empresas:suspender` | EMP-001 |
| API-046 | GET | `/health` | Sistema | — / — | IMPLEMENTADO | público | — | SYS-001 |
| API-044 | POST | `/api/v1/publico/postulaciones` | Postulaciones | PA-02 / CU-09, CU-12 | IMPLEMENTADO | público | — | POS-001 |
| API-045 | GET | `/api/v1/publico/postulaciones/{codigo}` | Postulaciones | PA-02 / CU-09, CU-12 | IMPLEMENTADO | autenticado | solo autenticación | POS-001 |
| API-020 | GET | `/api/v1/roles` | Roles | PA-01 / CU-05 | IMPLEMENTADO | empresa + plataforma | `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma) | ROL-001 |
| API-021 | POST | `/api/v1/roles` | Roles | PA-01 / CU-05 | IMPLEMENTADO | empresa + plataforma | `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma) | ROL-001 |
| API-022 | DELETE | `/api/v1/roles/{role_id}` | Roles | PA-01 / CU-05 | IMPLEMENTADO | empresa + plataforma | `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma) | ROL-001 |
| API-023 | GET | `/api/v1/roles/{role_id}` | Roles | PA-01 / CU-05 | IMPLEMENTADO | empresa + plataforma | `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma) | ROL-001 |
| API-024 | PATCH | `/api/v1/roles/{role_id}` | Roles | PA-01 / CU-05 | IMPLEMENTADO | empresa + plataforma | `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma) | ROL-001 |
| API-025 | PUT | `/api/v1/roles/{role_id}/permissions` | Roles | PA-01 / CU-05 | IMPLEMENTADO | empresa + plataforma | `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma) | ROL-001 |
| API-010 | GET | `/api/v1/usuarios` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:ver` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-011 | POST | `/api/v1/usuarios` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:crear` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-012 | DELETE | `/api/v1/usuarios/{usuario_id}` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:eliminar` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-013 | GET | `/api/v1/usuarios/{usuario_id}` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:ver` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-014 | PATCH | `/api/v1/usuarios/{usuario_id}` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:editar` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-015 | PATCH | `/api/v1/usuarios/{usuario_id}/activar` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:editar` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-016 | PATCH | `/api/v1/usuarios/{usuario_id}/desactivar` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:editar` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-017 | PATCH | `/api/v1/usuarios/{usuario_id}/desbloquear` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:desbloquear` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-018 | PUT | `/api/v1/usuarios/{usuario_id}/password` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:cambiar_password` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |
| API-019 | PATCH | `/api/v1/usuarios/{usuario_id}/restaurar` | Usuarios | PA-01 / CU-04 | IMPLEMENTADO | empresa + plataforma | `usuarios:restaurar` (empresa) o `platform:usuarios:gestionar` (plataforma) | USR-001 |

### Endpoints PENDIENTES — alcance del Sprint 1 aún sin implementar

Derivados del **Capítulo 4 · Sprint 1** del perfil del proyecto y de los modelos ya
migrados. Ninguno existe todavía en el código: el contrato es `DECISIÓN PENDIENTE`
hasta que se implemente.

| ID | Método | Endpoint | Módulo | PA / CU | Estado | Alcance | Permiso previsto | Task |
|---|---|---|---|---|---|---|---|---|
| API-P01 | GET | `/api/v1/vacantes` | Vacantes | PA-02 / CU-08 | IMPLEMENTADO | empresa | `vacantes:ver` | VAC-003 |
| API-P02 | POST | `/api/v1/vacantes` | Vacantes | PA-02 / CU-08 | IMPLEMENTADO | empresa | `vacantes:crear` | VAC-003 |
| API-P03 | GET | `/api/v1/vacantes/{vacante_id}` | Vacantes | PA-02 / CU-08 | IMPLEMENTADO | empresa | `vacantes:ver` | VAC-003 |
| API-P04 | PUT | `/api/v1/vacantes/{vacante_id}` | Vacantes | PA-02 / CU-08 | IMPLEMENTADO | empresa | `vacantes:editar` | VAC-003 |
| API-P05 | PATCH | `/api/v1/vacantes/{vacante_id}/publicar` | Vacantes | PA-02 / CU-08 | IMPLEMENTADO | empresa | `vacantes:publicar` | VAC-003 |
| API-P06 | DELETE | `/api/v1/vacantes/{vacante_id}` | Vacantes | PA-02 / CU-08 | IMPLEMENTADO | empresa | `vacantes:eliminar` | VAC-003 |
| API-P07 | GET | `/api/v1/publico/{empresa_slug}/vacantes` | Portal | PA-02 / CU-09 | IMPLEMENTADO | público | `— (público)` | POR-001 |
| API-P08 | GET | `/api/v1/publico/{empresa_slug}/vacantes/{vacante_id}` | Portal | PA-02 / CU-09 | IMPLEMENTADO | público | `— (público)` | POR-001 |
| API-P09 | GET | `/api/v1/postulantes` | Postulantes | PA-02 / CU-11 | IMPLEMENTADO | empresa | `postulantes:ver` | PTE-003 |
| API-P10 | GET | `/api/v1/postulantes/{postulante_id}` | Postulantes | PA-02 / CU-11 | IMPLEMENTADO | empresa | `postulantes:ver` | PTE-003 |
| API-P11 | GET | `/api/v1/vacantes/{vacante_id}/tablero` | Tablero | PA-03 / CU-12 | IMPLEMENTADO | empresa | `postulaciones:ver` | TAB-002 |
| API-P12 | GET | `/api/v1/postulaciones` | Postulaciones | PA-02 / CU-12 | IMPLEMENTADO | empresa | `postulaciones:ver` | TAB-002 |
| API-P13 | PATCH | `/api/v1/postulaciones/{postulacion_id}/etapa` | Tablero | PA-03 / CU-12 | IMPLEMENTADO | empresa | `postulaciones:gestionar` | TAB-003 |
| API-P14 | PATCH | `/api/v1/postulaciones/{postulacion_id}/rechazar` | Tablero | PA-03 / CU-12 | IMPLEMENTADO | empresa | `postulaciones:gestionar` | TAB-003 |
| API-P15 | GET | `/api/v1/etapas-reclutamiento` | Tablero | PA-03 / CU-12 | IMPLEMENTADO | empresa | `postulaciones:ver` | TAB-001 |
| API-P16 | GET | `/api/v1/motivos-rechazo` | Tablero | PA-03 / CU-12 | IMPLEMENTADO | empresa | `postulaciones:ver` | TAB-001 |
| API-P17 | GET | `/api/v1/habilidades` | Habilidades | PA-02 / apoyo CU-08 | IMPLEMENTADO | empresa | `habilidades:ver` | HAB-003 |
| API-P18 | POST | `/api/v1/habilidades` | Habilidades | PA-02 / apoyo CU-08 | IMPLEMENTADO | empresa | `habilidades:gestionar` | HAB-003 |
| API-P19 | DELETE | `/api/v1/habilidades/{habilidad_id}` | Habilidades | PA-02 / apoyo CU-08 | IMPLEMENTADO | empresa | `habilidades:gestionar` | HAB-003 |

> Los permisos de la columna anterior **no existen todavía** en el catálogo de la base
> (28 permisos actuales). Crearlos es parte de las tareas `*-004` del backlog.

---

## Fichas de endpoints implementados


---

# AUTH  ·  PA-01

## [API-001] POST `/api/v1/auth/email/verification/resend`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Genera un nuevo enlace cuando la cuenta existe y su correo continúa pendiente de verificación.

**Request** · `application/json` · schema `ResendVerificationSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `email` | string | sí | Email |
| `empresa_slug` | string | sí | Empresa Slug |

**Response 200** · schema `MessageSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Message |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 422 | Validation Error |
| 503 | El servicio de correo no está disponible. |

**Implementación**

- Handler: `resend_email_verification()` — `src/ssas/auth/infrastructure/http/router.py:350`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-002] POST `/api/v1/auth/email/verify`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Confirma el correo mediante un token de verificación vigente y de un solo uso.

**Request** · `application/json` · schema `VerifyEmailSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `token` | string | sí | Token |

**Response 200** · schema `MessageSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Message |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token inválido, vencido o utilizado previamente. |
| 422 | Validation Error |

**Implementación**

- Handler: `verify_email()` — `src/ssas/auth/infrastructure/http/router.py:376`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-003] POST `/api/v1/auth/login`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Autentica mediante correo o nombre de usuario. Omite `empresa_slug` para una cuenta de plataforma; envíalo para buscar la cuenta dentro de una empresa. Los intentos fallidos se registran y pueden bloquear temporalmente la cuenta.

**Request** · `application/json` · schema `LoginSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `empresa_slug` | string | no | Slug de la empresa. Omitir para administradores de plataforma. |
| `email` | string | no | Correo. Alternativa: username. |
| `username` | string | no | Username |
| `password` | string | sí | Password |

**Response 200** · schema `TokenPairSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `access_token` | string | Access Token |
| `refresh_token` | string | Refresh Token |
| `token_type` | string | Token Type |
| `expires_in` | integer | Expires In |
| `must_change_password` | boolean | Must Change Password |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Credenciales inválidas o cuenta inactiva. |
| 403 | El correo aún no fue verificado. |
| 422 | Validation Error |
| 423 | Cuenta bloqueada temporalmente por intentos fallidos. |
| 503 | No se pudo acceder a una dependencia del servicio. |

**Implementación**

- Handler: `login_user()` — `src/ssas/auth/infrastructure/http/router.py:153`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-004] POST `/api/v1/auth/logout`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** autenticado  
**Autenticación:** Sí (Bearer)  
**Permiso:** solo autenticación

Revoca el refresh token enviado. Requiere un access token válido.

**Request** · `application/json` · schema `RefreshTokenSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `refresh_token` | string | sí | Refresh Token |

**Response 200** · schema `MessageSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Message |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `logout_user()` — `src/ssas/auth/infrastructure/http/router.py:214`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-005] GET `/api/v1/auth/me`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** autenticado  
**Autenticación:** Sí (Bearer)  
**Permiso:** solo autenticación

Devuelve la identidad autenticada, su empresa cuando corresponda, roles y estado de seguridad.

**Response 200** · schema `UserSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `name` | string | Name |
| `email` | string | Email |
| `empresa_id` | string | Empresa Id |
| `username` | string | Username |
| `roles` | array[string] | Roles |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `current_user()` — `src/ssas/auth/infrastructure/http/router.py:246`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-006] POST `/api/v1/auth/password/change`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** autenticado  
**Autenticación:** Sí (Bearer)  
**Permiso:** solo autenticación

Valida la contraseña actual, aplica la política de seguridad, actualiza la clave y revoca las sesiones existentes.

**Request** · `application/json` · schema `ChangePasswordSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `current_password` | string | sí | Current Password |
| `new_password` | string | sí | New Password |

**Response 200** · schema `MessageSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Message |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | La contraseña actual o la nueva contraseña no son válidas. |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `change_password()` — `src/ssas/auth/infrastructure/http/router.py:315`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-007] POST `/api/v1/auth/password/forgot`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Solicita un enlace de recuperación sin revelar si la cuenta existe. Omite `empresa_slug` para cuentas de plataforma.

**Request** · `application/json` · schema `ForgotPasswordSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `email` | string | sí | Email |
| `empresa_slug` | string | sí | Empresa Slug |

**Response 200** · schema `ForgotPasswordResponseSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Message |
| `reset_token` | string | Reset Token |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 422 | Validation Error |
| 503 | El servicio de correo no está disponible. |

**Implementación**

- Handler: `forgot_password()` — `src/ssas/auth/infrastructure/http/router.py:269`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-008] POST `/api/v1/auth/password/reset`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Establece una contraseña nueva mediante el token de recuperación y revoca las sesiones anteriores.

**Request** · `application/json` · schema `ResetPasswordSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `token` | string | sí | Token |
| `new_password` | string | sí | New Password |

**Response 200** · schema `MessageSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `message` | string | Message |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token inválido, vencido o utilizado previamente. |
| 422 | La contraseña nueva no cumple la política de seguridad. |

**Implementación**

- Handler: `reset_password()` — `src/ssas/auth/infrastructure/http/router.py:412`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-009] POST `/api/v1/auth/refresh`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-03  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Intercambia un refresh token activo por un nuevo par de tokens y revoca el refresh token anterior.

**Request** · `application/json` · schema `RefreshTokenSchema`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `refresh_token` | string | sí | Refresh Token |

**Response 200** · schema `TokenPairSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `access_token` | string | Access Token |
| `refresh_token` | string | Refresh Token |
| `token_type` | string | Token Type |
| `expires_in` | integer | Expires In |
| `must_change_password` | boolean | Must Change Password |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Refresh token inválido, vencido o revocado. |
| 422 | Validation Error |

**Implementación**

- Handler: `refresh_token()` — `src/ssas/auth/infrastructure/http/router.py:193`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso


---

# BITÁCORA  ·  PA-01

## [API-034] GET `/api/v1/bitacora`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-06  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `bitacora:ver` (empresa) o `platform:bitacora:ver` (plataforma)

Lista eventos inmutables con filtros por actor, módulo, acción y fechas. Un usuario empresarial solo consulta su empresa; plataforma puede seleccionar una empresa. Permisos: `bitacora:ver` o `platform:bitacora:ver`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |
| `user_id` | query | ? | no | Filtra por usuario que originó el evento. |
| `module` | query | ? | no | Filtra por módulo funcional. |
| `action` | query | ? | no | Filtra por código de acción. |
| `start_date` | query | ? | no | Fecha y hora inicial, inclusiva. |
| `end_date` | query | ? | no | Fecha y hora final, inclusiva. |
| `page` | query | integer | no |  |
| `per_page` | query | integer | no |  |

**Response 200** · schema `AuditLogPageSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `items` | array[AuditLogSchema] | Items |
| `total` | integer | Total |
| `page` | integer | Page |
| `per_page` | integer | Per Page |
| `total_pages` | integer | Total Pages |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Evento no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `list_audit_logs()` — `src/ssas/bitacora/infrastructure/http/router.py:44`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-035] GET `/api/v1/bitacora/{audit_log_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-06  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `bitacora:ver` (empresa) o `platform:bitacora:ver` (plataforma)

Obtiene un evento específico con su contexto, datos anteriores y datos nuevos, respetando el alcance de empresa.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `audit_log_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `AuditLogSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `module` | string | Module |
| `action` | string | Action |
| `description` | string | Description |
| `level` | string | Level |
| `user_id` | string | User Id |
| `actor_label` | string | Actor Label |
| `affected_table` | string | Affected Table |
| `record_id` | string | Record Id |
| `previous_data` | object | Previous Data |
| `new_data` | object | New Data |
| `source_ip` | string | Source Ip |
| `user_agent` | string | User Agent |
| `created_at` | string | Created At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `get_audit_log()` — `src/ssas/bitacora/infrastructure/http/router.py:84`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas


---

# CARGOS  ·  PA-04

## [API-040] GET `/api/v1/cargos`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `cargos:ver` (empresa) o `platform:organizacion:gestionar` (plataforma)

Lista cargos del alcance autorizado. Permisos: `cargos:ver` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |
| `activo` | query | ? | no | Filtra por estado activo. |
| `departamento_id` | query | ? | no | Filtra por departamento. |

**Response 200** · schema `list[CargoResponse]`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `departamento_id` | string | Departamento Id |
| `nombre` | string | Nombre |
| `descripcion` | string | Descripcion |
| `activo` | boolean | Activo |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `listar_cargos()` — `src/ssas/cargos/infrastructure/http/router.py:72`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-041] POST `/api/v1/cargos`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `cargos:crear` (empresa) o `platform:organizacion:gestionar` (plataforma)

Crea un cargo dentro de la empresa autorizada y valida que su departamento pertenezca al mismo alcance. Requiere `cargos:crear` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `CrearCargoRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `nombre` | string | sí | Nombre |
| `departamento_id` | string | no | Departamento Id |
| `descripcion` | string | no | Descripcion |
| `activo` | boolean | no | Activo |

**Response 201** · schema `CargoResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `departamento_id` | string | Departamento Id |
| `nombre` | string | Nombre |
| `descripcion` | string | Descripcion |
| `activo` | boolean | Activo |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | Ya existe un cargo con ese nombre. |
| 422 | El departamento no pertenece a la empresa. |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `crear_cargo()` — `src/ssas/cargos/infrastructure/http/router.py:103`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-042] DELETE `/api/v1/cargos/{cargo_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `cargos:eliminar` (empresa) o `platform:organizacion:gestionar` (plataforma)

Elimina un cargo sin dependencias dentro de la empresa autorizada. Requiere `cargos:eliminar` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `cargo_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 204** · schema `sin cuerpo`

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Cargo no encontrado. |
| 409 | El cargo tiene dependencias. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `eliminar_cargo()` — `src/ssas/cargos/infrastructure/http/router.py:170`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-043] PUT `/api/v1/cargos/{cargo_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `cargos:editar` (empresa) o `platform:organizacion:gestionar` (plataforma)

Actualiza un cargo de la empresa autorizada y valida el departamento indicado. Requiere `cargos:editar` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `cargo_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `ActualizarCargoRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `nombre` | string | no | Nombre |
| `departamento_id` | string | no | Departamento Id |
| `descripcion` | string | no | Descripcion |
| `activo` | boolean | no | Activo |

**Response 200** · schema `CargoResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `departamento_id` | string | Departamento Id |
| `nombre` | string | Nombre |
| `descripcion` | string | Descripcion |
| `activo` | boolean | Activo |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Cargo no encontrado. |
| 409 | Ya existe un cargo con ese nombre. |
| 422 | El departamento no pertenece a la empresa. |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `actualizar_cargo()` — `src/ssas/cargos/infrastructure/http/router.py:136`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas


---

# DEPARTAMENTOS  ·  PA-04

## [API-036] GET `/api/v1/departamentos`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `departamentos:ver` (empresa) o `platform:organizacion:gestionar` (plataforma)

Lista departamentos del alcance autorizado. Permisos: `departamentos:ver` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |
| `activo` | query | ? | no | Filtra por estado activo. |

**Response 200** · schema `list[DepartamentoResponse]`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `descripcion` | string | Descripcion |
| `activo` | boolean | Activo |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `listar_departamentos()` — `src/ssas/departamentos/infrastructure/http/router.py:73`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-037] POST `/api/v1/departamentos`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `departamentos:crear` (empresa) o `platform:organizacion:gestionar` (plataforma)

Crea un departamento dentro de la empresa autorizada. Requiere `departamentos:crear` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `CrearDepartamentoRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `nombre` | string | sí | Nombre |
| `descripcion` | string | no | Descripcion |
| `activo` | boolean | no | Activo |

**Response 201** · schema `DepartamentoResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `descripcion` | string | Descripcion |
| `activo` | boolean | Activo |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | Ya existe un departamento con ese nombre. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `crear_departamento()` — `src/ssas/departamentos/infrastructure/http/router.py:97`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-038] DELETE `/api/v1/departamentos/{departamento_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `departamentos:eliminar` (empresa) o `platform:organizacion:gestionar` (plataforma)

Elimina un departamento sin dependencias dentro de la empresa autorizada. Requiere `departamentos:eliminar` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `departamento_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 204** · schema `sin cuerpo`

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Departamento no encontrado. |
| 409 | El departamento tiene dependencias. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `eliminar_departamento()` — `src/ssas/departamentos/infrastructure/http/router.py:163`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-039] PUT `/api/v1/departamentos/{departamento_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-04 / CU-19  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `departamentos:editar` (empresa) o `platform:organizacion:gestionar` (plataforma)

Actualiza un departamento de la empresa autorizada. Requiere `departamentos:editar` o `platform:organizacion:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `departamento_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `ActualizarDepartamentoRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `nombre` | string | no | Nombre |
| `descripcion` | string | no | Descripcion |
| `activo` | boolean | no | Activo |

**Response 200** · schema `DepartamentoResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `descripcion` | string | Descripcion |
| `activo` | boolean | Activo |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Departamento no encontrado. |
| 409 | Ya existe un departamento con ese nombre. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `actualizar_departamento()` — `src/ssas/departamentos/infrastructure/http/router.py:129`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas


---

# EMPRESAS  ·  PA-01

## [API-026] GET `/api/v1/empresas`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `platform:empresas:ver`

Lista empresas con búsqueda, estado y paginación. Operación exclusiva de plataforma; requiere `platform:empresas:ver`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `search` | query | ? | no | Busca por razón social, nombre, NIT o slug. |
| `activo` | query | ? | no | Filtra por estado activo. |
| `incluir_eliminadas` | query | boolean | no | Incluye empresas eliminadas lógicamente. |
| `page` | query | integer | no |  |
| `per_page` | query | integer | no |  |

**Response 200** · schema `EmpresaPageResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `items` | array[EmpresaResponse] | Items |
| `total` | integer | Total |
| `page` | integer | Page |
| `per_page` | integer | Per Page |
| `total_pages` | integer | Total Pages |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | La empresa o su administrador ya existe. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `list_empresas()` — `src/ssas/platform/infrastructure/http/router.py:101`
- Guard: `require_platform_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-027] POST `/api/v1/empresas`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `platform:empresas:crear`

Crea la empresa, su administrador inicial y la información de acceso necesaria. Operación exclusiva de plataforma; requiere `platform:empresas:crear`.

**Request** · `application/json` · schema `ProvisionEmpresaRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `empresa` | ? | sí |  |
| `administrador` | ? | sí |  |

**Response 201** · schema `ProvisionEmpresaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `empresa` | ? |  |
| `administrador_id` | string | Administrador Id |
| `administrador_email` | string | Administrador Email |
| `verification_email_sent` | boolean | Verification Email Sent |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Empresa no encontrada. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `provision_empresa()` — `src/ssas/platform/infrastructure/http/router.py:131`
- Guard: `require_platform_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-028] DELETE `/api/v1/empresas/{empresa_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `platform:empresas:eliminar`

Elimina lógicamente la empresa, desactiva sus usuarios y revoca todas sus sesiones. Conserva la información y la bitácora. Operación exclusiva de plataforma; requiere `platform:empresas:eliminar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | path | string | sí |  |

**Response 200** · schema `EmpresaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `nit` | string | Nit |
| `razon_social` | string | Razon Social |
| `nombre_comercial` | string | Nombre Comercial |
| `slug` | string | Slug |
| `email` | string | Email |
| `telefono` | string | Telefono |
| `direccion` | string | Direccion |
| `ciudad` | string | Ciudad |
| `logo_url` | string | Logo Url |
| `activo` | boolean | Activo |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `eliminada` | boolean | Eliminada |
| `fecha_registro` | string | Fecha Registro |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | La empresa ya fue eliminada. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `delete_empresa()` — `src/ssas/platform/infrastructure/http/router.py:323`
- Guard: `require_platform_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-029] GET `/api/v1/empresas/{empresa_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `empresa:ver` (empresa) o `platform:empresas:ver` (plataforma)

Plataforma puede consultar cualquier empresa. Un administrador empresarial solo puede consultar la empresa incluida en su token. Permisos: `empresa:ver` o `platform:empresas:ver`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | path | string | sí |  |

**Response 200** · schema `EmpresaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `nit` | string | Nit |
| `razon_social` | string | Razon Social |
| `nombre_comercial` | string | Nombre Comercial |
| `slug` | string | Slug |
| `email` | string | Email |
| `telefono` | string | Telefono |
| `direccion` | string | Direccion |
| `ciudad` | string | Ciudad |
| `logo_url` | string | Logo Url |
| `activo` | boolean | Activo |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `eliminada` | boolean | Eliminada |
| `fecha_registro` | string | Fecha Registro |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Empresa no encontrada. |
| 409 | El NIT o el slug ya está siendo utilizado. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `get_empresa()` — `src/ssas/platform/infrastructure/http/router.py:184`
- Guard: `require_empresa_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-030] PATCH `/api/v1/empresas/{empresa_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `empresa:editar` (empresa) o `platform:empresas:editar` (plataforma)

Actualiza únicamente los campos enviados. El NIT y el slug deben continuar siendo únicos. Permisos: `empresa:editar` o `platform:empresas:editar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | path | string | sí |  |

**Request** · `application/json` · schema `EmpresaUpdateRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `nit` | string | no | Nit |
| `razon_social` | string | no | Razon Social |
| `nombre_comercial` | string | no | Nombre Comercial |
| `slug` | string | no | Slug |
| `email` | string | no | Email |
| `telefono` | string | no | Telefono |
| `direccion` | string | no | Direccion |
| `ciudad` | string | no | Ciudad |
| `logo_url` | string | no | Logo Url |

**Response 200** · schema `EmpresaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `nit` | string | Nit |
| `razon_social` | string | Razon Social |
| `nombre_comercial` | string | Nombre Comercial |
| `slug` | string | Slug |
| `email` | string | Email |
| `telefono` | string | Telefono |
| `direccion` | string | Direccion |
| `ciudad` | string | Ciudad |
| `logo_url` | string | Logo Url |
| `activo` | boolean | Activo |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `eliminada` | boolean | Eliminada |
| `fecha_registro` | string | Fecha Registro |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Empresa no encontrada. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `update_empresa()` — `src/ssas/platform/infrastructure/http/router.py:205`
- Guard: `require_empresa_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-031] PATCH `/api/v1/empresas/{empresa_id}/activar`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `platform:empresas:suspender`

Habilita nuevamente la empresa. Operación exclusiva de plataforma; requiere `platform:empresas:suspender`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | path | string | sí |  |

**Response 200** · schema `EmpresaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `nit` | string | Nit |
| `razon_social` | string | Razon Social |
| `nombre_comercial` | string | Nombre Comercial |
| `slug` | string | Slug |
| `email` | string | Email |
| `telefono` | string | Telefono |
| `direccion` | string | Direccion |
| `ciudad` | string | Ciudad |
| `logo_url` | string | Logo Url |
| `activo` | boolean | Activo |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `eliminada` | boolean | Eliminada |
| `fecha_registro` | string | Fecha Registro |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Empresa no encontrada. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `activate_empresa()` — `src/ssas/platform/infrastructure/http/router.py:281`
- Guard: `require_platform_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-032] PATCH `/api/v1/empresas/{empresa_id}/restaurar`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `platform:empresas:restaurar`

Recupera una empresa eliminada y la mantiene suspendida. Después debe usarse `/activar` para habilitar nuevamente el acceso. Operación exclusiva de plataforma; requiere `platform:empresas:restaurar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | path | string | sí |  |

**Response 200** · schema `EmpresaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `nit` | string | Nit |
| `razon_social` | string | Razon Social |
| `nombre_comercial` | string | Nombre Comercial |
| `slug` | string | Slug |
| `email` | string | Email |
| `telefono` | string | Telefono |
| `direccion` | string | Direccion |
| `ciudad` | string | Ciudad |
| `logo_url` | string | Logo Url |
| `activo` | boolean | Activo |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `eliminada` | boolean | Eliminada |
| `fecha_registro` | string | Fecha Registro |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | La empresa no está eliminada. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `restore_empresa()` — `src/ssas/platform/infrastructure/http/router.py:364`
- Guard: `require_platform_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-033] PATCH `/api/v1/empresas/{empresa_id}/suspender`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-01, CU-02  
**Alcance:** plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `platform:empresas:suspender`

Suspende el acceso empresarial sin eliminar sus datos. Operación exclusiva de plataforma; requiere `platform:empresas:suspender`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | path | string | sí |  |

**Response 200** · schema `EmpresaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `nit` | string | Nit |
| `razon_social` | string | Razon Social |
| `nombre_comercial` | string | Nombre Comercial |
| `slug` | string | Slug |
| `email` | string | Email |
| `telefono` | string | Telefono |
| `direccion` | string | Direccion |
| `ciudad` | string | Ciudad |
| `logo_url` | string | Logo Url |
| `activo` | boolean | Activo |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `eliminada` | boolean | Eliminada |
| `fecha_registro` | string | Fecha Registro |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `suspend_empresa()` — `src/ssas/platform/infrastructure/http/router.py:301`
- Guard: `require_platform_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso


---

# SISTEMA  ·  —

## [API-046] GET `/health`

**Estado:** IMPLEMENTADO  
**PA / CU:** — / —  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Endpoint público usado para verificar que la API está levantada.

**Response 200** · schema `sin cuerpo`

**Implementación**

- Handler: `?()` — `?:0`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso


---

# POSTULACIONES  ·  PA-02

## [API-044] POST `/api/v1/publico/postulaciones`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-02 / CU-09, CU-12  
**Alcance:** público  
**Autenticación:** No  
**Permiso:** —

Recibe un formulario publico multipart con datos del postulante y CV. Crea o actualiza el postulante por empresa, crea la postulacion y devuelve un codigo de seguimiento.

**Response 201** · schema `PostulacionPublicaResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `codigo_seguimiento` | string | Codigo Seguimiento |
| `estado` | string | Estado |
| `fecha_postulacion` | string | Fecha Postulacion |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 404 | La vacante no existe o no esta publicada. |
| 409 | El postulante ya postulo a esta vacante. |
| 422 | Datos invalidos, CV invalido o etapa inicial no configurada. |

**Implementación**

- Handler: `crear_postulacion_publica()` — `src/ssas/postulaciones/infrastructure/http/router.py:76`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso

## [API-045] GET `/api/v1/publico/postulaciones/{codigo}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-02 / CU-09, CU-12  
**Alcance:** autenticado  
**Autenticación:** Sí (Bearer)  
**Permiso:** solo autenticación

Consulta el estado de una postulacion publica mediante su codigo de seguimiento.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `codigo` | path | string | sí |  |

**Response 200** · schema `SeguimientoPostulacionResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `codigo_seguimiento` | string | Codigo Seguimiento |
| `estado` | string | Estado |
| `etapa` | string | Etapa |
| `vacante` | string | Vacante |
| `fecha_postulacion` | string | Fecha Postulacion |
| `fecha_ultimo_cambio` | string | Fecha Ultimo Cambio |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 404 | No existe una postulacion con ese codigo. |
| 422 | Validation Error |

**Implementación**

- Handler: `consultar_postulacion_publica()` — `src/ssas/postulaciones/infrastructure/http/router.py:136`
- Guard: `—`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso


---

# ROLES  ·  PA-01

## [API-020] GET `/api/v1/roles`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-05  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Lista los roles disponibles en el alcance seleccionado. Permiso: `roles:gestionar` para empresa o `platform:usuarios:gestionar` para plataforma.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `list[RoleSchema]`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `name` | string | Name |
| `codigo` | string | Codigo |
| `description` | string | Description |
| `is_active` | boolean | Is Active |
| `permissions` | array[PermissionSchema] | Permissions |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | Ya existe un rol con el mismo código en el alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `list_roles()` — `src/ssas/roles/infrastructure/http/router.py:79`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-021] POST `/api/v1/roles`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-05  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Crea un rol dentro del alcance seleccionado. Los códigos de rol deben ser únicos en ese alcance.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `CreateRoleRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `name` | string | sí | Name |
| `codigo` | string | sí | Codigo |
| `description` | string | no | Description |

**Response 201** · schema `RoleSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `name` | string | Name |
| `codigo` | string | Codigo |
| `description` | string | Description |
| `is_active` | boolean | Is Active |
| `permissions` | array[PermissionSchema] | Permissions |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `create_role()` — `src/ssas/roles/infrastructure/http/router.py:101`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-022] DELETE `/api/v1/roles/{role_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-05  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Elimina un rol del alcance autorizado cuando no está protegido por reglas del sistema.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `role_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 204** · schema `sin cuerpo`

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Rol no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `delete_role()` — `src/ssas/roles/infrastructure/http/router.py:193`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-023] GET `/api/v1/roles/{role_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-05  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Obtiene el rol y los permisos que tiene asignados dentro del alcance autorizado.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `role_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `RoleSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `name` | string | Name |
| `codigo` | string | Codigo |
| `description` | string | Description |
| `is_active` | boolean | Is Active |
| `permissions` | array[PermissionSchema] | Permissions |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Rol no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `get_role()` — `src/ssas/roles/infrastructure/http/router.py:133`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-024] PATCH `/api/v1/roles/{role_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-05  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Actualiza los campos enviados sin modificar los permisos que ya tiene asignados.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `role_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `UpdateRoleRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `name` | string | no | Name |
| `description` | string | no | Description |
| `is_active` | boolean | no | Is Active |

**Response 200** · schema `RoleSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `name` | string | Name |
| `codigo` | string | Codigo |
| `description` | string | Description |
| `is_active` | boolean | Is Active |
| `permissions` | array[PermissionSchema] | Permissions |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Rol no encontrado dentro del alcance. |
| 409 | Ya existe un rol con el mismo código en el alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `update_role()` — `src/ssas/roles/infrastructure/http/router.py:159`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-025] PUT `/api/v1/roles/{role_id}/permissions`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-05  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `roles:gestionar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Reemplaza el conjunto completo de permisos del rol. Los permisos deben existir y ser válidos para el alcance.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `role_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `AssignPermissionsRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `permission_ids` | array[string] | sí | Permission Ids |

**Response 200** · schema `RoleSchema`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `name` | string | Name |
| `codigo` | string | Codigo |
| `description` | string | Description |
| `is_active` | boolean | Is Active |
| `permissions` | array[PermissionSchema] | Permissions |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | El rol o alguno de los permisos no existe. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `assign_permissions()` — `src/ssas/roles/infrastructure/http/router.py:224`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas


---

# USUARIOS  ·  PA-01

## [API-010] GET `/api/v1/usuarios`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:ver` (empresa) o `platform:usuarios:gestionar` (plataforma)

Lista usuarios con búsqueda, estado y paginación. Permisos: `usuarios:ver` para empresa o `platform:usuarios:gestionar` para plataforma.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |
| `search` | query | ? | no | Busca por nombre, usuario o correo. |
| `is_active` | query | ? | no | Filtra por estado activo. |
| `incluir_eliminados` | query | boolean | no | Incluye cuentas eliminadas lógicamente. Requiere el mismo alcance autorizado. |
| `page` | query | integer | no |  |
| `per_page` | query | integer | no |  |

**Response 200** · schema `UsuarioPageResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `items` | array[UsuarioResponse] | Items |
| `total` | integer | Total |
| `page` | integer | Page |
| `per_page` | integer | Per Page |
| `total_pages` | integer | Total Pages |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | El correo o nombre de usuario ya está registrado. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `listar_usuarios()` — `src/ssas/usuarios/infrastructure/http/router.py:115`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-011] POST `/api/v1/usuarios`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:crear` (empresa) o `platform:usuarios:gestionar` (plataforma)

Crea una cuenta y asigna sus roles. Un administrador empresarial crea usuarios solo en su empresa; plataforma puede crear usuarios globales o indicar `empresa_id`. Permisos: `usuarios:crear` o `platform:usuarios:gestionar`.

**Request** · `application/json` · schema `CrearUsuarioRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `empresa_id` | string | no | Empresa Id |
| `nombre` | string | sí | Nombre |
| `apellido` | string | sí | Apellido |
| `email` | string | sí | Email |
| `username` | string | sí | Username |
| `password` | string | sí | Password |
| `telefono` | string | no | Telefono |
| `role_ids` | array[string] | sí | Role Ids |

**Response 201** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Usuario no encontrado dentro del alcance. |
| 409 | El correo o nombre de usuario ya está registrado. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `crear_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:157`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-012] DELETE `/api/v1/usuarios/{usuario_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:eliminar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Elimina lógicamente la cuenta, desactiva su acceso y revoca sus sesiones sin borrar roles ni bitácora. No permite autoeliminación ni eliminar al último administrador activo. Permisos: `usuarios:eliminar` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | La cuenta no puede eliminarse en su estado actual. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `eliminar_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:297`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-013] GET `/api/v1/usuarios/{usuario_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:ver` (empresa) o `platform:usuarios:gestionar` (plataforma)

Obtiene una cuenta por identificador dentro del alcance autorizado. Permisos: `usuarios:ver` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Usuario no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `obtener_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:366`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-014] PATCH `/api/v1/usuarios/{usuario_id}`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:editar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Actualiza únicamente los campos enviados y, cuando corresponda, reemplaza sus roles. Permisos: `usuarios:editar` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `ActualizarUsuarioRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `nombre` | string | no | Nombre |
| `apellido` | string | no | Apellido |
| `email` | string | no | Email |
| `username` | string | no | Username |
| `telefono` | string | no | Telefono |
| `role_ids` | array | no | Role Ids |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Usuario no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `actualizar_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:191`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-015] PATCH `/api/v1/usuarios/{usuario_id}/activar`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:editar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Habilita el acceso de una cuenta dentro del alcance autorizado. Permisos: `usuarios:editar` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Usuario no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `activar_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:230`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-016] PATCH `/api/v1/usuarios/{usuario_id}/desactivar`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:editar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Deshabilita el acceso sin eliminar la cuenta. No permite desactivar al último administrador del alcance. Permisos: `usuarios:editar` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Usuario no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `desactivar_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:263`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-017] PATCH `/api/v1/usuarios/{usuario_id}/desbloquear`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:desbloquear` (empresa) o `platform:usuarios:gestionar` (plataforma)

Restablece los intentos fallidos y elimina el bloqueo temporal. Permisos: `usuarios:desbloquear` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `desbloquear_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:431`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-018] PUT `/api/v1/usuarios/{usuario_id}/password`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:cambiar_password` (empresa) o `platform:usuarios:gestionar` (plataforma)

Establece una contraseña nueva, permite exigir cambio en el siguiente acceso y revoca sesiones existentes. Permisos: `usuarios:cambiar_password` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Request** · `application/json` · schema `CambiarPasswordUsuarioRequest`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `new_password` | string | sí | New Password |
| `must_change` | boolean | no | Must Change |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 404 | Usuario no encontrado dentro del alcance. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `cambiar_password_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:393`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas

## [API-019] PATCH `/api/v1/usuarios/{usuario_id}/restaurar`

**Estado:** IMPLEMENTADO  
**PA / CU:** PA-01 / CU-04  
**Alcance:** empresa + plataforma  
**Autenticación:** Sí (Bearer)  
**Permiso:** `usuarios:restaurar` (empresa) o `platform:usuarios:gestionar` (plataforma)

Recupera una cuenta eliminada y la mantiene inactiva. Después debe usarse `/activar` para habilitar su acceso. Permisos: `usuarios:restaurar` o `platform:usuarios:gestionar`.

**Parámetros**

| Nombre | En | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `usuario_id` | path | string | sí |  |
| `empresa_id` | query | ? | no | Identificador de empresa. Los administradores de plataforma pueden indicarlo para seleccionar el alcance; los usuarios empresariales quedan limitados a su propia empresa. |

**Response 200** · schema `UsuarioResponse`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Id |
| `empresa_id` | string | Empresa Id |
| `nombre` | string | Nombre |
| `apellido` | string | Apellido |
| `email` | string | Email |
| `username` | string | Username |
| `telefono` | string | Telefono |
| `is_active` | boolean | Is Active |
| `email_verified` | boolean | Email Verified |
| `must_change_password` | boolean | Must Change Password |
| `failed_login_attempts` | integer | Failed Login Attempts |
| `locked_until` | string | Locked Until |
| `eliminado_at` | string | Eliminado At |
| `eliminado_por_id` | string | Eliminado Por Id |
| `is_deleted` | boolean | Is Deleted |
| `roles` | array[string] | Roles |
| `created_at` | string | Created At |
| `updated_at` | string | Updated At |

**Errores documentados**

| HTTP | Situación |
|---|---|
| 401 | Token de acceso ausente, inválido o vencido. |
| 403 | El usuario no tiene el permiso requerido, intenta operar fuera de su empresa o debe cambiar primero su contraseña. |
| 409 | La cuenta no está eliminada. |
| 422 | Validation Error |
| 503 | El servicio o una dependencia externa no está disponible. |

**Implementación**

- Handler: `restaurar_usuario()` — `src/ssas/usuarios/infrastructure/http/router.py:333`
- Guard: `require_scoped_permission`

**Tests** · `[ ]` éxito `[ ]` validaciones `[ ]` 401 sin token `[ ]` 403 sin permiso `[ ]` aislamiento entre empresas


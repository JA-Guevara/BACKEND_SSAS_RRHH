# OpenAPI y versionado de API - Sprint 1

## Contrato oficial

El contrato oficial del backend SSAH RRHH se publica desde FastAPI en:

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`

La version actual de la API es `v1` y todas las rutas funcionales del backend deben exponerse bajo el prefijo:

```text
/api/v1
```

El archivo `openapi.json` generado por FastAPI es la fuente de sincronizacion entre los equipos backend, web y movil. Antes de consumir o modificar endpoints, los frentes deben revisar ese contrato y validar nombres de rutas, cuerpos de request, codigos de respuesta y modelos de respuesta.

## Regla de versionado

Los cambios compatibles pueden mantenerse dentro de `/api/v1`. Se consideran compatibles los cambios que no rompen clientes existentes, por ejemplo agregar campos opcionales, agregar nuevos endpoints o ampliar respuestas sin quitar datos ya publicados.

Los cambios que rompen contrato no deben fusionarse sin aviso previo a web y movil. Se consideran cambios rompientes quitar o renombrar campos, cambiar tipos, cambiar codigos de respuesta esperados, cambiar rutas existentes o volver obligatorio un campo que antes era opcional.

Los cambios mayores deben planificarse como una nueva version de API, por ejemplo `/api/v2`, y deben convivir temporalmente con `/api/v1` cuando haya clientes activos usando la version anterior.

## Alcance Sprint 1

En Sprint 1 el contrato cubre:

- Autenticacion: login, refresh, logout y perfil autenticado.
- Departamentos: CRUD filtrado por empresa.
- Cargos: CRUD filtrado por empresa y departamento.
- Portal publico: envio de postulacion con CV y consulta por codigo de seguimiento.
- Estado del servicio: `/health`.

Los endpoints privados usan `Authorization: Bearer <access_token>`. Las rutas del portal publico no requieren JWT.

## Pendientes identificados

Al momento de esta documentacion, no se encontro router HTTP real para vacantes ni endpoints internos de gestion de postulaciones. Por eso la coleccion Postman incluye sus carpetas como pendientes, sin inventar rutas que todavia no existen en el backend.

# Contrato OpenAPI y Versionado

## Objetivo

El contrato OpenAPI generado por FastAPI es el punto de sincronizacion entre el backend SSAS RRHH, el frontend web, el frontend movil y cualquier otro consumidor de la API.

Cada equipo debe usar este contrato para conocer endpoints, metodos HTTP, esquemas de request, esquemas de response, codigos de estado y requisitos de autenticacion/autorizacion.

## URLs locales

Swagger UI:

http://127.0.0.1:8000/docs

ReDoc:

http://127.0.0.1:8000/redoc

OpenAPI JSON:

http://127.0.0.1:8000/openapi.json

Health:

http://127.0.0.1:8000/health

## URLs de produccion

Swagger UI:

https://<railway-domain>/docs

OpenAPI JSON:

https://<railway-domain>/openapi.json

Health:

https://<railway-domain>/health

## Version actual

- Version OpenAPI/backend: 0.1.0
- Prefijo actual de API: /api/v1
- Version funcional del contrato: v1

## Regla de versionado

Mientras el contrato sea compatible, la API mantiene el prefijo /api/v1.

Si se necesitan cambios rompientes grandes, debe crearse una nueva version funcional, por ejemplo /api/v2.

No se debe cambiar /api/v1 de forma rompiente sin avisar y coordinar previamente con los equipos de frontend web y movil.

## Cambios compatibles

Se consideran compatibles, en general:

- Agregar un endpoint nuevo.
- Agregar un campo opcional en una respuesta.
- Agregar un query parameter opcional.
- Ampliar documentacion.
- Agregar nuevos status codes sin romper los existentes.
- Agregar nuevos permisos sin cambiar los existentes.

## Cambios rompientes

Se consideran rompientes, en general:

- Eliminar un endpoint.
- Cambiar el metodo HTTP de un endpoint existente.
- Cambiar un path existente.
- Renombrar un campo de request o response.
- Cambiar el tipo de dato de un campo.
- Volver requerido un campo que antes era opcional.
- Quitar un campo usado por frontend web o movil.
- Cambiar la estructura de una respuesta.
- Cambiar el significado de un status code.
- Cambiar el formato de errores.
- Cambiar permisos requeridos para una ruta sin avisar.

## Proceso antes de fusionar un cambio rompiente

Antes de fusionar un cambio rompiente se debe:

- Avisar al equipo web.
- Avisar al equipo movil.
- Actualizar esta documentacion.
- Actualizar el contrato OpenAPI.
- Coordinar la fecha de cambio.
- Mantener compatibilidad si no existe coordinacion.

## Checklist para Pull Requests

Antes de fusionar un Pull Request que toque API, revisar:

- Cambia OpenAPI?
- Agrega endpoint?
- Modifica request schema?
- Modifica response schema?
- Cambia permisos?
- Es cambio compatible?
- Es cambio rompiente?
- Se aviso a web/movil?

## Como exportar el contrato OpenAPI

Con el backend corriendo, se puede exportar el contrato desde PowerShell:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/openapi.json" -OutFile "docs/openapi-v1.json"
```

O usando curl.exe:

```powershell
curl.exe http://127.0.0.1:8000/openapi.json -o docs/openapi-v1.json
```

## Archivos a versionar

Se debe versionar este documento:

docs/CONTRATO_OPENAPI_Y_VERSIONADO.md

Opcionalmente se puede exportar y versionar:

docs/openapi-v1.json

Si se versiona docs/openapi-v1.json, debe actualizarse cada vez que cambien endpoints, schemas o metadata OpenAPI. Si mantenerlo se vuelve pesado, la fuente principal sigue siendo /openapi.json generado por FastAPI.

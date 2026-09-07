# Documentación de SSAS RRHH

Backend del Sistema de Gestión de Recursos Humanos, plataforma SaaS multi-tenant.
Sistemas de Información 2 · UAGRM · Grupo N.° 12.

## Sistema de control — leer en este orden

| # | Documento | Para qué |
|---|---|---|
| 1 | **[01_ESTADO_PROYECTO.md](01_ESTADO_PROYECTO.md)** | Estado de cada área, arquitectura real, reglas que los agentes deben respetar. **Empezar acá.** |
| 2 | **[02_API_ENDPOINTS.md](02_API_ENDPOINTS.md)** | Contrato de los 46 endpoints implementados y los 18 pendientes. Generado desde el OpenAPI. |
| 3 | **[03_BACKLOG_IMPLEMENTACION.md](03_BACKLOG_IMPLEMENTACION.md)** | Las 36 tareas con dependencias y criterios de aceptación. Elegí un ID y trabajá. |
| 4 | **[04_EJECUCION_MULTIAGENTE_SPRINT1.md](04_EJECUCION_MULTIAGENTE_SPRINT1.md)** | Cómo correr el Sprint 1 con varios agentes: olas, reparto de archivos, contrato del agente y decisiones pendientes. |
| — | [tareas_sprint1.json](tareas_sprint1.json) | Las mismas tareas en formato consumible por un orquestador. |

> **Antes de asignar la primera tarea:** la Ola 0 del documento 04 lista cinco
> bloqueadores verificados el 2026-09-07. Entre ellos, `alembic upgrade head` falla por
> dos cabezas y `pytest` a secas no corre. Nada arranca hasta que esa ola esté en verde.

Los cuatro se mantienen sincronizados con el código. Antes de confiar en ellos:

```bash
python scripts/verificar_documentacion.py
```

Falla si una ruta del código no está documentada, si algo marcado IMPLEMENTADO no
existe, o si una referencia cruzada entre documentos no resuelve.

## Referencia

| Documento | Contenido |
|---|---|
| [arquitectura/ARQUITECTURA_BACKEND_FASTAPI.md](arquitectura/ARQUITECTURA_BACKEND_FASTAPI.md) | Documento de diseño: Vertical Slicing, Hexagonal, reglas de dependencias |
| [arquitectura/CONTRATO_OPENAPI_Y_VERSIONADO.md](arquitectura/CONTRATO_OPENAPI_Y_VERSIONADO.md) | Convenciones de OpenAPI, versionado y cambios rompientes |
| [guias/GUIA_DESARROLLO.md](guias/GUIA_DESARROLLO.md) | Puesta en marcha y flujo de trabajo |
| [guias/AUTH_Y_USUARIOS.md](guias/AUTH_Y_USUARIOS.md) | Guía funcional de autenticación y usuarios |
| [guias/PLATFORM_ADMINISTRACION.md](guias/PLATFORM_ADMINISTRACION.md) | Guía funcional de superadministración |
| [sprints/SPRINT_0_ADAPTACION_ORM.md](sprints/SPRINT_0_ADAPTACION_ORM.md) | Registro histórico del Sprint 0 |
| [postman/](postman/) | Colección Postman (pendiente de regenerar: ver `DOC-002`) |
| [_archivo/](_archivo/) | Documentación retirada, con el motivo de cada retiro |

## Fuentes de verdad

| Qué | Dónde |
|---|---|
| Esquema de la base | `migrations/versions/` — **no** un `.sql` a mano |
| Contrato de la API | `GET /openapi.json` de la aplicación |
| Permisos | catálogo en la tabla `permiso`, sembrado por migración |
| Estado del desarrollo | los tres documentos de arriba, verificados por el script |

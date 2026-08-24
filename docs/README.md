# Documentación de SSAS RRHH

Este directorio concentra la información técnica, decisiones, análisis y evidencias del backend.

## Guías

- [Guía de desarrollo](guias/GUIA_DESARROLLO.md): instalación, ejecución, variables, pruebas,
  endpoints, Git y estado actual.

## Arquitectura y contratos

- [Arquitectura del backend](arquitectura/ARQUITECTURA_BACKEND_FASTAPI.md): principios, módulos,
  capas y decisiones arquitectónicas.
- [Contrato OpenAPI y versionado](arquitectura/CONTRATO_OPENAPI_Y_VERSIONADO.md): reglas de
  compatibilidad para clientes web y móvil.

## Análisis

- [Análisis y propuesta del backend](analisis/ANALISIS_Y_PROPUESTA_BACKEND.md): diagnóstico
  histórico y decisiones de evolución.

## Sprints

- [Sprint 0 — adaptación ORM](sprints/SPRINT_0_ADAPTACION_ORM.md): modelos multiempresa,
  migraciones aplicadas y verificaciones realizadas.

## Regla de organización

- La raíz conserva únicamente archivos operativos y un `README.md` de entrada.
- Los documentos nuevos deben ubicarse en la categoría correspondiente dentro de `docs/`.
- Los archivos generados, cachés, entornos virtuales y secretos no se versionan.

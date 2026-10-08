# ADR 0008: Separación del Módulo de Empleados del Dominio de Selección

- **Estado:** Aceptado
- **Fecha:** Octubre 2026
- **Contexto:** Sprint 2 (Desacoplamiento de Selección y Contratación) / Preparación para Sprint 3
- **Decisores:** Equipo de Arquitectura Backend (Grupo 12)

---

## 1. Contexto y Problema

Durante el diseño inicial de los endpoints de la API, las rutas de empleados (`GET /api/v1/empleados` y `GET /api/v1/empleados/{id}`) se encontraban alojadas de manera provisional dentro del archivo de router de selección (`seleccion_router.py`).

Esta ubicación generaba diversos problemas arquitectónicos:
1. **Confusión de Dominios de Negocio:** El dominio de **Selección** (`ssas.seleccion`) modela postulantes, candidatos, entrevistas, evaluaciones y rankings. Por el contrario, el dominio de **Empleados** (`ssas.empleados`) modela el personal activo contratado por la organización, su información laboral formal, datos personales sensibles y datos bancarios/previsionales.
2. **Violación del Principio de Responsabilidad Única (SRP):** El router de selección acumulaba endpoints de dos entidades del ciclo de vida completamente distintas (candidatos externos vs empleados internos).
3. **Escalabilidad Hacia Sprints Futuros:** El Sprint 3 y subsiguientes requieren expandir las funcionalidades sobre empleados: gestión de asistencia, control de turnos, legajos, ausencias, evaluaciones de desempeño y nóminas/liquidaciones. Mantener empleados acoplado a selección impedía el crecimiento modular e independiente de estos módulos.

---

## 2. Decisión de Diseño

Se resolvió formalizar la separación arquitectónica completa:

1. **Creación del Router Independiente:**
   Se implementó `src/ssas/empleados/infrastructure/http/router.py` con prefijo `/empleados` y tag OpenAPI dedicado `"Empleados"`.
2. **Schemas HTTP Dedicados:**
   Se definieron `EmpleadoListItemResponse`, `EmpleadoDetalleResponse` y `ListaEmpleadosResponse` en `src/ssas/empleados/infrastructure/http/schemas.py`, estructurando con precisión los tipos de datos expuestos (incluyendo datos bancarios y personales).
3. **Guardia de Permisos Extraída:**
   Se extrajo la dependencia de seguridad `permiso("empleados:leer")` a `src/ssas/core/api/guards.py`, permitiendo su reutilización limpia sin dependencias cruzadas entre routers.
4. **Registro Centralizado en la API:**
   El router de empleados se registra en `src/ssas/core/api/router.py` bajo `/api/v1/empleados`, desacoplado totalmente de `src/ssas/seleccion/infrastructure/http/router.py`.
5. **Enlace Trazable con Selección:**
   En el modelo de datos y en la respuesta detallada del empleado se mantiene la referencia opcional `postulacion_id`, permitiendo trazabilidad bidireccional entre el proceso de selección de origen y la ficha formal del empleado contratado.

---

## 3. Consecuencias y Beneficios

### Positivas:
- **Alta Cohesión y Bajo Acoplamiento:** Cada módulo responde exclusivamente a su contexto delimitado (*Bounded Context* de DDD).
- **Control de Acceso Granular:** El permiso `empleados:leer` se evalúa de forma específica e independiente de los permisos de selección (`seleccion:leer`), protegiendo datos personales y bancarios sensibles de los colaboradores.
- **Base Sólida para Sprint 3 y 4:** Los módulos futuros de Asistencia, Turnos y Nóminas pueden consumir directamente el repositorio y servicios del módulo `ssas.empleados` sin intermediarios ni dependencias artificiales con Selección.
- **Documentación OpenAPI Limpia:** Swagger UI y ReDoc presentan la sección "Empleados" como un dominio de primer nivel claramente diferenciado.

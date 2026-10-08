# DOC-04 · Resolver la promesa de la app móvil

> Cambios exactos a aplicar en el perfil de proyecto para que la declaración de alcance sea verdadera.
> Decisión del equipo: **Camino A** — ajustar el documento (el alcance de este plan es
> "back y front por ahora"; el móvil queda para un sprint posterior).

## 1. Tabla de implementación — cambiar "WEB / MÓVIL" por "WEB"

| CU | Funcionalidad | Antes | Después |
|---|---|---|---|
| CU-14 | Visualizar ranking de candidatos | **WEB / MÓVIL** | **WEB** |
| CU-15 | Programar y confirmar entrevistas | **WEB / MÓVIL** | **WEB** |

## 2. Sección 2.1.5.3 · Diagramas de navegación

Los diagramas **NAV-2 (postulante en móvil)** y **NAV-3 (reclutador en móvil)** deben:

- **Opción A (recomendada):** eliminarse de la sección, **o**
- **Opción B:** conservarse con una nota explícita:

  > *"NAV-2 y NAV-3 corresponden a un diseño previsto para un sprint posterior. La app móvil no forma
  > parte del alcance entregado en el Sprint 2 (ver ADR/decisión de alcance)."*

## 3. Texto de cierre sugerido (si se deja constancia en el perfil)

> El Sprint 2 entrega el flujo de selección sobre el **portal web** y el **portal público**. La
> aplicación móvil (Flutter) permanece sin cambios en este sprint: sus únicos commits corresponden a
> login y bitácora, y será la base para los módulos de autoservicio y marcación de asistencia en
> sprints posteriores. En consecuencia, CU-14 y CU-15 se declaran de implementación **web**, y los
> diagramas NAV-2/NAV-3 figuran como diseño previsto, no como funcionalidad entregada.

## Referencia interna

La misma decisión está documentada en `docs/sprints/sprint-2-seleccion.md` §5.
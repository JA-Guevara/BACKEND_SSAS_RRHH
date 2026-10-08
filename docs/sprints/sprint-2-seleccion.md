# Sprint 2: Módulo de Selección, IA y Gestión de Candidatos

> **Sistemas de Información 2 (INF 412-SA) · UAGRM · Grupo N.° 12**  
> **Estado:** Implementado. Métricas de calidad pendientes de adjuntar desde `docs/evidencias/` (ver §4).  
> **Fecha de cierre:** Octubre 2026  

---

## 1. Resumen Ejecutivo del Sprint

El Sprint 2 consolida el flujo integral de **Selección de Personal**, integrando el procesamiento inteligente de currículums (IA con Google Gemini y contingencia local), portal público de postulaciones y seguimiento, programación y confirmación de entrevistas, registro de evaluaciones técnicas y psicotécnicas, cálculo de rankings de candidatos y la transición final de candidatos seleccionados a la nómina de empleados activos.

| Métrica | Estado |
|---|---|
| **Casos de Uso Implementados** | CU-13 a CU-19 (siete casos de uso), todos implementados |
| **Pruebas Unitarias Backend** | Salida real guardada en `docs/evidencias/pytest.txt` y `cobertura.txt` (véase §4) |
| **Pruebas Unitarias Frontend** | Salida real guardada en `docs/evidencias/vitest.txt` |
| **TypeScript / Build** | `npm run build` en `docs/evidencias/build.txt` |
| **ESLint Frontend** | `npm run lint` en `docs/evidencias/lint.txt` |
| **Contrato OpenAPI** | `openapi_dump.json` + `schema.d.ts` sincronizados; 118 rutas en `/api/v1` |

---

## 2. Casos de Uso del Sprint (CU-13 a CU-19)

Los siete casos de uso responden a la numeración del perfil de proyecto: **CU-13** Análisis de CV **· CU-14** Ranking **· CU-15** Entrevistas (con confirmación pública) **· CU-16** Resultados y evaluaciones **· CU-17** Comparar finalistas **· CU-18** Banco de talentos **· CU-19** Contratar y alta de empleado.

### CU-13 · Análisis de CV con IA y Extracción de Datos (100%)
- **Backend:** `ssas.analisis_cv`.
- **Estrategia Dual:**
  - Proveedor principal: `GeminiAnalysisProvider` (`gemini-3.5-flash-lite`) que extrae habilidades, experiencia y resumen con validación estricta de evidencia en texto y cálculo de afinidad respecto a la vacante.
  - Proveedor de contingencia: `ExtraccionLocalProvider` (`extraccion-local-v1`), determinista, basado en catálogo léxico y regex, garantizando resiliencia operativa ante cuotas agotadas o desconexión externa (ADR 0007).
  - Selector automático vía `ia_proveedor_cv` en `Settings` (`auto`, `gemini`, `local`); en modo `auto` sin clave configurada se usa el proveedor local.
  - Degradación elegante: solo ante errores 502/503/504 del proveedor primario se recurre al respaldo local; `validar_evidencia` y `calcular_afinidad` se ejecutan fuera del bloque de reintento para que el puntaje sea idéntico venga la extracción de donde venga.
- **Endpoint:** `POST /api/v1/postulaciones/{id}/analisis-cv`.
- **Pruebas:** `test_extraccion_local.py` (15 tests) y `test_analisis_cv_respaldo.py` (10 tests), más el flujo completo de punta a punta (QA-04, §4).

### CU-14 · Ranking de Candidatos (100%)
- **Backend:** `GET /api/v1/seleccion/vacantes` (vacantes en selección) y `GET /api/v1/vacantes/{id}/ranking`.
- Algoritmo de ponderación combinada: Puntaje IA de afinidad (CV) + Puntaje manual de reclutador + Entrevistas + Evaluaciones.
- **Frontend:** `SeleccionPage` con tabla comparativa de habilidades detectadas vs faltantes por candidato.

### CU-15 · Gestión de Entrevistas y Confirmación Pública (100%)
- **Backend:**
  - `POST /api/v1/entrevistas` (programar) y `GET /api/v1/entrevistas` (agenda filtrable); `GET /api/v1/entrevistas/{id}` y `PATCH /api/v1/entrevistas/{id}`; transiciones por `PATCH /api/v1/entrevistas/{id}/estado` y resultados por `PATCH /api/v1/entrevistas/{id}/resultado`.
  - `GET /api/v1/publico/postulaciones/{codigo}/entrevista`: endpoint público sin autenticación para que el candidato consulte su entrevista agendada.
  - `POST /api/v1/publico/postulaciones/{codigo}/entrevista/confirmar`: confirmación pública de asistencia con transición de `PROGRAMADA` a `CONFIRMADA`.
- **Frontend:**
  - Formulario de programación de entrevistas con validación estricta de enlaces HTTPS virtuales.
  - Componente público `EntrevistaAgendada` integrado en `SeguimientoPostulacion`, permitiendo confirmación en un clic y mostrando enlace seguro a la sala virtual o ubicación presencial.

### CU-16 · Resultados y Evaluaciones Técnicas y Psicotécnicas (100%)
- **Backend:** `POST /api/v1/postulaciones/{id}/evaluaciones` y `GET /api/v1/postulaciones/{id}/evaluaciones`.
  - Registro de evaluaciones con tipo (`TECNICA`, `PSICOTECNICA`, `MEDICA`, `OTRO`), puntaje (0-100), observaciones y evaluador; actualización por `PATCH /api/v1/evaluaciones/{id}`.
  - Impacto directo en el promedio de puntaje de evaluaciones dentro del ranking general de la vacante.
- **Frontend:** `EvaluacionForm` dentro de modal accesible con validación de evaluador en alcance de la empresa y gestión de foco.

### CU-17 · Comparar Finalistas (100%)
- **Backend:** `POST /api/v1/vacantes/{id}/comparar` — compara entre dos y cuatro postulaciones de la vacante y devuelve el detalle de cada candidato con su ranking.
- **Frontend:** vista de comparación en `SeleccionPage`. La decisión de contratación corresponde al personal autorizado, no a la IA.

### CU-18 · Gestionar Banco de Talentos (100%)
- **Backend:** `PATCH /api/v1/postulantes/{id}/banco-talento` (alta/baja en el banco de talentos) y `POST /api/v1/postulantes/{id}/postulaciones` (asociación de un candidato a una vacante, respuesta tipada `AsociacionResponse`, 201).
- **Frontend:** acciones de banco de talentos dentro del flujo de selección.

### CU-19 · Contratación y Alta de Empleado (100%)
- **Backend:**
  - `POST /api/v1/postulaciones/{id}/contratar`: transición formal de candidato a nuevo registro en la tabla `empleados`, vinculando `postulacion_id`, asignando código laboral correlativo y estableciendo estado inicial `ACTIVO`.
  - Módulo independiente `ssas.empleados` (ADR 0008) con endpoints `GET /api/v1/empleados` (filtrado y paginación) y `GET /api/v1/empleados/{id}` (ficha laboral, personal y bancaria enmascarada).
- **Frontend:**
  - Módulo `/empleados` accesible desde navegación principal con control de acceso por permisos (`empleados:ver`).
  - Grilla de empleados con búsqueda en tiempo real, selector de estado, paginación y modal detallado `EmpleadoDetalleModal` con enmascaramiento de cuentas bancarias (`••••1234`) y enlace de retorno al proceso de selección de origen.

---

## 3. Mejoras Arquitectónicas Clave del Sprint

### 3.1 Proveedor de Extracción Local (`ExtraccionLocalProvider`)
Se introdujo como mecanismo de contingencia frente a límites de la API de Google Gemini (ADR 0007). Cuenta con:
- Búsqueda de habilidades del catálogo con límite de palabras completas (evita el falso positivo de "Java" dentro de "javascript") y tabla de sinónimos (Postgres/PostgreSQL, TS/TypeScript, JS/JavaScript, React/ReactJS, Py/Python).
- Análisis de expresiones regulares multilingües para años de experiencia laboral.
- Auditoría explícita en base de datos mediante el campo `modelo_usado: "extraccion-local-v1"`.
- La evidencia se recorta del propio texto normalizado, por lo que `validar_evidencia` siempre se cumple por construcción.
- No realiza ninguna llamada de red; reproducible sin clave de API.

### 3.2 Desacoplamiento del Módulo de Empleados
Conforme al ADR 0008, los endpoints de empleados se extrajeron del router de selección a un módulo independiente:
- Router: `src/ssas/empleados/infrastructure/http/router.py`
- Schemas: `src/ssas/empleados/infrastructure/http/schemas.py`
- Guardia de permiso: `permiso("empleados:ver")` en `src/ssas/core/api/guards.py`
- Aislamiento multi-tenant: filtra por `empresa_id` resuelto desde el usuario y devuelve 404 (no 403) para no revelar existencia cruzada entre empresas.
- Preparación directa para el Sprint 3 (Asistencia, Turnos, Nóminas).

### 3.3 Normalización de Finales de Línea (`.gitattributes`)
Para prevenir discrepancias en entornos heterogéneos de desarrollo (Windows vs Linux/CI), se crearon archivos `.gitattributes` en backend y frontend con `* text=auto eol=lf` y protecciones para binarios e imágenes (`.png`, `.pdf`, `.ico`).

---

## 4. Métricas de Calidad y Pruebas

Los comandos de verificación se ejecutan localmente (entorno Windows) y su salida textual se guarda como evidencia en `docs/evidencias/` sin editar:

### Backend (`backend_ssas_rrhh`)
```powershell
ruff check src tests
pytest -q                                        → docs/evidencias/pytest.txt
pytest --cov=src/ssas --cov-report=term-missing tests/ → docs/evidencias/cobertura.txt
```
- **Pruebas de extracción local (`test_extraccion_local.py`):** 17 pruebas, incluidas sinónimos.
- **Pruebas de fallback y análisis de CV (`test_analisis_cv_respaldo.py`):** 10 pruebas.
- **Flujo completo de punta a punta (`tests/integration/test_sprint2_selection.py::test_flujo_completo_cu13_a_cu19`):** recorre CU-13 → CU-19 en orden, con aislamiento entre empresas.

### Frontend (`frontend_ssas_rrhh`)
```powershell
npm run lint   → docs/evidencias/lint.txt
npm run build  → docs/evidencias/build.txt
npm test       → docs/evidencias/vitest.txt
npm run check:api → docs/evidencias/check-api.txt
```
- Nuevas suites Vitest agregadas:
  1. `src/features/portal/components/EntrevistaAgendada.test.tsx` (5 pruebas).
  2. `src/features/empleados/pages/EmpleadosPage.test.tsx` (4 pruebas).
  3. `src/features/empleados/components/EmpleadoDetalleModal.test.tsx` (2 pruebas).

> Regla del equipo: ninguna cifra ni ninguna ruta entra al informe sin estar respaldada por la salida de un comando o la lectura directa del código.

---

## 5. Exclusión Explícita de la Aplicación Móvil (DOC-04)

> [!NOTE]
> De conformidad con el alcance acordado para el Sprint 2 en el plan de trabajo (`DOC-04`), el repositorio/directorio `mobile_ssas_rrhh` (Flutter) **no ha sido modificado en este sprint**. Los casos de uso de reclutamiento, análisis de CVs con IA, gestión de candidatos, confirmación pública de entrevistas y administración de empleados corresponden al portal público y al panel web administrativo. El proyecto móvil permanece íntegro y servirá como base para los módulos de autoservicio del empleado y marcación de asistencia en sprints posteriores. El perfil `.docx` queda actualizado para declarar los CU-14 y CU-15 como web únicamente y marcar los diagramas NAV-2/NAV-3 móviles como diseño previsto.
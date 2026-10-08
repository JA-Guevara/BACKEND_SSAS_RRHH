# ADR 0007: Proveedor de Extracción Local de Respaldo para Análisis de CVs

- **Estado:** Aceptado
- **Fecha:** Octubre 2026
- **Contexto:** Sprint 2 (Módulo de Selección y Análisis de CVs)
- **Decisores:** Equipo de Arquitectura e Inteligencia Artificial (Grupo 12)

---

## 1. Contexto y Problema

El módulo de selección (`ssas.analisis_cv`) requiere analizar currículums vitae (CVs) en formatos PDF o texto para extraer información estructurada del candidato:
1. Habilidades técnicas y blandas detectadas.
2. Años estimados de experiencia laboral.
3. Nivel de educación alcanzado (Secundaria, Técnico, Licenciatura, Maestría, Doctorado).

Inicialmente, el caso de uso `AnalizarCVUseCase` dependía exclusivamente de la API de **Google Gemini** (`GeminiAnalysisProvider`). Durante pruebas de carga y escenarios con cuotas de API agotadas o latencias elevadas, se observaron los siguientes problemas:
- Errores HTTP 429 (Too Many Requests / cuota de Gemini agotada).
- Errores HTTP 502/503/504 en entornos sin conexión externa o con degradación del servicio del proveedor de IA.
- Bloqueo total del procesamiento de postulaciones, impidiendo que los reclutadores avancen en el pipeline de selección.

---

## 2. Decisión de Diseño

Se decidió implementar un **Proveedor de Extracción Local Determinista** (`ExtraccionLocalProvider`) como mecanismo de respaldo (*fallback*) y contingencia:

1. **Patrón Strategy & Fallback en Casos de Uso:**
   El caso de uso `AnalizarCVUseCase` orquesta los proveedores según la configuración `ia_proveedor_cv` en `Settings`:
   - `"auto"` (por defecto): Intenta primero `GeminiAnalysisProvider`. Si la API de Gemini falla por cuota (429), errores de gateway (502, 503, 504) o problemas de red, conmuta automáticamente a `ExtraccionLocalProvider`.
   - `"gemini"`: Fuerza el uso exclusivo de Gemini (genera error si la API no está disponible).
   - `"local"`: Fuerza el uso exclusivo de `ExtraccionLocalProvider`, garantizando ejecución 100% offline y deterministicidad en entornos de pruebas unitarias o CI/CD.

2. **Diseño de `ExtraccionLocalProvider`:**
   - **Catálogo de Habilidades:** Diccionario normalizado con sinónimos y variaciones para tecnologías comunes (Python, React, TypeScript, Docker, SQL, Git, FastAPI, AWS, etc.).
   - **Detección de Años de Experiencia:** Expresiones regulares que capturan patrones numéricos como `"3 años"`, `"5 anios"`, `"2 years"`, calculando el máximo reportado de forma segura.
   - **Detección de Educación:** Análisis léxico de grados académicos estándar (Doctorado > Maestría > Licenciatura > Técnico > Secundaria).
   - **Auditoría del Modelo:** El resultado reporta `modelo_usado: "local-rules-v1"`, permitiendo que el sistema y el usuario reconozcan qué motor procesó el análisis.

---

## 3. Consecuencias y Beneficios

### Positivas:
- **Resiliencia Operativa:** El flujo de selección y postulación nunca se interrumpe, garantizando alta disponibilidad del sistema.
- **Eficiencia en Costos:** En entornos de desarrollo, pruebas automatizadas y CI/CD, el modo `local` elimina el consumo de cuota de Gemini y el costo financiero.
- **Rendimiento:** La extracción local por expresiones regulares y catálogo léxico se ejecuta en milisegundos (< 10 ms frente a 1-3 segundos de latencia de red de LLM).
- **Trazabilidad:** Cada resultado de análisis audita el modelo exacto (`gemini-2.0-flash` o `local-rules-v1`), asegurando transparencia total.

### Negativas / Compensaciones:
- La extracción local se basa en patrones sintácticos predefinidos y no infiere contexto semántico complejo como un LLM moderno. Sin embargo, su precisión en palabras clave y experiencia es suficiente para habilitar la preselección inicial del postulante.

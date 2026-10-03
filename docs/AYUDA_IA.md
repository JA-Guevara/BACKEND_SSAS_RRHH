# Ayuda con IA, alcance controlado

La pregunta escrita por el usuario usa exclusivamente la FAQ local. El botón
"Explicar con IA" está unido a un artículo fijo del servidor y no acepta texto
libre; solo se envían el título y el contenido público de ese artículo. Los
permisos de la cuenta limitan los artículos disponibles.

Configuración opcional **solo en el backend**:

```ini
OPENAI_API_KEY=...
HELP_AI_ENABLED=true
HELP_AI_TIMEOUT_SECONDS=10
IA_MODEL=gpt-4o-mini
```

Sin clave, con la opción deshabilitada o si el proveedor falla, se muestra la
guía local. La clave no debe configurarse en Vite. No se guarda historial de
preguntas. Hay un límite de 10 consultas por minuto y usuario en cada proceso;
para varios workers se necesitaría un limitador compartido.

La solicitud usa Responses API con `store: false` y máximo 300 tokens de salida.
Esto no equivale por sí solo a retención cero del proveedor. No se envían CV,
empleados, candidatos, contraseñas, datos de empresa ni preguntas libres.

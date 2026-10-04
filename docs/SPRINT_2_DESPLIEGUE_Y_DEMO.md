# Sprint 2: configuración, despliegue y demostración

## Migración

La revisión `20260927_0006` continúa `20260915_0005`. Crea `entrevista`,
`evaluacion`, `analisis_cv`, `postulante_habilidad`, `empleado` y la relación de
contratación. Conserva los datos anteriores y asignaciones de roles personalizados.

Antes de publicar, comprobar un respaldo y probar la migración en una base de
pruebas. Desde el backend, con el entorno Python activo:

```powershell
$env:PYTHONPATH="src"
python -m alembic heads
python -m alembic current
python -m alembic upgrade head
```

En Railway mantener `alembic upgrade head` como pre-deploy, dentro del entorno
Python del servicio. El comando de inicio continúa levantando la API. Desplegar
backend antes que la web. No hacer downgrade en producción: eliminaría información
del Sprint 2. Si hay referencias previas inválidas a `empleado_id`, la migración
se detiene para que se resuelvan explícitamente.

## IA y archivos

Configurar únicamente en backend:

```ini
GEMINI_API_KEY=valor_privado_configurado_en_el_entorno
GEMINI_CV_MODEL=gemini-3.5-flash-lite
IA_TIMEOUT_SECONDS=60
IA_EXTRACTION_TIMEOUT_SECONDS=15
IA_MAX_CV_BYTES=5242880
IA_MAX_CV_TEXT_CHARS=60000
IA_MAX_OUTPUT_TOKENS=4000
CV_STORAGE_DIRECTORY=uploads/cv
```

El modelo es configurable. La llamada real usa Gemini Developer API con respuesta
estructurada. La clave no se incluye en Git, en las variables VITE ni en Postman.
Sin clave configurada, el análisis devuelve un error de configuración y conserva
el último resultado exitoso. No se reemplaza por una afinidad ficticia.

La afinidad combina 80% cobertura ponderada de habilidades acreditadas y 20%
experiencia relevante respecto al mínimo. El nivel declarado se conserva como
evidencia, pero esta versión no añade otra ponderación por nivel ni toma decisiones
automáticas de contratación/rechazo. El ranking permite ordenar separadamente por
IA, puntaje manual, promedio normalizado de evaluaciones o entrevistas. Un puntaje
ausente aparece como pendiente y se ordena al final.

Para que los CV persistan en Railway, conectar un volumen al backend con mount path
`/data`. El backend detecta `RAILWAY_VOLUME_MOUNT_PATH` y usa `/data/cv` tanto para
CV como para backup. Si se definieron `CV_STORAGE_DIRECTORY` o
`BACKUP_FILES_DIRECTORY`, quitarlas o fijar ambas a `/data/cv`; tienen prioridad
sobre el valor automático. Sin volumen, nuevas postulaciones con CV devuelven 503
en vez de guardar archivos efímeros. Migrar los archivos existentes al volumen
conservando sus nombres antes del cambio, si aún están disponibles. La base conserva
las referencias; no descargar archivos arbitrarios desde URLs del cliente.

Esta entrega registra evaluaciones sin archivos adjuntos. `archivo_url` permanece
en el esquema del diagrama, reservado para una futura carga/descarga protegida.
No se acepta una URL externa como adjunto confiable.

## Permisos

Los permisos nuevos se añaden por acciones de negocio, con equivalentes de
plataforma. Roles personalizados conservan sus asignaciones. Para empresas nuevas
se actualizó el aprovisionamiento; para las existentes, la migración amplía solo
roles de sistema.

Administrador de empresa y RRHH pueden contratar. Reclutador gestiona entrevistas,
evaluaciones y análisis, sin permiso automático de contratación. Jefe de área
puede consultar y registrar resultados/evaluaciones. Empleado no recibe acceso
general a selección. Plataforma requiere permiso explícito y empresa seleccionada.

Una evaluación registrada desde plataforma exige designar un evaluador autorizado
de la empresa; el actor de plataforma queda registrado en bitácora. La corrección
preserva al evaluador original. Las escrituras de empresa respetan la política de
suscripción operativa y el módulo de reclutamiento habilitado.

## Contratación

La contratación crea el empleado y actualiza la postulación/etapa dentro de una
misma transacción. No crea una cuenta de usuario. Si hay varios cupos, la vacante
continúa abierta hasta cubrirlos; al completar los cupos pasa a CERRADA. Repetir
la solicitud para la misma postulación y código devuelve el empleado existente.
Una persona ya empleada en esa empresa no se convierte de nuevo automáticamente.

## Comprobación de la demo

1. Usar una empresa de demostración y habilitar Reclutamiento.
2. Crear una vacante publicada con habilidades, pesos, experiencia y cupos.
3. Registrar al menos tres candidatos con CV PDF/DOCX que contengan texto.
4. Analizar y revisar evidencia, afinidad y habilidades faltantes.
5. Abrir el ranking, cambiar su orden y comparar entre dos y cuatro candidatos.
6. Programar una entrevista con un entrevistador autorizado; comprobar un
   conflicto horario y confirmar/reprogramar según corresponda.
7. Registrar resultados después de iniciada la entrevista y añadir evaluaciones
   con su escala de puntaje.
8. Incorporar un candidato al banco de talentos y asociarlo a otra vacante.
9. Contratar al finalista con un código único y verificar empleado, etapa,
   estado, cupos, historial y bitácora.
10. Cambiar a otra empresa y comprobar que los candidatos y archivos no se mezclan.

Las fechas se guardan con zona horaria y se muestran en la hora local del navegador.
Un PDF escaneado sin texto informa que requiere OCR; OCR no forma parte de esta
entrega. Los datos de demostración deben ser ficticios y cargarse únicamente en
una empresa elegida expresamente.

## Pruebas reproducibles

Ejecutar la suite unitaria y las pruebas del Sprint 2 contra una base PostgreSQL
local desechable, nunca mediante la URL de producción. Consultar el encabezado de
`tests/integration/test_sprint2_selection.py` para configurar su variable específica.
La prueba real de Gemini requiere además `RUN_CV_GEMINI_TEST=1`; puede realizar
una llamada facturable y se mantiene desactivada por defecto.

En frontend ejecutar build, lint, tests y comprobación del contrato OpenAPI
actualizado. Verificar health, docs, login y demo tras el despliegue autorizado.

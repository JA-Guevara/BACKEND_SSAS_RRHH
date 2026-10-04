# Analisis de CV: contrato y configuracion

`await analizar_cv(session, postulacion_id, empresa_id, actor_id, *, source_ip=None, user_agent=None) -> AnalisisCvModel`

Importar desde `ssas.analisis_cv.application.use_cases.analizar_cv`. Los IDs son UUID
como strings. El llamador aplica autenticacion, permiso scoped
`postulaciones:analizar_cv` y politica de modulo/suscripcion antes de invocar.
Guardar empresa y actor como valores simples antes de llamar: un rollback de lectura
expira objetos ORM cargados por autenticacion. El caso de uso comprueba actor activo
y pertenencia de vacante, postulante y habilidades a la empresa.

La sesion debe estar ligada a un AsyncEngine PostgreSQL y no contener escrituras.
Una transaccion previa exclusivamente de lectura se libera con rollback tras validar
el alcance. Ademas de new/dirty/deleted, se verifica `txid_current_if_assigned()` para
rechazar escrituras ya flushed. No se realiza commit dentro del caso de uso.
La dependencia HTTP conserva su commit/rollback habitual.

## Variables de entorno

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| GEMINI_API_KEY | sin configurar | Secreto backend compartido con reportes; ausencia devuelve 503 |
| GEMINI_CV_MODEL | gemini-3.5-flash-lite | Modelo Gemini para analisis de CV; independiente del de reportes |
| IA_TIMEOUT_SECONDS | 60 | Tiempo total maximo para Gemini, entre 0 y 300 |
| IA_MAX_CV_BYTES | 5242880 | Limite de archivo PDF/DOCX, maximo configurable 20 MiB |
| IA_MAX_CV_TEXT_CHARS | 60000 | Limite de texto; se rechaza exceso, no se trunca |
| IA_EXTRACTION_TIMEOUT_SECONDS | 15 | Tiempo maximo de parser en proceso independiente |
| IA_MAX_OUTPUT_TOKENS | 4000 | Limite de salida Gemini |
| IA_MAX_CONCURRENT_ANALYSES | 2 | Cupos globales PostgreSQL compartidos entre procesos |
| CV_STORAGE_DIRECTORY | `RAILWAY_VOLUME_MOUNT_PATH/cv` en Railway con volumen; `uploads/cv` local | Directorio compartido de carga, descarga y extraccion |

Ejemplo sin secretos: `GEMINI_CV_MODEL=gemini-3.5-flash-lite`, `CV_STORAGE_DIRECTORY=/data/cv`.
Configurar GEMINI_API_KEY directamente en las variables del backend; nunca en frontend.
OPENAI_API_KEY e IA_MODEL siguen siendo opciones de la ayuda generativa, pero el
analisis de CV ya no las utiliza.
En Railway, conectar un volumen al servicio backend con mount path `/data`. El backend
usara automaticamente `/data/cv` para nuevas cargas y para el backup, sin agregar
variables. Si ya existen `CV_STORAGE_DIRECTORY` o `BACKUP_FILES_DIRECTORY` en Railway,
quitarlas o configurarlas ambas como `/data/cv`; una variable explicita tiene prioridad.
El backend devuelve 503 y no crea la postulacion si se intenta subir un CV sin volumen
o con un directorio fuera de este. Los CV de contenedores anteriores no se trasladan
solos: copiarlos al volumen conservando sus nombres, si aun estan disponibles.
El resolver reutiliza el nombre de archivo guardado
y verifica que el archivo real no salga del directorio (incluidos enlaces simbolicos).
Ademas se verifica que su nombre corresponda a un codigo_seguimiento de una
postulacion del mismo postulante y empresa. Un cv_url a otro archivo del directorio
compartido se rechaza antes de extraer o enviar al proveedor.
No se crean ni despliegan volumenes automaticamente desde el repositorio.

## Extraccion y proveedor

PDF usa pypdf y DOCX usa python-docx (incluye texto en tablas). Se limita PDF a 200
paginas y DOCX expandido a cuatro veces IA_MAX_CV_BYTES. El parser corre en un proceso
independiente con timeout que termina el proceso, compatible con Windows y Linux.
PDF sin texto requiere OCR; OCR no esta implementado. Documentos corruptos/protegidos,
tamano excesivo y formatos no aceptados producen errores comprensibles.

El proveedor usa httpx asincrono contra Gemini Developer API `generateContent`
con respuesta JSON estructurada, siguiendo la
[documentacion oficial de Gemini](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).
No hay fallback que simule IA. Se manejan timeout (504), rechazo/salida invalida (502),
HTTP externo o credenciales ausentes (503). No se incluye el cuerpo del error externo
en errores/logs. Los puertos permiten sustituir extractor/proveedor para pruebas.

Se omiten datos personales conocidos del postulante, emails, URLs y campos personales
etiquetados del texto. Esto reduce datos enviados; no equivale a anonimizacion completa
de texto libre. Se envian CV depurado, requisitos laborales y catalogo de habilidades
de la empresa. El prompt trata documentos como datos no confiables y prohibe basar
el resultado en atributos sensibles. La salida debe citar evidencia literal del CV,
usar IDs del catalogo sin duplicados y experiencia finita entre 0 y 80 anos.

## Formula y persistencia

`afinidad = 80 * cobertura_ponderada + 20 * min(experiencia / experiencia_min, 1)`.
Cobertura es suma de pesos de habilidades requeridas con evidencia / suma de pesos.
Sin habilidades requeridas, cobertura vale 1; sin experiencia minima, el factor de
experiencia vale 1. Se redondea a dos decimales (Decimal, half-even). La cobertura
acredita presencia de habilidad, no equivalencia de nivel; el nivel y obligatoriedad
se conservan para revision humana. No se usan atributos personales ni puntaje manual.

Se persisten analisis, puntaje_ia, union de habilidades y bitacora en un savepoint del
request. Ningun fallo externo reemplaza el ultimo resultado exitoso. Una habilidad
existente (manual o IA) se conserva con ON CONFLICT DO NOTHING; nuevos pares se insertan
con detectado_por_ia=true. Nunca se eliminan habilidades detectadas en otra vacante.
No se adjudica experiencia laboral total a cada habilidad: los nuevos pares usan 0
cuando no se ha extraido experiencia especifica de esa habilidad.

La justificacion se guarda en observaciones; las citas de habilidades en fortalezas.
habilidades_detectadas y habilidades_faltantes contienen listas de nombres, alineadas
con el contrato HTTP y frontend. Evidencia completa se conserva en fortalezas y
observaciones; experiencia es decimal (Numeric 5,2), no se convierte a entero.
Antes de persistir se vuelve a validar el alcance, actor y snapshot de CV/vacante/catalogo.
Si cambian, se devuelve 409 y se requiere reanalizar.

## Concurrencia y transacciones

Un advisory session-level determinista por postulacion se mantiene en una conexion
dedicada AUTOCOMMIT durante extraccion/proveedor; no hay transaccion ni row locks
abiertos en PostgreSQL durante la llamada externa. Se libera en finally y se invalida
la conexion si falla el desbloqueo. PostgreSQL libera el lock al cerrar la conexion
tras caida del proceso. Requiere conexion directa o pooler en session mode, no PgBouncer
transaction pooling. La conexion usa NullPool independiente, por lo que no ocupa
conexiones del pool principal. La transaccion de autenticacion/lectura se libera antes
de adquirir el bloqueo. Advisory locks de cupo global limitan ejecuciones simultaneas
entre workers; el limite efectivo es el menor entre IA_MAX_CONCURRENT_ANALYSES y
max(1, DB_POOL_SIZE + DB_MAX_OVERFLOW - 2). Al agotarse los cupos se devuelve 503 sin
esperar conexiones del pool. Usar el mismo limite en todos los workers.

Antes de empezar se comprueba otro advisory de persistencia. Al guardar, la sesion del
request adquiere ese segundo lock a nivel transaccional y lo conserva hasta el commit
o rollback del llamador. Esta transferencia impide analizar otra vez entre retorno
de la funcion y commit HTTP. Duplicados devuelven 409, incluso entre procesos.
La persistencia toma row locks explicitamente en orden vacante, postulación, postulante,
alineado con contratacion; nunca se confia en el orden de un FOR UPDATE con joins.

## Verificacion

`pytest tests/unit/test_analisis_cv.py` cubre extraccion real de documentos sinteticos,
limites, proveedor con MockTransport, validacion de evidencia, formula, locks y contrato
sin commit. `pytest tests/integration/test_analisis_cv_external.py` habilita pruebas
reales solo con `RUN_CV_GEMINI_TEST=1` / `CV_LOCK_TEST_DATABASE_URL` configurados.
`pytest tests/integration/test_analisis_cv_postgresql.py` con SPRINT2_TEST_DATABASE_URL
usa exclusivamente loopback:55432/sprint2 sin password, crea un schema propio y lo
elimina al terminar. Verifica guardado decimal/contrato, bloqueo concurrente, ausencia
de transacciones externas, auditoria unica, rollback, snapshots y propiedad de archivos.
La prueba Gemini usa texto sintetico sin datos personales y consume una llamada.
Los mocks no sustituyen esa prueba real para cerrar CU-13. Revision humana es necesaria
antes de decisiones de contratacion/rechazo.

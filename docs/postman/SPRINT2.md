# Sprint2: integracion y demo local

Todos los comandos se ejecutan desde el backend. No cargar `.env`. Esta suite y
la demo aceptan exclusivamente PostgreSQL desechable en `localhost` o
`127.0.0.1`, puerto `55432`, base/usuario `sprint2`, sin password ni opciones URL.
La variable de opt-in debe estar presente; cualquier otro destino produce skip
en pytest y rechazo en la demo antes de importar la configuracion del backend.

## Pruebas

PowerShell, usando Python 3.12 incluido (el launcher de `.venv` puede estar roto):

```powershell
$py = 'C:\Users\JORDI\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONPATH = 'src;.venv/Lib/site-packages'
$env:SPRINT2_TEST_DATABASE_URL = 'postgresql+psycopg://sprint2@127.0.0.1:55432/sprint2'
$env:SETTINGS_ENV_FILE = Join-Path $PWD '.sprint2-env-does-not-exist'
$env:APP_ENV = 'development'
$env:APP_SECRET_KEY = 'test'
$env:APP_AUDIT_ENCRYPTION_KEY = '11' * 32
$env:DATABASE_URL = $env:SPRINT2_TEST_DATABASE_URL
& $py -m alembic upgrade head
& $py -m pytest -c pyproject.toml tests/integration/test_sprint2_selection.py -q
```

La revision `20260927_0006` es obligatoria. Las pruebas reflejan las tablas
migradas a un esquema SQL temporal, con tipos, constraints e indices; no crean
el esquema deseado a partir del ORM. Se usan commits y conexiones independientes
para comprobar los bloqueos reales. El esquema temporal se elimina al finalizar;
los datos publicos de demo y los de otros agentes quedan intactos.

Las rutas de seleccion se montan en una app FastAPI minima con el mismo router
y handler de `SeleccionError`. Solo se sustituye la identidad autenticada y la
sesion SQL; permisos, roles, modulos, suscripciones, repositorios, auditoria,
validacion y serializacion se ejecutan realmente. La suite no valida middleware
JWT del app completo ni llama al proveedor IA. Los analisis CV son fixtures SQL.

Cobertura: aislamiento de dos empresas; revocacion de modulo; agenda persistida;
colision y limites contiguos; confirmacion/cancelacion/resultado; modalidad
telefonica y zonas horarias; responsables; evaluaciones y evaluador original;
rollback de contratacion y fallo de auditoria; idempotencia; carrera por cupo;
carrera idempotente de la misma postulacion; carrera de entrevistas; ranking,
comparacion y ultimo analisis; historial; ocultamiento de evaluaciones,
entrevistas y puntajes derivados para un rol de solo lectura.

## Demo persistente para navegador

La demo usa el esquema publico. Requiere los catalogos de permisos, modulos y
planes existentes y provisionamiento del proyecto. No configura ni llama a
correo, Stripe u OpenAI. No genera usuarios con hashes ficticios ni claves fijas.

```powershell
# Variables de conexion/configuracion: iguales al bloque anterior.
# Inspeccion sin escritura:
& $py scripts/cargar_sprint2_demo.py --empresa-slug sprint2-demo-ui

# Solo al crear una empresa: proporcionar estos valores desde el entorno.
$env:SPRINT2_DEMO_ADMIN_USERNAME = 'sprint2admin'
$env:SPRINT2_DEMO_ADMIN_EMAIL = 'sprint2-demo@example.com'
$env:SPRINT2_DEMO_ADMIN_PASSWORD = [guid]::NewGuid().ToString('N') + 'Q7!z'
& $py scripts/cargar_sprint2_demo.py --empresa-slug sprint2-demo-ui --create-empresa --apply --confirm-empresa-slug sprint2-demo-ui --session-file tmp/sprint2-demo-session.json

# Reejecucion idempotente de una empresa existente; no cambia su clave:
& $py scripts/cargar_sprint2_demo.py --empresa-slug sprint2-demo-ui --apply --confirm-empresa-slug sprint2-demo-ui
```

ProvisionEmpresa valida la politica estricta de password y crea administrador,
roles, etapas y suscripcion. El script usa un lock asesor para serializar cargas.
Las claves estables son el slug, titulos/nombres con prefijo `[SPRINT2 DEMO]` y
CI `SPRINT2-DEMO-*`; las reejecuciones conservan IDs y no reinician entrevistas
ni contrataciones. No se crea empresa sin `--create-empresa`; no se escribe sin
`--apply` y confirmacion literal del slug. Los usuarios existentes deben tener
capacidades de seleccion y una suscripcion operativa; la demo no cambia permisos.

El archivo temporal opcional contiene IDs y JWT firmado con la clave local
`test`; al provisionar tambien contiene las credenciales de login locales.
No imprimirlo ni versionarlo. El token expira segun el TTL de la aplicacion;
para renovarlo repetir la demo con `--session-file`, sin `--create-empresa`.
La salida de consola solo contiene IDs. Se crean tres PDF ficticios validos con
ReportLab usando `LocalCvStorage.save_cv` y el codigo unico de cada postulacion;
se verifica `owns_cv` antes del commit. El catalogo tiene Python, SQL y REST APIs,
requisitos ponderados y habilidades de cada candidato. Los puntajes y analisis
persistidos estan identificados como sinteticos; la carga no llama a IA.

Para el servidor local del navegador, usar exactamente el bloque de configuracion
anterior y la misma base/clave `test`, luego:

```powershell
& $py -m uvicorn ssas.main:app --host 127.0.0.1 --port 8012
```

Login real: `POST /api/v1/auth/login` con `empresa_slug`, `username` y `password`
del archivo temporal. Usar la ruta habitual del proyecto para recuperar el
perfil/permisos despues del login. Nunca reutilizar estas credenciales o JWT en
otro entorno.

## Postman

Importar `sprint2_seleccion.postman_collection.json` y
`sprint2_local.postman_environment.json`. Las exportaciones no incluyen tokens
ni passwords. Guardar `access_token` como valor local secreto de Postman y evitar
exportarlo. `base_url` debe apuntar al backend local configurado arriba.

Mapear el manifiesto de demo: `vacante_id`; primera y segunda entrada de
`postulacion_ids` a `postulacion_id` y `postulacion_2_id`; primera entrada de
`postulante_ids` a `postulante_id`; `user_id` a `entrevistador_id`. Completar
`fecha_entrevista` con una fecha futura ISO 8601 y zona horaria, `fecha_ingreso`
con `YYYY-MM-DD` y `codigo_empleado` con un codigo unico de demo.

Seleccionar peticiones individualmente. Las escrituras y la comparacion POST
requieren `allow_writes=true`. La coleccion rechaza cualquier URL no local.
Programar crea `entrevista_id`; evaluar crea `evaluacion_id`; contratar crea
`empleado_id`. Los scripts guardan IDs en variables de coleccion; el entorno
no define esas variables de salida para evitar ocultarlas con valores vacios.
El resultado de entrevista exige que su fecha ya haya comenzado; no ejecutar
todo el runner seguido esperando 200 para ese paso. Contratar consume un cupo;
reintentar con el mismo codigo devuelve el mismo empleado. Cambiar el codigo
para esa postulacion devuelve 409. La demo tiene dos cupos y tres candidatos.

Respuestas negativas esperadas: 401 sin JWT; 403 sin permiso o alcance;
404 para recursos ajenos; 409 por cruces de agenda/cupo/estado; 422 por fechas
sin zona, enlace virtual no HTTPS, puntaje superior al maximo o comparacion
invalida. Ordenar por entrevistas/evaluaciones sin su permiso produce 403;
ranking/comparacion ocultan esos registros y puntajes; historial los filtra.

El POST de analisis CV externo se omite deliberadamente de esta coleccion.
GET consulta los analisis sinteticos ya persistidos y no consume proveedor.

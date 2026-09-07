# Instrucciones para ejecutar el backlog con múltiples agentes

Proyecto: `backend_ssas_rrhh` · commit base `782ac60` · 31 tareas en `docs/03_BACKLOG_IMPLEMENTACION.md`

---

## 1. Los tres cuellos de botella que hay que respetar

Antes de repartir tareas, estos tres puntos son los que hacen fracasar el trabajo en paralelo
en **este** proyecto concreto. No son teoría.

### 1.1 Una sola base de datos compartida

Local, Railway y las pruebas apuntan **a la misma base de Supabase**. Si dos agentes corren
`alembic upgrade`, un seed o `pytest` al mismo tiempo, se pisan entre ellos y sobre producción.

> **Regla:** hasta que `INFRA-001` esté cerrada, **un solo agente por vez puede tocar la base.**
> Los demás trabajan en código que no requiere base (repositorios, casos de uso, schemas) y
> corren únicamente `pytest tests/unit`.

### 1.2 Las migraciones de Alembic no se paralelizan

Dos agentes que crean una revisión con el mismo `down_revision` generan un historial
ramificado, y `alembic upgrade head` falla con *multiple heads*. Cuesta más desenredarlo que
lo que se ganó paralelizando.

> **Regla:** **un solo agente a la vez crea migraciones.** Hoy las necesitan `VAC-004`,
> `TAB-001` y `MIG-001`: van en serie, nunca simultáneas. El que la crea avisa el nuevo
> `revision` antes de que el siguiente empiece.

### 1.3 Los tres documentos son archivos compartidos

Todos los agentes terminan editando `docs/02` y `docs/03`.

> **Regla:** cada agente modifica **solo** el bloque de su tarea y **su** fila en la matriz.
> Nunca reformatea, reordena ni reindenta el archivo completo. Los IDs son inmutables.

---

## 2. Orden de ejecución

### Ola 0 — en serie, bloquea a todo lo demás

| Tarea | Por qué va primero |
|---|---|
| `INFRA-001` | Sin base de pruebas separada, ningún agente puede correr la suite completa sin arriesgar producción. Desbloquea `TEST-001`, `TEST-002`, `TEST-003`. |
| `BUG-001` | Fallo de aislamiento entre empresas documentado como FALLA. **Ver la advertencia de §4.** |

### Ola 1 — en paralelo, sin dependencias

| Agente | Tarea | Toca migraciones |
|---|---|---|
| A | `VAC-001` Repositorio de vacantes | no |
| B | `TAB-001` Catálogos de etapas y motivos | **sí** |
| C | `HAB-001` Capa de aplicación de habilidades | no |
| D | `PERF-001` Alinear el perfil con el código | no |

`VAC-004` (permisos) y `MIG-001` (renombrar migraciones) esperan a que B libere las migraciones.

### Ola 2 — en serie sobre vacantes

```
VAC-001 ──▶ VAC-002 ──┐
VAC-004 ──────────────┴──▶ VAC-003
```

### Ola 3 — en paralelo, una vez que existe la API de vacantes

| Agente | Tarea |
|---|---|
| A | `POR-001` Portal público |
| B | `TAB-002` Tablero de candidatos |
| C | `PTE-001` → `PTE-003` Banco de talentos |
| D | `TEST-002` / `TEST-003` (si `INFRA-001` está cerrada) |

### Ola 4

`TAB-003` (mover de etapa y rechazar) depende de `TAB-002`.
`NOT-001` sigue **BLOQUEADO**: no asignarla.

---

## 3. Prompt por agente

Pegar esto a cada agente, reemplazando `<TASK-ID>`.

```text
Vas a implementar una única tarea del backlog del proyecto backend_ssas_rrhh.

TAREA ASIGNADA: <TASK-ID>

ANTES DE ESCRIBIR CÓDIGO
1. git fetch origin && git log --oneline -3
   Confirmá que trabajás sobre el HEAD actual. Este repositorio avanza rápido.
2. git switch -c feat/<TASK-ID>-descripcion-corta
   Una tarea, una rama. Nunca trabajes sobre main.
3. Leé docs/01_ESTADO_PROYECTO.md completo.
4. Leé la ficha de <TASK-ID> en docs/03_BACKLOG_IMPLEMENTACION.md.
5. Leé los endpoints que la ficha referencia en docs/02_API_ENDPOINTS.md.
6. Revisá SOLO el módulo afectado y sus dependencias directas.
   No recorras todo el repositorio.

INVARIANTES QUE NO PODÉS ROMPER
- El tenant es implícito en el token. Nunca va en la URL.
    usuario.empresa_id  IS NULL -> administrador de plataforma
    rol.empresa_id      IS NULL -> rol global
    bitacora.empresa_id IS NULL -> evento de plataforma
- Todo recurso de empresa se filtra por empresa_id EN EL REPOSITORIO, no en el router.
  Un router puede olvidarse del filtro; el repositorio no debe permitirlo.
- Un recurso de otra empresa se responde 404, nunca 403. Un 403 confirmaría que existe.
- Ningún rol de empresa recibe permisos platform:*.
- La lógica de negocio no vive en los routers.
- Entidad de dominio != modelo ORM. Adaptadores: SqlAlchemy<Cosa>Repository.
- Nombres de negocio en español; capas técnicas en inglés.

BASE DE DATOS
- Verificá a qué apunta DATABASE_URL antes de CUALQUIER comando que escriba.
  Local, Railway y las pruebas comparten la misma base de Supabase.
- Si tu tarea NO crea migraciones, corré solo: pytest tests/unit
- Si tu tarea SÍ crea una migración, pedí autorización antes: solo un agente por vez.
- Nunca quites el freno de host local de las pruebas e2e: hacen TRUNCATE.

ALCANCE
- Implementá SOLO lo que dice la ficha. Nada más.
- No refactorices código ajeno, no renombres, no "limpies".
- No cambies la arquitectura ni agregues capas.
- Si la ficha dice DECISIÓN PENDIENTE: NO decidas por tu cuenta.
  Marcá la tarea BLOQUEADO, escribí qué falta decidir, y detenete.

AL TERMINAR — los cinco pasos, en orden
1. pytest
2. ruff check src tests
3. python scripts/verificar_documentacion.py
4. Actualizá docs/02_API_ENDPOINTS.md: estado del endpoint y su ficha.
5. Actualizá docs/03_BACKLOG_IMPLEMENTACION.md: estado, archivos modificados,
   resultado, fecha y tu identificador.
   Si cambió el estado de un área, actualizá también docs/01_ESTADO_PROYECTO.md.

Editá ÚNICAMENTE el bloque de tu tarea y tu fila en la matriz.
No reformatees los archivos completos: otros agentes están editando los mismos.

ENTREGA
Un commit por tarea, con el ID en el mensaje:
   feat(vacantes): implementar repositorio de vacantes [VAC-001]
No hagas merge a main. No hagas push --force. Dejá la rama para revisión.
```

---

## 4. Advertencia sobre `BUG-001`

La ficha dice que `CP-S1-21` está marcado FALLA: un usuario de la empresa B accede al tablero
de la empresa A sin recibir 404. **Pero el endpoint del tablero no existe en el backend** —
solo hay dos rutas públicas de postulaciones.

Instrucción para el agente que la tome:

1. Intentá reproducirlo. Si la ruta no existe en el backend, **no inventes dónde está el fallo**.
2. Averiguá dónde se corrió esa prueba: probablemente en el frontend o en una rama sin fusionar.
3. Si el backend no tiene el endpoint, convertí la tarea en un requisito de `TAB-002`:
   el tablero nace con el test de aislamiento en verde desde el primer commit.
4. Registrá en la ficha qué encontraste. Cambiá el estado a `BLOQUEADO` si el fallo vive
   fuera de este repositorio.

Un agente sin esta advertencia va a dar vueltas buscando código que no existe.

---

## 5. Definición de terminado

Una tarea no está terminada hasta que las seis cosas son ciertas:

- [ ] `pytest` en verde
- [ ] `ruff check src tests` sin errores
- [ ] `python scripts/verificar_documentacion.py` sin fallos
- [ ] Los criterios de aceptación de la ficha están todos marcados y son verificables
- [ ] Si el endpoint es de empresa: **existe un test que falla si alguien quita el filtro por `empresa_id`**
- [ ] Los tres documentos reflejan el estado real

El quinto punto es el que más se saltea y el que evalúa la materia.

---

## 6. Cuándo un agente debe detenerse

Detenerse y reportar, en vez de improvisar:

| Situación | Qué hacer |
|---|---|
| La ficha dice `DECISIÓN PENDIENTE` | Marcar `BLOQUEADO`, escribir qué hay que decidir, parar |
| Haría falta cambiar la arquitectura | Parar. No se cambia sin autorización |
| El contrato del endpoint no coincide con `docs/02` | Parar. O el documento está mal o la tarea está mal entendida |
| Hay que crear una migración y otro agente ya está creando una | Esperar turno |
| `verificar_documentacion.py` falla por algo ajeno a la tarea | Reportarlo, no arreglarlo por cuenta propia |
| Un test ajeno se rompe | Parar. Probablemente rompiste algo que no era tuyo |

---

## 7. Lo que ningún agente debe hacer

- Correr `alembic upgrade`, seeds o `pytest tests/e2e` contra la base de producción
- Quitar el freno de host local de las pruebas e2e
- `DROP SCHEMA` en Supabase (destruye `auth`, `storage`, `realtime`)
- `git push --force`, merge a `main`, o reescribir historial
- Renumerar IDs de tareas o endpoints
- Reformatear archivos completos con `ruff format` sobre módulos ajenos
- Marcar `IMPLEMENTADO` algo que no fue probado
- Editar la ficha de otra tarea

"""Opt-in PostgreSQL integration: never read the application's production .env."""

import asyncio
import os
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

TARGET = os.environ.get("SPRINT2_TEST_DATABASE_URL", "")
if not TARGET:
    pytest.skip(
        "Set SPRINT2_TEST_DATABASE_URL to the disposable local Sprint2 DB", allow_module_level=True
    )
try:
    url = make_url(TARGET)
    safe = (
        url.drivername == "postgresql+psycopg"
        and url.host in {"localhost", "127.0.0.1"}
        and url.port == 55432
        and url.database == "sprint2"
        and url.username == "sprint2"
        and not url.password
        and not url.query
    )
except (ArgumentError, TypeError, ValueError):
    safe = False
if not safe:
    pytest.skip(
        "Sprint2 integration only permits loopback:55432/sprint2, user sprint2, no password/options",
        allow_module_level=True,
    )

os.environ.update(
    SETTINGS_ENV_FILE=str(Path(__file__).with_name(".sprint2-env-does-not-exist")),
    APP_ENV="development",
    APP_SECRET_KEY="test",
    DATABASE_URL=TARGET,
    APP_AUDIT_ENCRYPTION_KEY="11" * 32,
)
os.environ.pop("OPENAI_API_KEY", None)

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import MetaData, delete, func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from ssas.infrastructure.database.base import import_all_models

import_all_models()
from ssas.analisis_cv.infrastructure.persistence.models.analisis_cv import AnalisisCvModel
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.bitacora.infrastructure.persistence.models.audit_log import AuditLogModel
from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.config.settings import settings
from ssas.core.security.dependencies import CurrentUser, get_current_user
from ssas.departamentos.infrastructure.persistence.models.departamento import DepartamentoModel
from ssas.empleados.infrastructure.http.router import router as empleados_router
from ssas.empleados.infrastructure.persistence.models.empleado import EmpleadoModel
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.empresas.infrastructure.persistence.models.suscripcion import (
    PlanSuscripcionModel,
    SuscripcionModel,
)
from ssas.entrevistas.infrastructure.persistence.models.entrevista import EntrevistaModel
from ssas.evaluaciones.infrastructure.persistence.models.evaluacion import EvaluacionModel
from ssas.habilidades.infrastructure.persistence.models.habilidad import HabilidadModel
from ssas.infrastructure.database.session import get_session
from ssas.modulos.infrastructure.persistence.models.empresa_modulo import EmpresaModuloModel
from ssas.modulos.infrastructure.persistence.models.modulo import ModuloModel
from ssas.postulaciones.application.use_cases.gestionar_seleccion import GestionarSeleccion
from ssas.postulaciones.domain.seleccion import SeleccionError
from ssas.postulaciones.infrastructure.http.entrevista_publica_router import (
    router as entrevista_publica_router,
)
from ssas.postulaciones.infrastructure.http.seleccion_router import router
from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
    EtapaReclutamientoModel,
)
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulaciones.infrastructure.persistence.repositories.seleccion_repository import (
    SeleccionRepository,
)
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
from ssas.roles.infrastructure.persistence.models.permission import PermissionModel
from ssas.roles.infrastructure.persistence.models.role import RoleModel
from ssas.roles.infrastructure.persistence.models.role_permission import rol_permiso_table
from ssas.roles.infrastructure.persistence.models.user_role import usuario_rol_table
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel
from ssas.vacantes.infrastructure.persistence.models.vacante_habilidad import (
    VacanteHabilidadModel,
)


def uid():
    return str(uuid4())


def test_migrated_nullable_evaluation_observations_are_readable(database):
    async def body(factory, c, ts, *rest):
        t = ts[0]
        async with factory() as s:
            s.add(
                EvaluacionModel(
                    id=uid(),
                    postulacion_id=t["posts"][0],
                    evaluador_id=t["user"],
                    tipo="TECNICA",
                    nombre="Legacy nullable observation",
                    puntaje=8,
                    puntaje_maximo=10,
                    aprobado=True,
                    observaciones=None,
                )
            )
            await s.commit()
        for path in (
            f"postulaciones/{t['posts'][0]}/evaluaciones",
            f"vacantes/{t['vacante']}/ranking",
        ):
            response = await c.get(path)
            assert response.status_code == 200, response.text
        response = await c.post(
            f"vacantes/{t['vacante']}/comparar", json={"postulacion_ids": t["posts"][:2]}
        )
        assert response.status_code == 200, response.text

    asyncio.run(scenario(database, body))


@pytest.fixture(scope="module")
def database():
    # Reflect migrated SQL, rather than creating the current ORM's preferred schema.
    # Separate schema permits real commits/concurrency without touching other agents' rows.
    schema = "sprint2_it_" + uuid4().hex

    async def setup():
        engine = create_async_engine(TARGET, poolclass=NullPool)
        async with engine.begin() as conn:
            versions = (
                (await conn.execute(text("SELECT version_num FROM alembic_version")))
                .scalars()
                .all()
            )
            assert "20261005_0009" in versions, "Migrate disposable DB to Sprint2 head first"
            metadata = MetaData()
            await conn.run_sync(lambda sync: metadata.reflect(sync))
            metadata.remove(metadata.tables["alembic_version"])
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            await conn.execute(text(f'SET LOCAL search_path TO "{schema}", public'))
            await conn.run_sync(lambda sync: metadata.create_all(sync, checkfirst=False))
        await engine.dispose()

    asyncio.run(setup())
    yield schema

    async def cleanup():
        engine = create_async_engine(TARGET, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await engine.dispose()

    asyncio.run(cleanup())


async def scenario(schema, body):
    engine = create_async_engine(
        TARGET,
        poolclass=NullPool,
        connect_args={
            "options": f"-csearch_path={schema},public -clock_timeout=5000 -cstatement_timeout=15000",
            "application_name": schema,
        },
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as s:
            module = await s.scalar(select(ModuloModel).where(ModuloModel.codigo == "SPRINT2_IT"))
            if module is None:
                module = ModuloModel(id=uid(), codigo="SPRINT2_IT", nombre="Integration selection")
                s.add(module)
                await s.flush()
            permissions = []
            for code in (
                "entrevistas:ver",
                "entrevistas:gestionar",
                "entrevistas:registrar_resultado",
                "evaluaciones:ver",
                "evaluaciones:gestionar",
                "postulaciones:ver",
                "postulaciones:analizar_cv",
                "postulaciones:contratar",
                "empleados:ver",
                "postulantes:gestionar",
            ):
                p = await s.scalar(select(PermissionModel).where(PermissionModel.name == code))
                if p is None:
                    resource, action = code.split(":")
                    p = PermissionModel(
                        id=uid(), name=code, modulo=module.codigo, resource=resource, action=action
                    )
                    s.add(p)
                    await s.flush()
                permissions.append(p)
            plan = PlanSuscripcionModel(id=uid(), nombre=uid(), precio_mensual=0, max_empleados=100)
            s.add(plan)
            await s.flush()
            tenants = []
            for index in range(2):
                e = EmpresaModel(
                    id=uid(),
                    slug="it-" + uuid4().hex,
                    razon_social="Synthetic",
                    nombre_comercial="Synthetic",
                )
                s.add(e)
                await s.flush()
                user = UserModel(
                    id=uid(),
                    empresa_id=e.id,
                    name="Tester",
                    apellido=str(index),
                    email="test@example.invalid",
                    username="tester",
                    hashed_password="!disabled-integration-login",
                    email_verified=True,
                )
                role = RoleModel(id=uid(), empresa_id=e.id, name="Selection", codigo="IT")
                dep = DepartamentoModel(id=uid(), empresa_id=e.id, nombre="Engineering")
                initial = EtapaReclutamientoModel(
                    id=uid(), empresa_id=e.id, nombre="Initial", orden=1, es_inicial=True
                )
                hired = EtapaReclutamientoModel(
                    id=uid(), empresa_id=e.id, nombre="Hired", orden=2, es_contratado=True
                )
                s.add_all(
                    [
                        user,
                        role,
                        dep,
                        initial,
                        hired,
                        EmpresaModuloModel(empresa_id=e.id, modulo_id=module.id),
                        SuscripcionModel(
                            id=uid(), empresa_id=e.id, plan_id=plan.id, estado="ACTIVA"
                        ),
                    ]
                )
                await s.flush()
                await s.execute(
                    usuario_rol_table.insert().values(usuario_id=user.id, rol_id=role.id)
                )
                await s.execute(
                    rol_permiso_table.insert(),
                    [{"rol_id": role.id, "permiso_id": p.id} for p in permissions],
                )
                cargo = CargoModel(
                    id=uid(), empresa_id=e.id, departamento_id=dep.id, nombre="Developer"
                )
                s.add(cargo)
                await s.flush()
                vacancy = VacanteModel(
                    id=uid(),
                    empresa_id=e.id,
                    cargo_id=cargo.id,
                    departamento_id=dep.id,
                    responsable_id=user.id,
                    titulo="Integration vacancy",
                    descripcion="Synthetic only",
                    modalidad="REMOTO",
                    estado="PUBLICADA",
                    cantidad_vacantes=1,
                )
                s.add(vacancy)
                await s.flush()
                posts = []
                for n in range(3):
                    candidate = PostulanteModel(
                        id=uid(),
                        empresa_id=e.id,
                        nombres=f"Candidate {n}",
                        apellidos="Synthetic",
                        ci=f"IT{index}{n}",
                        email=f"candidate{n}@example.invalid",
                        telefono="00000000",
                        ciudad="La Paz",
                        nivel_educativo="LICENCIATURA",
                        fuente="OTRO",
                        anios_experiencia=n,
                    )
                    s.add(candidate)
                    await s.flush()
                    post = PostulacionModel(
                        id=uid(),
                        vacante_id=vacancy.id,
                        postulante_id=candidate.id,
                        etapa_id=initial.id,
                        estado="ACTIVA",
                        codigo_seguimiento=uid(),
                        puntaje_ia=[90, 50, None][n],
                        puntaje_manual=[20, 80, None][n],
                    )
                    s.add(post)
                    posts.append(post.id)
                tenants.append(
                    {
                        "empresa": e.id,
                        "user": user.id,
                        "role": role.id,
                        "vacante": vacancy.id,
                        "posts": posts,
                        "hired": hired.id,
                    }
                )
            await s.commit()
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        app.include_router(empleados_router, prefix="/api/v1")
        app.include_router(entrevista_publica_router, prefix="/api/v1")

        @app.exception_handler(SeleccionError)
        async def selection_error(request: Request, exc: SeleccionError):
            return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

        async def session_dependency():
            async with factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        current = [CurrentUser(id=tenants[0]["user"], empresa_id=tenants[0]["empresa"])]

        async def identity():
            return current[0]

        app.dependency_overrides[get_session] = session_dependency
        app.dependency_overrides[get_current_user] = identity
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test/api/v1/"
        ) as client:
            await body(factory, client, tenants, current, module.id)
    finally:
        await engine.dispose()


def interview(t, post=None, when=None):
    return {
        "postulacion_id": post or t["posts"][0],
        "entrevistador_id": t["user"],
        "tipo": "TECNICA",
        "modalidad": "VIRTUAL",
        "fecha_hora": (when or datetime.now(UTC) + timedelta(days=2)).isoformat(),
        "duracion_min": 45,
        "enlace_reunion": "https://example.invalid/meeting",
        "lugar": "",
    }


def hire(code="IT-001"):
    return {
        "codigo": code,
        "apellido_paterno": "Synthetic",
        "apellido_materno": "",
        "ci_expedido": "LP",
        "fecha_ingreso": datetime.now(UTC).date().isoformat(),
    }


def test_sql_tenant_isolation_and_effective_permissions(database):
    async def body(factory, c, ts, current, module):
        a, b = ts
        r = await c.post("entrevistas", json=interview(b))
        assert r.status_code == 404, r.text
        for path in (
            f"vacantes/{b['vacante']}/ranking",
            f"postulaciones/{b['posts'][0]}/historial",
        ):
            assert (await c.get(path)).status_code == 404
        assert (await c.get("entrevistas", params={"empresa_id": b["empresa"]})).status_code == 403
        async with factory() as s:
            with pytest.raises(SeleccionError) as exc:
                await SeleccionRepository(s, a["empresa"]).postulante(
                    (await s.get(PostulacionModel, b["posts"][0])).postulante_id
                )
            assert exc.value.status_code == 404
            enabled = await s.get(EmpresaModuloModel, (a["empresa"], module))
            enabled.habilitado = False
            await s.commit()
        assert (await c.get("entrevistas")).status_code == 403

    asyncio.run(scenario(database, body))


def test_interview_persistence_collision_boundary_cancel_and_result(database):
    async def body(factory, c, ts, *rest):
        t = ts[0]
        start = datetime.now(UTC) + timedelta(days=2)
        r = await c.post("entrevistas", json=interview(t, when=start))
        assert r.status_code == 201, r.text
        key = r.json()["id"]
        async with factory() as s:
            assert (await s.get(EntrevistaModel, key)).estado == "PROGRAMADA"
        collision = await c.post(
            "entrevistas", json=interview(t, t["posts"][1], start + timedelta(minutes=44))
        )
        assert collision.status_code == 409, collision.text
        adjacent = await c.post(
            "entrevistas", json=interview(t, t["posts"][1], start + timedelta(minutes=45))
        )
        assert adjacent.status_code == 201, adjacent.text
        assert (
            await c.patch(
                f"entrevistas/{key}/resultado",
                json={"puntaje": 90, "observaciones": "Good", "recomendacion": "APTO"},
            )
        ).status_code == 409
        assert (
            await c.patch(f"entrevistas/{key}/estado", json={"estado": "CONFIRMADA"})
        ).status_code == 200
        assert (
            await c.patch(f"entrevistas/{key}/estado", json={"estado": "CANCELADA"})
        ).status_code == 200
        assert (
            await c.patch(f"entrevistas/{key}/estado", json={"estado": "CONFIRMADA"})
        ).status_code == 409
        replacement = await c.post("entrevistas", json=interview(t, when=start))
        assert replacement.status_code == 201
        key = replacement.json()["id"]
        async with factory() as s:
            item = await s.get(EntrevistaModel, key)
            item.fecha_hora = datetime.now(UTC) - timedelta(hours=1)
            await s.commit()
        r = await c.patch(
            f"entrevistas/{key}/resultado",
            json={"puntaje": 92, "observaciones": "SQL verified", "recomendacion": "APTO"},
        )
        assert r.status_code == 200, r.text
        async with factory() as s:
            item = await s.get(EntrevistaModel, key)
            assert item.estado == "REALIZADA" and item.puntaje == 92
        assert (await c.get("entrevistas")).json()["total"] == 3

    asyncio.run(scenario(database, body))


def test_evaluation_validation_persistence_and_foreign_access(database):
    async def body(factory, c, ts, current, module):
        a, b = ts
        data = {
            "tipo": "TECNICA",
            "nombre": "SQL",
            "puntaje": 15,
            "puntaje_maximo": 20,
            "aprobado": True,
            "observaciones": "Synthetic",
        }
        path = f"postulaciones/{a['posts'][0]}/evaluaciones"
        assert (await c.post(path, json={**data, "puntaje": 21})).status_code == 422
        r = await c.post(path, json=data)
        assert r.status_code == 201, r.text
        key = r.json()["id"]
        assert (await c.post(path, json={**data, "evaluador_id": b["user"]})).status_code == 403
        async with factory() as s:
            item = await s.get(EvaluacionModel, key)
            assert item.evaluador_id == a["user"] and item.puntaje == 15
        current[0] = CurrentUser(id=b["user"], empresa_id=b["empresa"])
        assert (await c.patch(f"evaluaciones/{key}", json=data)).status_code == 404
        current[0] = CurrentUser(id=a["user"], empresa_id=a["empresa"])
        assert (
            await c.patch(f"evaluaciones/{key}", json={**data, "puntaje": 18})
        ).status_code == 200
        assert (
            await c.patch(f"evaluaciones/{key}", json={**data, "evaluador_id": b["user"]})
        ).status_code == 409
        assert (await c.get(path)).json()[0]["puntaje"] == "18.00"

    asyncio.run(scenario(database, body))


def test_custom_read_role_cannot_leak_interviews_evaluations_or_derived_scores(database):
    async def body(factory, c, ts, current, module):
        t = ts[0]
        appointment = await c.post("entrevistas", json=interview(t))
        assert appointment.status_code == 201, appointment.text
        evaluation = await c.post(
            f"postulaciones/{t['posts'][0]}/evaluaciones",
            json={
                "tipo": "TECNICA",
                "nombre": "Sensitive SQL",
                "puntaje": 9,
                "puntaje_maximo": 10,
                "aprobado": True,
                "observaciones": "Private assessment",
            },
        )
        assert evaluation.status_code == 201, evaluation.text
        async with factory() as s:
            item = await s.get(EntrevistaModel, appointment.json()["id"])
            item.puntaje, item.observaciones = 88, "Private interview"
            item.fecha_hora, item.estado = datetime.now(UTC) - timedelta(hours=1), "REALIZADA"
            # Keep only postulaciones:ver on this custom role; effective permissions
            # still resolve through the SQL role/module assignments on every request.
            await s.execute(
                delete(rol_permiso_table).where(rol_permiso_table.c.rol_id == t["role"])
            )
            permission = await s.scalar(
                select(PermissionModel).where(PermissionModel.name == "postulaciones:ver")
            )
            await s.execute(
                rol_permiso_table.insert().values(rol_id=t["role"], permiso_id=permission.id)
            )
            await s.commit()
        base = f"vacantes/{t['vacante']}"
        ranking = await c.get(base + "/ranking")
        assert ranking.status_code == 200, ranking.text
        comparison = await c.post(base + "/comparar", json={"postulacion_ids": t["posts"][:2]})
        assert comparison.status_code == 200, comparison.text
        for candidate in ranking.json()["items"] + comparison.json():
            assert candidate["entrevistas"] == [] and candidate["evaluaciones"] == []
            assert (
                candidate["puntaje_entrevistas"] is None
                and candidate["puntaje_evaluaciones"] is None
            )
        for ordering in ("entrevistas", "evaluaciones"):
            assert (await c.get(base + "/ranking", params={"orden": ordering})).status_code == 403
        assert (await c.get("entrevistas")).status_code == 403
        assert (await c.get(f"postulaciones/{t['posts'][0]}/evaluaciones")).status_code == 403
        history = await c.get(f"postulaciones/{t['posts'][0]}/historial")
        assert history.status_code == 200, history.text
        assert all(event["tipo"] not in {"ENTREVISTA", "EVALUACION"} for event in history.json())
        assert "Private" not in history.text

    asyncio.run(scenario(database, body))


def test_hire_rollback_idempotency_and_capacity(database):
    async def body(factory, c, ts, *rest):
        t = ts[0]
        async with factory() as s:
            emp = await GestionarSeleccion(SeleccionRepository(s, t["empresa"])).contratar(
                t["posts"][0], {**hire(), "fecha_ingreso": datetime.now(UTC).date()}
            )
            rolled_back_id = emp.id
            await s.rollback()
        async with factory() as s:
            assert await s.get(EmpleadoModel, rolled_back_id) is None
            post = await s.get(PostulacionModel, t["posts"][0])
            assert post.estado == "ACTIVA" and post.empleado_id is None
            assert (await s.get(VacanteModel, t["vacante"])).estado == "PUBLICADA"
        path = f"postulaciones/{t['posts'][0]}/contratar"
        first = await c.post(path, json=hire())
        assert first.status_code == 201, first.text
        second = await c.post(path, json=hire())
        assert second.status_code == 201 and second.json()["id"] == first.json()["id"], second.text
        assert (await c.post(path, json=hire("OTHER"))).status_code == 409
        assert (
            await c.post(f"postulaciones/{t['posts'][1]}/contratar", json=hire("IT-002"))
        ).status_code == 409
        async with factory() as s:
            assert (
                await s.scalar(
                    select(func.count())
                    .select_from(EmpleadoModel)
                    .where(EmpleadoModel.empresa_id == t["empresa"])
                )
                == 1
            )
            post = await s.get(PostulacionModel, t["posts"][0])
            vacancy = await s.get(VacanteModel, t["vacante"])
            assert post.etapa_id == t["hired"] and post.estado == "CONTRATADA"
            assert vacancy.estado == "CERRADA" and vacancy.fecha_cierre is not None

    asyncio.run(scenario(database, body))


@pytest.mark.parametrize("operation", ["hire", "hire_same_post", "interview"])
def test_concurrent_requests_serialize_real_sql_locks(database, operation):
    async def body(factory, c, ts, *rest):
        t = ts[0]
        ready = asyncio.Event()
        start = datetime.now(UTC) + timedelta(days=3)

        async def winner():
            async with factory() as s:
                service = GestionarSeleccion(SeleccionRepository(s, t["empresa"]))
                if operation.startswith("hire"):
                    await service.contratar(
                        t["posts"][0], {**hire("RACE-1"), "fecha_ingreso": datetime.now(UTC).date()}
                    )
                else:
                    await service.guardar_entrevista(
                        {**interview(t, when=start), "fecha_hora": start}
                    )
                ready.set()
                # Observe an actual PostgreSQL lock wait before releasing the winner;
                # a merely sequential schedule must not satisfy this race regression.
                async with factory() as monitor:
                    for _ in range(200):
                        waiting = await monitor.scalar(
                            text(
                                "SELECT count(*) FROM pg_stat_activity WHERE application_name = :name "
                                "AND wait_event_type = 'Lock'"
                            ),
                            {"name": database},
                        )
                        if waiting:
                            break
                        await monitor.rollback()
                        await asyncio.sleep(0.01)
                    else:
                        pytest.fail(
                            "The competing SQL session never waited for the winner's row lock"
                        )
                await s.commit()

        async def competitor():
            await ready.wait()
            if operation.startswith("hire"):
                post = t["posts"][0 if operation == "hire_same_post" else 1]
                code = "RACE-1" if operation == "hire_same_post" else "RACE-2"
                return await c.post(f"postulaciones/{post}/contratar", json=hire(code))
            return await c.post("entrevistas", json=interview(t, t["posts"][1], start))

        _, loser = await asyncio.wait_for(asyncio.gather(winner(), competitor()), timeout=20)
        assert loser.status_code == (201 if operation == "hire_same_post" else 409), loser.text
        async with factory() as s:
            if operation.startswith("hire"):
                assert (
                    await s.scalar(
                        select(func.count())
                        .select_from(EmpleadoModel)
                        .where(EmpleadoModel.empresa_id == t["empresa"])
                    )
                    == 1
                )
                assert (await s.get(PostulacionModel, t["posts"][1])).estado == "ACTIVA"
                if operation == "hire_same_post":
                    assert (
                        loser.json()["id"]
                        == (await s.get(PostulacionModel, t["posts"][0])).empleado_id
                    )
            else:
                assert (
                    await s.scalar(
                        select(func.count())
                        .select_from(EntrevistaModel)
                        .where(EntrevistaModel.entrevistador_id == t["user"])
                    )
                    == 1
                )

    asyncio.run(scenario(database, body))


def test_phone_timezone_responsible_and_agenda_filters(database):
    async def body(factory, c, ts, *rest):
        a, b = ts
        data = {
            **interview(a),
            "tipo": "TELEFONICA",
            "modalidad": "TELEFONICA",
            "enlace_reunion": "",
        }
        assert (
            await c.post("entrevistas", json={**data, "entrevistador_id": b["user"]})
        ).status_code == 422
        assert (
            await c.post("entrevistas", json={**data, "fecha_hora": "2030-01-01T10:00:00"})
        ).status_code == 422
        assert (
            await c.post("entrevistas", json={**data, "fecha_hora": "2020-01-01T10:00:00Z"})
        ).status_code == 422
        r = await c.post("entrevistas", json=data)
        assert r.status_code == 201, r.text
        async with factory() as s:
            item = await s.get(EntrevistaModel, r.json()["id"])
            assert item.tipo == item.modalidad == "TELEFONICA"
        agenda = await c.get(
            "entrevistas",
            params={"estado": "PROGRAMADA", "postulacion_id": a["posts"][0], "limit": 1},
        )
        assert agenda.status_code == 200 and agenda.json()["total"] == 1
        assert (
            await c.get("entrevistas", params={"desde": "2030-01-01T10:00:00"})
        ).status_code == 422
        assert (await c.get("entrevistas", params={"offset": 1})).json()["items"] == []
        async with factory() as s:
            user = await s.get(UserModel, a["user"])
            user.is_active = False
            await s.commit()
            with pytest.raises(SeleccionError) as exc:
                await SeleccionRepository(s, a["empresa"]).responsable(
                    a["user"], "entrevistas:registrar_resultado"
                )
            assert exc.value.status_code == 422

    asyncio.run(scenario(database, body))


def test_failed_audit_rolls_back_hire_in_request_transaction(database, monkeypatch):
    import ssas.postulaciones.infrastructure.http.seleccion_router as selection_http

    async def fail_audit(*args, **kwargs):
        raise SeleccionError("Injected audit failure", 409)

    monkeypatch.setattr(selection_http, "auditar", fail_audit)

    async def body(factory, c, ts, *rest):
        t = ts[0]
        response = await c.post(f"postulaciones/{t['posts'][0]}/contratar", json=hire())
        assert response.status_code == 409 and response.json()["detail"] == "Injected audit failure"
        async with factory() as s:
            assert (
                await s.scalar(
                    select(func.count())
                    .select_from(EmpleadoModel)
                    .where(EmpleadoModel.empresa_id == t["empresa"])
                )
                == 0
            )
            post = await s.get(PostulacionModel, t["posts"][0])
            assert post.estado == "ACTIVA" and post.empleado_id is None
            assert (await s.get(VacanteModel, t["vacante"])).estado == "PUBLICADA"

    asyncio.run(scenario(database, body))


def test_ranking_comparison_latest_analysis_and_history(database):
    async def body(factory, c, ts, *rest):
        a, b = ts
        async with factory() as s:
            for days, skills in [(2, ["Old"]), (1, ["SQL", "Python"])]:
                s.add(
                    AnalisisCvModel(
                        id=uid(),
                        postulacion_id=a["posts"][0],
                        puntaje_afinidad=90,
                        habilidades_detectadas=skills,
                        habilidades_faltantes=["Rust"],
                        anios_experiencia_detectados=2,
                        resumen_ia="Synthetic fixture; no provider",
                        modelo_usado="fixture",
                        tiempo_proceso_ms=0,
                        fecha_analisis=datetime.now(UTC) - timedelta(days=days),
                    )
                )
            await s.commit()
        evaluation = {
            "tipo": "TECNICA",
            "nombre": "SQL",
            "puntaje": 8,
            "puntaje_maximo": 10,
            "aprobado": True,
        }
        assert (
            await c.post(f"postulaciones/{a['posts'][0]}/evaluaciones", json=evaluation)
        ).status_code == 201
        base = f"vacantes/{a['vacante']}"
        ranking = await c.get(base + "/ranking")
        assert ranking.status_code == 200, ranking.text
        items = ranking.json()["items"]
        assert [x["id"] for x in items] == a["posts"]
        assert items[0]["habilidades_detectadas"] == ["SQL", "Python"]
        assert items[0]["puntaje_evaluaciones"] == 80
        manual = (await c.get(base + "/ranking", params={"orden": "manual", "limit": 1})).json()
        assert manual["total"] == 3 and manual["items"][0]["id"] == a["posts"][1]
        assert (
            await c.post(base + "/comparar", json={"postulacion_ids": a["posts"][:2]})
        ).status_code == 200
        assert (
            await c.post(
                base + "/comparar", json={"postulacion_ids": [a["posts"][0], b["posts"][0]]}
            )
        ).status_code == 422
        assert (
            await c.post(base + "/comparar", json={"postulacion_ids": [a["posts"][0]] * 2})
        ).status_code == 422
        history = await c.get(f"postulaciones/{a['posts'][0]}/historial")
        assert history.status_code == 200, history.text
        events = history.json()
        assert [e["tipo"] for e in events].count("ANALISIS_CV") == 2
        assert any(e["tipo"] == "EVALUACION" and e["responsable"] == "Tester 0" for e in events)
        assert [e["fecha"] for e in events] == sorted([e["fecha"] for e in events], reverse=True)

    asyncio.run(scenario(database, body))


def test_flujo_completo_cu13_a_cu19(database, tmp_path, monkeypatch):
    """QA-04: postulación -> CV -> análisis -> entrevista -> evaluación -> contratación."""
    monkeypatch.setattr(settings, "ia_proveedor_cv", "local")
    monkeypatch.setattr(settings, "cv_storage_directory", str(tmp_path))

    async def body(factory, c, ts, current, module):
        a, b = ts
        codigo = uid()
        pdf = tmp_path / (re.sub(r"[^A-Z0-9-]", "_", codigo.upper()) + ".pdf")
        canvas = Canvas(str(pdf))
        y = 760
        for line in (
            "Flujo Completo, desarrollador de software radicado en La Paz, Bolivia.",
            "5 anios de experiencia construyendo aplicaciones web con Python.",
            "Manejo de bases de datos relacionales y consultas SQL avanzadas.",
            "Experiencia en pruebas automatizadas, control de versiones con Git",
            "y metodologias agiles de trabajo en equipo.",
        ):
            canvas.drawString(50, y, line)
            y -= 16
        canvas.save()

        # Pasos 1 y 2: vacante con 3 habilidades (una obligatoria) y postulación activa con CV.
        async with factory() as s:
            habilidades = []
            for nombre in ("Python", "SQL", "Docker"):
                skill = HabilidadModel(
                    id=uid(), empresa_id=a["empresa"], nombre=nombre, activo=True
                )
                s.add(skill)
                habilidades.append(skill)
            await s.flush()
            cargo = (
                await s.scalars(select(CargoModel).where(CargoModel.empresa_id == a["empresa"]))
            ).first()
            dep = (
                await s.scalars(
                    select(DepartamentoModel).where(DepartamentoModel.empresa_id == a["empresa"])
                )
            ).first()
            initial = (
                await s.scalars(
                    select(EtapaReclutamientoModel).where(
                        EtapaReclutamientoModel.empresa_id == a["empresa"],
                        EtapaReclutamientoModel.es_inicial.is_(True),
                    )
                )
            ).first()
            vacancy = VacanteModel(
                id=uid(),
                empresa_id=a["empresa"],
                cargo_id=cargo.id,
                departamento_id=dep.id,
                responsable_id=a["user"],
                titulo="Vacante flujo QA-04",
                descripcion="Solo para el flujo completo del CU-13 al CU-19",
                modalidad="REMOTO",
                estado="PUBLICADA",
                cantidad_vacantes=1,
                experiencia_min=3,
            )
            s.add(vacancy)
            await s.flush()
            for position, skill in enumerate(habilidades):
                s.add(
                    VacanteHabilidadModel(
                        id=uid(),
                        vacante_id=vacancy.id,
                        habilidad_id=skill.id,
                        nivel_requerido="INTERMEDIO",
                        es_obligatorio=position == 0,
                        peso=Decimal("3.00"),
                    )
                )
            candidate = PostulanteModel(
                id=uid(),
                empresa_id=a["empresa"],
                nombres="Flujo",
                apellidos="Contratacion",
                ci="FLUJO01",
                email="flujo@example.invalid",
                telefono="70000000",
                ciudad="La Paz",
                nivel_educativo="LICENCIATURA",
                fuente="OTRO",
                anios_experiencia=5,
                cv_url=pdf.as_posix(),
            )
            rival = PostulanteModel(
                id=uid(),
                empresa_id=a["empresa"],
                nombres="Flujo",
                apellidos="Comparacion",
                ci="FLUJO02",
                email="comparacion@example.invalid",
                telefono="70000001",
                ciudad="La Paz",
                nivel_educativo="LICENCIATURA",
                fuente="OTRO",
                anios_experiencia=2,
            )
            s.add_all([candidate, rival])
            await s.flush()
            post_cv = PostulacionModel(
                id=uid(),
                vacante_id=vacancy.id,
                postulante_id=candidate.id,
                etapa_id=initial.id,
                estado="ACTIVA",
                codigo_seguimiento=codigo,
            )
            post_rival = PostulacionModel(
                id=uid(),
                vacante_id=vacancy.id,
                postulante_id=rival.id,
                etapa_id=initial.id,
                estado="ACTIVA",
                codigo_seguimiento=uid(),
            )
            s.add_all([post_cv, post_rival])
            await s.commit()
            flow = {
                "vacante": vacancy.id,
                "post_cv": post_cv.id,
                "post_rival": post_rival.id,
                "postulante": candidate.id,
                "codigo": codigo,
            }

        # Paso 3 (CU-13): análisis del CV con el proveedor local.
        r = await c.post(f"postulaciones/{flow['post_cv']}/analisis-cv")
        assert r.status_code == 201, r.text
        analysis = r.json()
        assert 0 <= float(analysis["puntaje_afinidad"]) <= 100
        assert analysis["modelo_usado"] == "extraccion-local-v1"
        assert "Python" in analysis["habilidades_detectadas"]
        assert "SQL" in analysis["habilidades_detectadas"]
        assert analysis["habilidades_faltantes"] == ["Docker"]
        assert analysis["anios_experiencia_detectados"] == 5
        analysis_id = analysis["id"]

        # Paso 4 (CU-14): ranking de la vacante ordenado por el puntaje de la IA.
        ranking = await c.get(f"vacantes/{flow['vacante']}/ranking", params={"orden": "ia"})
        assert ranking.status_code == 200, ranking.text
        page = ranking.json()
        assert page["total"] == 2
        assert page["items"][0]["id"] == flow["post_cv"]
        assert page["items"][0]["puntaje_ia"] is not None
        assert page["items"][1]["puntaje_ia"] is None

        # Paso 5 (CU-15): entrevista programada para una fecha futura.
        r = await c.post("entrevistas", json=interview(a, post=flow["post_cv"]))
        assert r.status_code == 201, r.text
        entrevista_id = r.json()["id"]
        assert r.json()["estado"] == "PROGRAMADA"

        # Paso 6 (CU-15): el postulante confirma con su código de seguimiento.
        r = await c.post(
            f"publico/postulaciones/{flow['codigo']}/entrevista/confirmar",
            params={"entrevista_id": entrevista_id},
        )
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == "CONFIRMADA"

        # Paso 7 (CU-16): resultado de la entrevista ya realizada.
        async with factory() as s:
            item = await s.get(EntrevistaModel, entrevista_id)
            item.fecha_hora = datetime.now(UTC) - timedelta(hours=1)
            await s.commit()
        r = await c.patch(
            f"entrevistas/{entrevista_id}/resultado",
            json={
                "puntaje": 91,
                "observaciones": "Flujo QA-04 verificado",
                "recomendacion": "APTO",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["estado"] == "REALIZADA"

        # Paso 8 (CU-16): evaluación técnica de la postulación.
        r = await c.post(
            f"postulaciones/{flow['post_cv']}/evaluaciones",
            json={
                "tipo": "TECNICA",
                "nombre": "Prueba flujo QA-04",
                "puntaje": 9,
                "puntaje_maximo": 10,
                "aprobado": True,
                "observaciones": "Evaluacion del flujo completo",
            },
        )
        assert r.status_code == 201, r.text
        evaluacion_id = r.json()["id"]

        # Paso 9 (CU-17): comparación de las dos postulaciones de la vacante.
        r = await c.post(
            f"vacantes/{flow['vacante']}/comparar",
            json={"postulacion_ids": [flow["post_cv"], flow["post_rival"]]},
        )
        assert r.status_code == 200, r.text
        assert {item["id"] for item in r.json()} == {flow["post_cv"], flow["post_rival"]}

        # Paso 10 (CU-18): el postulante queda en el banco de talento.
        r = await c.patch(
            f"postulantes/{flow['postulante']}/banco-talento", json={"en_banco_talento": True}
        )
        assert r.status_code == 200, r.text
        assert r.json()["en_banco_talento"] is True

        # Paso 11 (CU-19): contratación que crea el empleado.
        r = await c.post(f"postulaciones/{flow['post_cv']}/contratar", json=hire("QA04-001"))
        assert r.status_code == 201, r.text
        empleado_id = r.json()["id"]

        # Paso 12 (CU-19): el empleado aparece en el listado de la empresa.
        r = await c.get("empleados")
        assert r.status_code == 200, r.text
        assert any(item["id"] == empleado_id for item in r.json()["items"])

        # Paso 13: historial de la postulación con los pasos 3 a 11.
        r = await c.get(f"postulaciones/{flow['post_cv']}/historial")
        assert r.status_code == 200, r.text
        events = r.json()
        tipos = {event["tipo"] for event in events}
        assert {"ANALISIS_CV", "ENTREVISTA", "EVALUACION"} <= tipos
        assert any(event["tipo"] == "APPROVE" for event in events)

        async with factory() as s:
            post = await s.get(PostulacionModel, flow["post_cv"])
            assert post.empleado_id == empleado_id
            assert post.estado == "CONTRATADA"
            audit = (
                await s.scalars(
                    select(AuditLogModel).where(
                        AuditLogModel.empresa_id == a["empresa"],
                        AuditLogModel.module == "SELECCION",
                    )
                )
            ).all()
        # Cada paso que escribe deja su evento en bitacora con modulo SELECCION.
        # La descripcion se persiste cifrada, por eso se verifican los campos claros.
        assert len(audit) == 7
        assert {(row.tabla_afectada, row.action) for row in audit} == {
            ("analisis_cv", "CREATE"),
            ("entrevista", "CREATE"),
            ("entrevista", "UPDATE"),
            ("evaluacion", "CREATE"),
            ("postulacion", "APPROVE"),
            ("postulante", "UPDATE"),
        }
        registros = {}
        for row in audit:
            registros.setdefault(row.tabla_afectada, set()).add(row.registro_id)
        assert registros == {
            "analisis_cv": {analysis_id},
            "entrevista": {entrevista_id},
            "evaluacion": {evaluacion_id},
            "postulacion": {flow["post_cv"]},
            "postulante": {flow["postulante"]},
        }

        # Aislamiento multiempresa sobre los pasos 4, 12 y 13.
        current[0] = CurrentUser(id=b["user"], empresa_id=b["empresa"])
        assert (await c.get(f"vacantes/{flow['vacante']}/ranking")).status_code == 404
        assert (await c.get(f"postulaciones/{flow['post_cv']}/historial")).status_code == 404
        foreign_page = (await c.get("empleados")).json()
        assert foreign_page["items"] == [] and foreign_page["total"] == 0
        current[0] = CurrentUser(id=a["user"], empresa_id=a["empresa"])
        assert (await c.get(f"vacantes/{flow['vacante']}/ranking")).status_code == 200

    asyncio.run(scenario(database, body))

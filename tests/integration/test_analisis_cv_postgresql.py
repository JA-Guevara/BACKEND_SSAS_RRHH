"""Isolated schema on the disposable loopback Sprint2 database, never production .env."""

import asyncio
import importlib
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from ssas.analisis_cv.domain.analysis import AnalisisCvError, ResultadoIA
from ssas.analisis_cv.infrastructure.persistence.models.analisis_cv import AnalisisCvModel
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.bitacora.infrastructure.persistence.models.audit_log import AuditLogModel
from ssas.cargos.infrastructure.persistence.models.cargo import CargoModel
from ssas.config.settings import Settings
from ssas.departamentos.infrastructure.persistence.models.departamento import DepartamentoModel
from ssas.empresas.infrastructure.persistence.models.empresa import EmpresaModel
from ssas.habilidades.infrastructure.persistence.models.habilidad import HabilidadModel
from ssas.infrastructure.database.base import Base, import_all_models
from ssas.postulaciones.infrastructure.http.seleccion_schemas import AnalisisResponse
from ssas.postulaciones.infrastructure.persistence.models.etapa_reclutamiento import (
    EtapaReclutamientoModel,
)
from ssas.postulaciones.infrastructure.persistence.models.postulacion import PostulacionModel
from ssas.postulantes.infrastructure.persistence.models.postulante import PostulanteModel
from ssas.postulantes.infrastructure.persistence.models.postulante_habilidad import (
    PostulanteHabilidadModel,
)
from ssas.vacantes.infrastructure.persistence.models.vacante import VacanteModel
from ssas.vacantes.infrastructure.persistence.models.vacante_habilidad import VacanteHabilidadModel

import_all_models()


def local_target():
    target = os.getenv("SPRINT2_TEST_DATABASE_URL")
    if not target:
        pytest.skip("Configure SPRINT2_TEST_DATABASE_URL para PostgreSQL local Sprint2")
    url = make_url(target)
    if not (
        url.drivername == "postgresql+psycopg"
        and url.host in {"localhost", "127.0.0.1"}
        and url.port == 55432
        and url.database == "sprint2"
        and url.username == "sprint2"
        and not url.password
        and not url.query
    ):
        pytest.skip("Solo se admite loopback:55432/sprint2, usuario sprint2 sin password/options")
    return target


@asynccontextmanager
async def isolated_database():
    target = local_target()
    schema = "cv_it_" + uuid4().hex
    admin = create_async_engine(target, poolclass=NullPool)
    engine = create_async_engine(
        target,
        poolclass=NullPool,
        connect_args={
            "options": f"-csearch_path={schema},public -clock_timeout=5000 -cstatement_timeout=15000",
            "application_name": schema,
        },
    )
    try:
        async with admin.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync: Base.metadata.create_all(sync, checkfirst=False))
        yield engine, schema
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()


async def seed(factory):
    ids = {
        name: str(uuid4())
        for name in (
            "empresa",
            "other",
            "actor",
            "dep",
            "cargo",
            "vacante",
            "etapa",
            "postulante",
            "post",
            "python",
            "sql",
        )
    }
    async with factory() as session:
        session.add_all(
            [
                EmpresaModel(
                    id=ids["empresa"],
                    slug="cv-test",
                    razon_social="Synthetic",
                    nombre_comercial="Synthetic",
                ),
                EmpresaModel(
                    id=ids["other"], slug="other", razon_social="Other", nombre_comercial="Other"
                ),
            ]
        )
        await session.flush()
        session.add_all(
            [
                UserModel(
                    id=ids["actor"],
                    empresa_id=ids["empresa"],
                    name="Tester",
                    email="test@example.invalid",
                    username="tester",
                    hashed_password="!disabled",
                ),
                DepartamentoModel(id=ids["dep"], empresa_id=ids["empresa"], nombre="Engineering"),
                EtapaReclutamientoModel(
                    id=ids["etapa"],
                    empresa_id=ids["empresa"],
                    nombre="Initial",
                    orden=1,
                    es_inicial=True,
                ),
                HabilidadModel(id=ids["python"], empresa_id=ids["empresa"], nombre="Python"),
                HabilidadModel(id=ids["sql"], empresa_id=ids["empresa"], nombre="SQL"),
                PostulanteModel(
                    id=ids["postulante"],
                    empresa_id=ids["empresa"],
                    nombres="Candidate",
                    apellidos="Synthetic",
                    ci="IT001",
                    email="candidate@example.invalid",
                    telefono="00000000",
                    ciudad="La Paz",
                    nivel_educativo="LICENCIATURA",
                    fuente="OTRO",
                    cv_url="CV-TEST.pdf",
                ),
            ]
        )
        await session.flush()
        session.add(
            CargoModel(
                id=ids["cargo"],
                empresa_id=ids["empresa"],
                departamento_id=ids["dep"],
                nombre="Developer",
            )
        )
        await session.flush()
        session.add(
            VacanteModel(
                id=ids["vacante"],
                empresa_id=ids["empresa"],
                cargo_id=ids["cargo"],
                departamento_id=ids["dep"],
                responsable_id=ids["actor"],
                titulo="Python Developer",
                descripcion="Python and SQL",
                modalidad="REMOTO",
                experiencia_min=4,
            )
        )
        await session.flush()
        session.add_all(
            [
                PostulacionModel(
                    id=ids["post"],
                    vacante_id=ids["vacante"],
                    postulante_id=ids["postulante"],
                    etapa_id=ids["etapa"],
                    codigo_seguimiento="CV-TEST",
                    puntaje_ia=Decimal(10),
                ),
                VacanteHabilidadModel(
                    vacante_id=ids["vacante"],
                    habilidad_id=ids["python"],
                    nivel_requerido="INTERMEDIO",
                    peso=3,
                ),
                VacanteHabilidadModel(
                    vacante_id=ids["vacante"],
                    habilidad_id=ids["sql"],
                    nivel_requerido="INTERMEDIO",
                    peso=1,
                ),
                PostulanteHabilidadModel(
                    postulante_id=ids["postulante"],
                    habilidad_id=ids["python"],
                    nivel="MANUAL",
                    anios_experiencia=7,
                    detectado_por_ia=False,
                ),
            ]
        )
        await session.commit()
    return ids


@pytest.mark.asyncio
async def test_real_sql_persistence_concurrency_and_guards(monkeypatch):
    async with isolated_database() as (engine, schema):
        factory = async_sessionmaker(engine, expire_on_commit=False)
        ids = await seed(factory)
        lock_statements = []

        def record_locks(conn, cursor, statement, parameters, context, executemany):
            if "FOR UPDATE" in statement:
                lock_statements.append(statement)

        event.listen(engine.sync_engine, "before_cursor_execute", record_locks)
        module = importlib.import_module("ssas.analisis_cv.application.use_cases.analizar_cv")
        audit_module = importlib.import_module(
            "ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository",
        )
        config = Settings(
            _env_file=None,
            app_env="development",
            app_secret_key="test",
            app_audit_encryption_key="11" * 32,
        )
        monkeypatch.setattr(module, "settings", config)
        monkeypatch.setattr(audit_module, "settings", config)
        ready, resume = asyncio.Event(), asyncio.Event()
        state = {"calls": 0, "pause": True, "fail": False, "mutate": False}
        doc = "Desarrollo Python. Desarrollo SQL. 2.5 anos de experiencia."

        async def extract(cv_url):
            return doc

        async def analyze(*args):
            state["calls"] += 1
            async with engine.connect() as conn:
                count = await conn.scalar(
                    text(
                        "SELECT count(*) FROM pg_stat_activity WHERE application_name=:name "
                        "AND pid <> pg_backend_pid() AND xact_start IS NOT NULL"
                    ),
                    {"name": schema},
                )
                assert count == 0, "No database transaction may remain during provider call"
            if state["pause"]:
                ready.set()
                await resume.wait()
            if state["fail"]:
                raise AnalisisCvError("Synthetic provider timeout", 504)
            if state["mutate"]:
                async with factory() as changed:
                    vacancy = await changed.get(VacanteModel, ids["vacante"])
                    vacancy.descripcion = "Changed by concurrent request"
                    await changed.commit()
            return ResultadoIA(
                habilidades=[
                    {
                        "habilidad_id": ids["python"],
                        "nivel": "INTERMEDIO",
                        "evidencia": "Desarrollo Python",
                    },
                    {"habilidad_id": ids["sql"], "nivel": "BASICO", "evidencia": "Desarrollo SQL"},
                ],
                anios_experiencia=2.5,
                evidencia_experiencia="2.5 anos de experiencia",
                resumen="Synthetic evidence",
                justificacion="Evidence-based review",
            )

        monkeypatch.setattr(
            module, "LocalCvExtractor", lambda config: SimpleNamespace(extract=extract)
        )
        monkeypatch.setattr(
            module, "OpenAIAnalysisProvider", lambda config: SimpleNamespace(analyze=analyze)
        )
        async with factory() as winner, factory() as loser:
            await winner.scalar(select(UserModel.id).where(UserModel.id == ids["actor"]))
            task = asyncio.create_task(
                module.analizar_cv(
                    winner,
                    ids["post"],
                    ids["empresa"],
                    ids["actor"],
                    source_ip="127.0.0.1",
                    user_agent="integration-test",
                )
            )
            try:
                await asyncio.wait_for(ready.wait(), 10)
                assert not winner.in_transaction()
                with pytest.raises(AnalisisCvError) as exc:
                    await module.analizar_cv(loser, ids["post"], ids["empresa"], ids["actor"])
                assert exc.value.status_code == 409
                resume.set()
                model = await asyncio.wait_for(task, 10)
            finally:
                resume.set()
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            assert model.puntaje_afinidad == Decimal("92.50")
            assert "FROM vacante" in lock_statements[0]
            assert "FROM postulacion" in lock_statements[1]
            assert "FROM postulante" in lock_statements[2]
            assert model.anios_experiencia_detectados == Decimal("2.5")
            response = AnalisisResponse.model_validate(model)
            assert response.habilidades_detectadas == ["Python", "SQL"]
            assert response.anios_experiencia_detectados == 2.5
            async with factory() as check:
                assert (await check.get(PostulacionModel, ids["post"])).puntaje_ia == 10
                assert await check.scalar(select(func.count()).select_from(AnalisisCvModel)) == 0
            with pytest.raises(AnalisisCvError):
                await module.analizar_cv(loser, ids["post"], ids["empresa"], ids["actor"])
            await winner.commit()
        state["pause"] = False
        async with factory() as check:
            stored = await check.get(AnalisisCvModel, model.id)
            assert stored.anios_experiencia_detectados == Decimal("2.50")
            assert (await check.get(PostulacionModel, ids["post"])).puntaje_ia == Decimal("92.50")
            skills = (await check.execute(select(PostulanteHabilidadModel))).scalars().all()
            assert len(skills) == 2
            manual = next(s for s in skills if s.habilidad_id == ids["python"])
            assert manual.nivel == "MANUAL" and manual.anios_experiencia == 7
            assert manual.detectado_por_ia is False
            assert await check.scalar(select(func.count()).select_from(AuditLogModel)) == 1
        state["fail"] = True
        async with factory() as request:
            with pytest.raises(AnalisisCvError, match="timeout"):
                await module.analizar_cv(request, ids["post"], ids["empresa"], ids["actor"])
        async with factory() as check:
            assert await check.scalar(select(func.count()).select_from(AnalisisCvModel)) == 1
            assert (await check.get(PostulacionModel, ids["post"])).puntaje_ia == Decimal("92.50")
        calls = state["calls"]
        async with factory() as request:
            with pytest.raises(AnalisisCvError) as exc:
                await module.analizar_cv(request, ids["post"], ids["other"], ids["actor"])
            assert exc.value.status_code == 403
            item = await request.get(PostulanteModel, ids["postulante"])
            item.ci = "IT002"
            await request.flush()
            with pytest.raises(AnalisisCvError, match="escrituras"):
                await module.analizar_cv(request, ids["post"], ids["empresa"], ids["actor"])
            assert request.in_transaction()
            assert item.ci == "IT002"
            await request.rollback()
        assert state["calls"] == calls
        state["fail"] = False
        async with factory() as request:
            candidate = await request.get(PostulanteModel, ids["postulante"])
            candidate.cv_url = "FOREIGN-CODE.pdf"
            await request.commit()
        async with factory() as request:
            with pytest.raises(AnalisisCvError, match="no pertenece") as exc:
                await module.analizar_cv(request, ids["post"], ids["empresa"], ids["actor"])
            assert exc.value.status_code == 403
        assert state["calls"] == calls
        async with factory() as request:
            candidate = await request.get(PostulanteModel, ids["postulante"])
            candidate.cv_url = "CV-TEST.pdf"
            await request.commit()
        async with factory() as request:
            rolled_back = await module.analizar_cv(
                request,
                ids["post"],
                ids["empresa"],
                ids["actor"],
            )
            rolled_back_id = rolled_back.id
            await request.rollback()
        async with factory() as check:
            assert await check.get(AnalisisCvModel, rolled_back_id) is None
            assert await check.scalar(select(func.count()).select_from(AuditLogModel)) == 1
        state["mutate"] = True
        async with factory() as request:
            with pytest.raises(AnalisisCvError, match="cambiaron"):
                await module.analizar_cv(request, ids["post"], ids["empresa"], ids["actor"])
            await request.rollback()
        async with factory() as check:
            assert await check.scalar(select(func.count()).select_from(AnalisisCvModel)) == 1

import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from ssas.analisis_cv.domain.analysis import AnalisisCvError, validar_evidencia
from ssas.analisis_cv.infrastructure.providers.analysis_lock import analysis_lock, lock_persistence
from ssas.analisis_cv.infrastructure.providers.gemini_provider import GeminiAnalysisProvider
from ssas.config.settings import Settings, settings


@pytest.mark.asyncio
async def test_real_gemini_structured_analysis():
    if os.getenv("RUN_CV_GEMINI_TEST") != "1":
        pytest.skip("Configure RUN_CV_GEMINI_TEST=1 y GEMINI_API_KEY")
    if not settings.gemini_api_key or not settings.gemini_api_key.get_secret_value().strip():
        pytest.skip("GEMINI_API_KEY no configurada")
    skill_id = str(uuid4())
    text = "Desarrollo Python. Experiencia laboral relevante: 2 anos de desarrollo Python."
    result = await GeminiAnalysisProvider(settings).analyze(
        text,
        {"titulo": "Desarrollador Python", "experiencia_min": 2},
        [{"habilidad_id": skill_id, "nombre": "Python"}],
    )
    validar_evidencia(result, {skill_id}, text)
    assert result.habilidades


@pytest.mark.asyncio
async def test_postgresql_lock_handoff_without_commit():
    url = os.getenv("CV_LOCK_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Configure CV_LOCK_TEST_DATABASE_URL para base de pruebas PostgreSQL")
    config = Settings(
        _env_file=None, app_env="development", app_secret_key="test", database_url=url
    )
    engine = create_async_engine(config.database_url)
    post_id = str(uuid4())
    try:
        async with AsyncSession(engine) as request:
            async with analysis_lock(engine, post_id):
                with pytest.raises(AnalisisCvError) as exc:
                    async with analysis_lock(engine, post_id):
                        pytest.fail("duplicate must fail")
                assert exc.value.status_code == 409
                await lock_persistence(request, post_id)
            with pytest.raises(AnalisisCvError):
                async with analysis_lock(engine, post_id):
                    pytest.fail("persistence still uncommitted")
            await request.rollback()
            async with analysis_lock(engine, post_id):
                pass
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_global_slots_leave_main_pool_available():
    url = os.getenv("CV_LOCK_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Configure CV_LOCK_TEST_DATABASE_URL para base de pruebas PostgreSQL")
    config = Settings(
        _env_file=None, app_env="development", app_secret_key="test", database_url=url
    )
    engine = create_async_engine(config.database_url, pool_size=1, max_overflow=0, pool_timeout=1)
    another_worker = create_async_engine(config.database_url, pool_size=1, max_overflow=0)
    try:
        async with analysis_lock(engine, str(uuid4()), max_slots=1):
            assert engine.pool.checkedout() == 0
            async with engine.connect() as conn:
                assert await conn.scalar(text("SELECT 1")) == 1
            with pytest.raises(AnalisisCvError) as exc:
                async with analysis_lock(another_worker, str(uuid4()), max_slots=1):
                    pytest.fail("global slot is busy in another worker")
            assert exc.value.status_code == 503
        async with analysis_lock(another_worker, str(uuid4()), max_slots=1):
            pass
    finally:
        await engine.dispose()
        await another_worker.dispose()

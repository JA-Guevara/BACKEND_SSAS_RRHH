import importlib
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine

from ssas.analisis_cv.domain.analysis import AnalisisCvError, ResultadoIA
from ssas.infrastructure.database.base import import_all_models

import_all_models()


def dummy_resultado():
    return ResultadoIA.model_validate(
        {
            "habilidades": [
                {
                    "habilidad_id": "h-py",
                    "nivel": "INTERMEDIO",
                    "evidencia": "Desarrollo en Python con experiencia laboral comprobada",
                }
            ],
            "anios_experiencia": 3.0,
            "evidencia_experiencia": "3 anios de experiencia comprobada en backend",
            "resumen": "Candidato con solidos conocimientos en Python.",
            "justificacion": "Acredita los requisitos principales solicitados en la vacante.",
        }
    )


CV_TEXTO = (
    "Desarrollador de software con más de 3 anios de experiencia comprobada "
    "en backend. Desarrollo en Python con experiencia laboral comprobada en proyectos web."
)


@pytest.fixture
def base_setup(monkeypatch):
    module = importlib.import_module("ssas.analisis_cv.application.use_cases.analizar_cv")
    ids = [str(uuid4()) for _ in range(3)]
    row = {
        "postulante_id": str(uuid4()),
        "cv_url": "cv.pdf",
        "experiencia_min": 3,
        "titulo": "Backend Dev",
        "descripcion": "Python",
        "requisitos": "Python",
        "nombres": "Ana",
        "apellidos": "Gomez",
        "ci": "456",
        "email": "ana@example.org",
        "telefono": "70001234",
        "direccion": None,
        "linkedin": None,
    }
    snapshot = (
        row,
        [{"habilidad_id": "h-py", "nombre": "Python"}],
        [{"habilidad_id": "h-py", "peso": 1}],
    )
    monkeypatch.setattr(module, "_snapshot", AsyncMock(return_value=snapshot))
    release = AsyncMock()
    monkeypatch.setattr(module, "_release_read_transaction", release)

    @asynccontextmanager
    async def lock(*args, **kwargs):
        yield

    monkeypatch.setattr(module, "analysis_lock", lock)
    monkeypatch.setattr(module, "lock_persistence", AsyncMock())
    monkeypatch.setattr(module, "AsyncSession", lambda engine: MagicMock())

    extractor = SimpleNamespace(extract=AsyncMock(return_value=CV_TEXTO))
    monkeypatch.setattr(module, "LocalCvExtractor", lambda settings: extractor)

    audit = SimpleNamespace(execute=AsyncMock())
    monkeypatch.setattr(module, "RegisterAuditEvent", lambda repo: audit)
    monkeypatch.setattr(module, "SqlAlchemyAuditLogRepository", lambda session: session)

    session = MagicMock()
    session.bind = MagicMock(spec=AsyncEngine)
    session.bind.dialect.name = "postgresql"
    session.new = session.dirty = session.deleted = set()
    session.get = AsyncMock(return_value=SimpleNamespace(puntaje_ia=None))
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    return module, ids, session, audit


@pytest.mark.asyncio
async def test_auto_sin_clave_usa_local(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "auto")
    monkeypatch.setattr(module.settings, "gemini_api_key", None)

    model = await module.analizar_cv(session, *ids)
    assert model.modelo_usado == "extraccion-local-v1"


@pytest.mark.asyncio
async def test_auto_con_clave_usa_gemini(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "auto")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(return_value=dummy_resultado()),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    model = await module.analizar_cv(session, *ids)
    assert model.modelo_usado == module.settings.gemini_cv_model
    gemini_mock.analyze.assert_awaited_once()


@pytest.mark.asyncio
async def test_degrada_ante_503(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "auto")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(side_effect=AnalisisCvError("Servicio no disponible", 503)),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    model = await module.analizar_cv(session, *ids)
    assert model.modelo_usado == "extraccion-local-v1"


@pytest.mark.asyncio
async def test_degrada_ante_504(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "auto")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(side_effect=AnalisisCvError("Tiempo agotado", 504)),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    model = await module.analizar_cv(session, *ids)
    assert model.modelo_usado == "extraccion-local-v1"


@pytest.mark.asyncio
async def test_no_degrada_ante_422(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "auto")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(side_effect=AnalisisCvError("Texto insuficiente", 422)),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    with pytest.raises(AnalisisCvError) as exc_info:
        await module.analizar_cv(session, *ids)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_no_degrada_ante_403(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "auto")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(side_effect=AnalisisCvError("Permiso denegado", 403)),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    with pytest.raises(AnalisisCvError) as exc_info:
        await module.analizar_cv(session, *ids)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_modo_gemini_no_degrada(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "gemini")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(side_effect=AnalisisCvError("Servicio caído", 503)),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    with pytest.raises(AnalisisCvError) as exc_info:
        await module.analizar_cv(session, *ids)
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_modo_local_ignora_gemini(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "local")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(return_value=dummy_resultado()),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    model = await module.analizar_cv(session, *ids)
    assert model.modelo_usado == "extraccion-local-v1"
    gemini_mock.analyze.assert_not_awaited()


@pytest.mark.asyncio
async def test_bitacora_registra_el_proveedor_real(base_setup, monkeypatch):
    module, ids, session, audit = base_setup
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "auto")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    gemini_mock = SimpleNamespace(
        analyze=AsyncMock(side_effect=AnalisisCvError("Indisponible", 503)),
        nombre=module.settings.gemini_cv_model,
    )
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    await module.analizar_cv(session, *ids)
    audit.execute.assert_awaited_once()
    call_kwargs = audit.execute.call_args.kwargs
    assert call_kwargs["new_data"]["modelo_usado"] == "extraccion-local-v1"


@pytest.mark.asyncio
async def test_el_puntaje_se_calcula_igual(base_setup, monkeypatch):
    module, ids, session, _ = base_setup
    # Ejecución por Gemini simulado
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "gemini")
    monkeypatch.setattr(module.settings, "gemini_api_key", SecretStr("test-key"))

    res = dummy_resultado()
    gemini_mock = SimpleNamespace(analyze=AsyncMock(return_value=res), nombre=module.settings.gemini_cv_model)
    monkeypatch.setattr(module, "GeminiAnalysisProvider", lambda s: gemini_mock)

    model_gemini = await module.analizar_cv(session, *ids)

    # Ejecución por mock local con exactamente el mismo resultado
    monkeypatch.setattr(module.settings, "ia_proveedor_cv", "local")
    local_mock = SimpleNamespace(analyze=AsyncMock(return_value=res), nombre="extraccion-local-v1")
    monkeypatch.setattr(module, "ExtraccionLocalProvider", lambda s: local_mock)

    model_local = await module.analizar_cv(session, *ids)

    assert model_gemini.puntaje_afinidad == model_local.puntaje_afinidad

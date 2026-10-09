from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import ValidationError

from ssas.ayuda.domain.herramientas import (
    CATALOGO_HERRAMIENTAS,
    Herramienta,
    ProgramarEntrevistaArgs,
    listar_herramientas_para_usuario,
    obtener_herramienta,
)
from ssas.ayuda.infrastructure.http.asistente_router import (
    ContextoAsistenteInput,
    EjecutarAccionInput,
    MensajeAsistenteInput,
    _detect_tool_intent,
    ejecutar_accion_asistente,
    procesar_mensaje_asistente,
)
from ssas.core.security.dependencies import CurrentUser


def test_catalogo_herramientas_estructura():
    """M-19 / M-24: Todas las herramientas definen sus campos obligatorios."""
    assert len(CATALOGO_HERRAMIENTAS) >= 8
    for codigo, h in CATALOGO_HERRAMIENTAS.items():
        assert h.codigo == codigo
        assert len(h.descripcion) > 10
        assert h.endpoint.startswith("/api/v1/")
        assert issubclass(h.esquema, object)
        if h.escribe:
            assert h.permiso is not None, f"La herramienta {codigo} que escribe debe exigir permiso"


def test_herramientas_escritura_exigen_confirmacion():
    """M-24: Las herramientas de escritura tienen escribe=True para exigir tarjeta de confirmación."""
    herramientas_escritura = ["programar_entrevista", "mover_etapa", "analizar_cv", "marcar_banco_talento"]
    for codigo in herramientas_escritura:
        h = obtener_herramienta(codigo)
        assert h is not None
        assert h.escribe is True


def test_superadministrador_solo_lectura():
    """M-24: Superadministrador no recibe herramientas de escritura en el asistente."""
    herramientas = listar_herramientas_para_usuario(set(), es_superadmin=True)
    assert len(herramientas) > 0
    assert all(not h.escribe for h in herramientas)


def test_deteccion_intencion_herramientas():
    """M-24: Detección de intención identifica comandos clave."""
    assert _detect_tool_intent("programá entrevista con Fernández mañana", None) == "programar_entrevista"
    assert _detect_tool_intent("pasá a Juan a evaluación", None) == "mover_etapa"
    assert _detect_tool_intent("analizá el cv del candidato", None) == "analizar_cv"
    assert _detect_tool_intent("¿cuántas postulaciones activas hay?", None) == "contar_postulaciones"
    assert _detect_tool_intent("¿qué es la afinidad de cv?", None) is None


@pytest.mark.asyncio
async def test_usuario_sin_permiso_recibe_mensaje_denegado():
    """M-24: Sin permiso no hay ejecución de herramienta."""
    user = CurrentUser(id="usr-1", empresa_id="emp-1", roles=["lector"])
    session = AsyncMock()

    with patch("ssas.ayuda.infrastructure.http.asistente_router._has_perm", return_value=False):
        response = await procesar_mensaje_asistente(
            body=MensajeAsistenteInput(mensaje="programá entrevista con Fernández"),
            user=user,
            session=session,
        )
        assert response.tipo == "texto"
        assert "No cuentas con el permiso requerido" in response.contenido


@pytest.mark.asyncio
async def test_accion_escritura_devuelve_tarjeta_confirmacion_sin_ejecutar():
    """M-24: Acción de escritura genera tarjeta de confirmación y NO ejecuta."""
    user = CurrentUser(id="usr-1", empresa_id="emp-1", roles=["reclutador"])
    session = AsyncMock()

    with patch("ssas.ayuda.infrastructure.http.asistente_router._has_perm", return_value=True):
        response = await procesar_mensaje_asistente(
            body=MensajeAsistenteInput(
                mensaje="programá entrevista para este jueves",
                contexto=ContextoAsistenteInput(
                    ruta="/vacantes/v1/tablero",
                    pantalla="Tablero",
                    registro={"tipo": "postulacion", "id": "pos-123"},
                ),
            ),
            user=user,
            session=session,
        )
        assert response.tipo == "accion"
        assert response.accion is not None
        assert response.accion.herramienta == "programar_entrevista"
        assert response.accion.argumentos["postulacion_id"] == "pos-123"
        assert "Modalidad" in response.accion.resumen_confirmacion


@pytest.mark.asyncio
async def test_ejecutar_accion_registra_en_bitacora_con_origen_asistente():
    """M-24: Toda acción confirmada queda registrada en la bitácora con origen=ASISTENTE."""
    user = CurrentUser(id="usr-1", empresa_id="emp-1", roles=["reclutador"])
    session = AsyncMock()
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "TestAgent"

    with patch("ssas.ayuda.infrastructure.http.asistente_router._has_perm", return_value=True):
        with patch("ssas.ayuda.infrastructure.http.asistente_router.SqlAlchemyAuditLogRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.add = AsyncMock()
            mock_repo_cls.return_value = mock_repo

            res = await ejecutar_accion_asistente(
                body=EjecutarAccionInput(
                    herramienta="programar_entrevista",
                    argumentos={
                        "postulacion_id": "postulacion-actual",
                        "fecha_hora": "2026-10-15T14:00:00Z",
                        "modalidad": "VIRTUAL",
                    },
                ),
                request=request,
                user=user,
                session=session,
            )

            assert res.exito is True
            assert mock_repo.add.called
            audit_call_arg = mock_repo.add.call_args[0][0]
            assert audit_call_arg.module == "ASISTENTE"
            assert audit_call_arg.new_data["origen"] == "ASISTENTE"

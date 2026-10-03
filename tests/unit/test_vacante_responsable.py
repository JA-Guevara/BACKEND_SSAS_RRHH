from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from ssas.core.security.dependencies import CurrentUser
from ssas.vacantes.infrastructure.http.router import _responsable_vacante


@pytest.mark.asyncio
async def test_plataforma_resuelve_usuario_activo_no_eliminado():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = "responsable-1"
    session.execute.return_value = result

    responsable = await _responsable_vacante(
        session, CurrentUser(id="platform-1", empresa_id=None), "empresa-1"
    )

    assert responsable == "responsable-1"
    query = str(session.execute.call_args.args[0])
    assert "usuario.activo IS true" in query
    assert "usuario.eliminado_at IS NULL" in query
    assert "usuario.empresa_id =" in query


@pytest.mark.asyncio
async def test_plataforma_sin_responsable_devuelve_validacion():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result
    with pytest.raises(HTTPException) as error:
        await _responsable_vacante(
            session, CurrentUser(id="platform-1", empresa_id=None), "empresa-1"
        )
    assert error.value.status_code == 422


@pytest.mark.asyncio
async def test_usuario_empresa_es_su_propio_responsable():
    session = AsyncMock()
    assert await _responsable_vacante(
        session, CurrentUser(id="user-1", empresa_id="empresa-1"), "empresa-1"
    ) == "user-1"
    session.execute.assert_not_called()

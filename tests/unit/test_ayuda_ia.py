import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException

from ssas.ayuda.infrastructure.http.router import _requests, explicar_articulo
from ssas.ayuda.infrastructure.providers.openai_help_provider import (
    HelpProviderError,
    OpenAIHelpProvider,
)
from ssas.config.settings import Settings

ARTICLE = {
    "id": "importacion",
    "titulo": "Importar catálogos",
    "texto": "Descarga una plantilla CSV y revisa la vista previa.",
    "ruta": "/importaciones",
    "permiso": "importacion:gestionar",
}


@pytest.mark.asyncio
async def test_provider_sends_only_fixed_article_and_does_not_store_response():
    sent = []

    def handle(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        assert request.url == "https://api.openai.com/v1/responses"
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "Primero descarga la plantilla."}
                        ],
                    }
                ],
            },
        )

    config = Settings(_env_file=None, app_secret_key="test", openai_api_key="test-only")
    result = await OpenAIHelpProvider(config, httpx.MockTransport(handle)).explain(ARTICLE)
    assert result == "Primero descarga la plantilla."
    assert sent[0]["store"] is False
    assert sent[0]["input"] == f"Título: {ARTICLE['titulo']}\nGuía: {ARTICLE['texto']}"
    assert "empresa_id" not in json.dumps(sent[0])
    assert "user_id" not in json.dumps(sent[0])


@pytest.mark.asyncio
async def test_provider_rejects_error_without_leaking_details():
    config = Settings(_env_file=None, app_secret_key="test", openai_api_key="test-only")
    transport = httpx.MockTransport(lambda request: httpx.Response(429, text="provider details"))
    with pytest.raises(HelpProviderError, match="no está disponible") as error:
        await OpenAIHelpProvider(config, transport).explain(ARTICLE)
    assert "provider details" not in str(error.value)


@pytest.mark.asyncio
async def test_explain_rejects_invisible_article_without_provider(monkeypatch):
    monkeypatch.setattr(
        "ssas.ayuda.infrastructure.http.router._visible", AsyncMock(return_value=[])
    )
    provider = AsyncMock()
    monkeypatch.setattr("ssas.ayuda.infrastructure.http.router.OpenAIHelpProvider", provider)
    user = SimpleNamespace(id="help-user", must_change_password=False)
    _requests.pop(user.id, None)
    with pytest.raises(HTTPException) as error:
        await explicar_articulo("importacion", user, object())
    assert error.value.status_code == 404
    provider.assert_not_called()
    _requests.pop(user.id, None)


@pytest.mark.asyncio
async def test_explain_without_configuration_returns_local_article(monkeypatch):
    monkeypatch.setattr(
        "ssas.ayuda.infrastructure.http.router._visible", AsyncMock(return_value=[ARTICLE])
    )
    monkeypatch.setattr(
        "ssas.ayuda.infrastructure.http.router.settings",
        SimpleNamespace(help_ai_enabled=False, openai_api_key=None),
    )
    user = SimpleNamespace(id="local-help-user", must_change_password=False)
    _requests.pop(user.id, None)
    result = await explicar_articulo("importacion", user, object())
    assert result["modo"] == "guia"
    assert result["respuesta"] == ARTICLE["texto"]
    _requests.pop(user.id, None)

import pytest
from httpx import ASGITransport, AsyncClient

from ssas.config.settings import settings
from ssas.core.security.jwt import JWTService
from ssas.main import app


@pytest.fixture(autouse=True)
def secure_test_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_secret_key", "unit-test-secret-key-with-at-least-32-bytes")


def test_unified_token_supports_global_scope_without_tenant() -> None:
    service = JWTService()
    token = service.create_access_token("admin-id", None, ["SUPER_ADMIN"])
    payload = service.decode_token(token, "access")
    assert payload["tid"] is None
    assert payload["roles"] == ["SUPER_ADMIN"]


def test_openapi_has_shared_resources_without_platform_stack() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/empresas" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/usuarios" in paths
    assert not any(path.startswith("/api/v1/platform") for path in paths)


@pytest.mark.asyncio
async def test_cors_allows_configured_frontend() -> None:
    origin = settings.cors_origins[0]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options(
            "/api/v1/empresas",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin

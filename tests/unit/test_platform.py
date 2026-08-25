import pytest
from httpx import ASGITransport, AsyncClient

from ssas.auth.domain.exceptions import InvalidTokenError
from ssas.config.settings import settings
from ssas.core.security.jwt import JWTService
from ssas.main import app
from ssas.platform.infrastructure.security.jwt_service import PlatformJWTService


@pytest.fixture(autouse=True)
def secure_test_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_secret_key", "unit-test-secret-key-with-at-least-32-bytes")


def test_platform_token_has_global_scope_without_tenant() -> None:
    service = PlatformJWTService()
    token, _ = service.create_access_token("admin-id")
    payload = service.decode(token, "access")
    assert payload["scope"] == "platform"
    assert payload["roles"] == ["SUPER_ADMIN"]
    assert "tid" not in payload


def test_platform_rejects_tenant_token() -> None:
    tenant_token = JWTService().create_access_token("user-id", "empresa-id", ["ADMIN_EMPRESA"])
    with pytest.raises(InvalidTokenError):
        PlatformJWTService().decode(tenant_token, "access")


def test_openapi_separates_platform_and_tenant_routes() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/platform/empresas" in paths
    assert "/api/v1/platform/auth/login" in paths
    assert "/api/v1/mi-empresa" in paths
    assert "/api/v1/usuarios" in paths


@pytest.mark.asyncio
async def test_cors_allows_configured_frontend() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options(
            "/api/v1/platform/empresas",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

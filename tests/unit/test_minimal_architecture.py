from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from ssas.auth.application.use_cases.refresh_token import RefreshToken
from ssas.core.security.dependencies import CurrentUser
from ssas.infrastructure.database.base import Base, import_all_models
from ssas.main import app
from ssas.usuarios.infrastructure.http.router import _target_empresa


def test_schema_contains_only_current_scope_tables() -> None:
    import_all_models()
    assert set(Base.metadata.tables) == {
        "empresa",
        "usuario",
        "rol",
        "permiso",
        "usuario_rol",
        "rol_permiso",
        "refresh_token",
        "password_reset_token",
        "email_verification_token",
        "bitacora",
    }


def test_openapi_does_not_expose_deferred_modules() -> None:
    paths = set(app.openapi()["paths"])
    assert not any("planes" in path for path in paths)
    assert not any("suscripciones" in path for path in paths)
    assert not any("parametros" in path for path in paths)
    assert not any(path.startswith("/api/v1/platform") for path in paths)


def test_login_examples_are_valid_request_bodies() -> None:
    login_schema = app.openapi()["components"]["schemas"]["LoginSchema"]
    examples = login_schema["examples"]

    assert examples
    assert all("summary" not in example and "value" not in example for example in examples)
    assert all("password" in example for example in examples)


def test_platform_admin_can_select_target_scope() -> None:
    current = CurrentUser(id="admin", empresa_id=None, roles=["SUPER_ADMIN"])
    assert _target_empresa(current, None) is None
    assert _target_empresa(current, "empresa-a") == "empresa-a"


def test_company_admin_is_forced_to_own_company() -> None:
    current = CurrentUser(id="admin", empresa_id="empresa-a", roles=["ADMIN_EMPRESA"])
    assert _target_empresa(current, None) == "empresa-a"
    assert _target_empresa(current, "empresa-a") == "empresa-a"


def test_company_admin_cannot_select_another_company() -> None:
    current = CurrentUser(id="admin", empresa_id="empresa-a", roles=["ADMIN_EMPRESA"])
    try:
        _target_empresa(current, "empresa-b")
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("Se permitió operar sobre otra empresa")


@pytest.mark.asyncio
async def test_refresh_token_supports_platform_identity() -> None:
    class Tokens:
        def decode_token(self, _token, expected_type):
            assert expected_type == "refresh"
            return {"sub": "admin", "tid": None, "jti": "token-id"}

        def fingerprint(self, _token):
            return "hash"

        def create_refresh_token(self, subject, empresa_id):
            assert subject == "admin" and empresa_id is None
            return "new-refresh", "new-id", datetime.now(UTC) + timedelta(days=1)

        def create_access_token(self, subject, empresa_id, **_kwargs):
            assert subject == "admin" and empresa_id is None
            return "new-access"

    class TokenRepository:
        async def get_active_refresh_token(self, _token_id):
            return SimpleNamespace(empresa_id=None, token_hash="hash")

        async def revoke_refresh_token(self, _token_id):
            return None

        async def save_refresh_token(self, **values):
            assert values["empresa_id"] is None

    class Users:
        async def get_by_id(self, _user_id, empresa_id):
            assert empresa_id is None
            return SimpleNamespace(
                is_active=True,
                empresa_is_active=False,
                empresa_id=None,
                roles=["SUPER_ADMIN"],
                email_verified=True,
                locked_until=None,
                must_change_password=False,
            )

    result = await RefreshToken(Tokens(), TokenRepository(), Users()).execute("refresh")
    assert result["access_token"] == "new-access"
    assert result["refresh_token"] == "new-refresh"

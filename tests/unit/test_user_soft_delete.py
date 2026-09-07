from types import SimpleNamespace

import pytest

from ssas.usuarios.application.use_cases.eliminar_usuario import EliminarUsuario
from ssas.usuarios.application.use_cases.restaurar_usuario import RestaurarUsuario
from ssas.usuarios.domain.exceptions import (
    CannotDeleteSelfError,
    LastAdminCannotBeDisabledError,
)


class FakeUsers:
    def __init__(self, *, admin: bool = False, active_admins: int = 2):
        self.user = SimpleNamespace(id="target", is_deleted=False)
        self.admin = admin
        self.active_admins = active_admins
        self.deleted = False
        self.restored = False

    async def get_by_id(self, _user_id, _empresa_id, include_deleted=False):
        if self.deleted and not include_deleted:
            return None
        return self.user

    async def user_has_admin_role(self, _user_id, _empresa_id):
        return self.admin

    async def count_active_admins(self, _empresa_id):
        return self.active_admins

    async def soft_delete_usuario(self, _user_id, _empresa_id, _actor_id):
        self.deleted = True
        self.user.is_deleted = True
        return self.user

    async def restore_usuario(self, _user_id, _empresa_id):
        self.deleted = False
        self.restored = True
        self.user.is_deleted = False
        return self.user


class FakeTokens:
    def __init__(self):
        self.revoked = False
        self.reset_revoked = False
        self.verification_revoked = False

    async def revoke_all_refresh_tokens(self, _user_id, _empresa_id):
        self.revoked = True

    async def revoke_password_reset_tokens(self, _user_id, _empresa_id):
        self.reset_revoked = True

    async def revoke_email_verification_tokens(self, _user_id, _empresa_id):
        self.verification_revoked = True


@pytest.mark.asyncio
async def test_delete_user_revokes_sessions_and_keeps_recoverable_record() -> None:
    users = FakeUsers()
    tokens = FakeTokens()

    result = await EliminarUsuario(users, tokens).execute("target", "company", "actor")

    assert result.is_deleted
    assert users.deleted
    assert tokens.revoked
    assert tokens.reset_revoked
    assert tokens.verification_revoked


@pytest.mark.asyncio
async def test_user_cannot_delete_self() -> None:
    with pytest.raises(CannotDeleteSelfError):
        await EliminarUsuario(FakeUsers(), FakeTokens()).execute("actor", "company", "actor")


@pytest.mark.asyncio
async def test_last_active_admin_cannot_be_deleted() -> None:
    with pytest.raises(LastAdminCannotBeDisabledError):
        await EliminarUsuario(
            FakeUsers(admin=True, active_admins=1), FakeTokens()
        ).execute("target", "company", "actor")


@pytest.mark.asyncio
async def test_restore_user_recovers_record_without_activating_it() -> None:
    users = FakeUsers()
    users.deleted = True
    users.user.is_deleted = True

    result = await RestaurarUsuario(users).execute("target", "company")

    assert not result.is_deleted
    assert users.restored

import pytest

from ssas.roles.application.use_cases.create_role import CreateRole

pytestmark = pytest.mark.asyncio


class FakeRoleRepository:
    def __init__(self):
        self.roles = []

    async def get_by_name(self, name):
        return next((role for role in self.roles if role.name == name), None)

    async def get_by_code(self, code):
        return next((role for role in self.roles if role.codigo == code), None)

    async def create(self, role):
        self.roles.append(role)
        return role


async def test_create_role_keeps_company_and_normalizes_code() -> None:
    repository = FakeRoleRepository()

    role = await CreateRole(repository).execute(
        empresa_id="empresa-a",
        name="Reclutador",
        codigo="reclutador",
    )

    assert role.empresa_id == "empresa-a"
    assert role.codigo == "RECLUTADOR"

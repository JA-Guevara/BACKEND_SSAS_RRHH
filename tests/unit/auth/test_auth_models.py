from sqlalchemy.orm import configure_mappers
from ssah.auth.infrastructure.persistence.models.password_reset_token import (
    PasswordResetTokenModel,
)
from ssah.auth.infrastructure.persistence.models.refresh_token import RefreshTokenModel
from ssah.auth.infrastructure.persistence.models.user import UserModel
from ssah.infrastructure.database.base import Base
from ssah.roles.infrastructure.persistence.models.permission import PermissionModel
from ssah.roles.infrastructure.persistence.models.role import RoleModel
from ssah.roles.infrastructure.persistence.models.user_role import UserRoleModel


def test_auth_models_share_the_same_metadata() -> None:
    configure_mappers()

    assert UserModel.metadata is Base.metadata
    assert RefreshTokenModel.metadata is Base.metadata
    assert PasswordResetTokenModel.metadata is Base.metadata
    assert RoleModel.metadata is Base.metadata
    assert PermissionModel.metadata is Base.metadata
    assert UserRoleModel.metadata is Base.metadata


def test_auth_tables_and_foreign_keys_are_ready_for_migrations() -> None:
    expected_tables = {
        "users",
        "refresh_tokens",
        "password_reset_tokens",
        "roles",
        "permissions",
        "role_permissions",
        "user_roles",
    }

    assert expected_tables.issubset(Base.metadata.tables)
    assert (
        next(iter(RefreshTokenModel.__table__.c.user_id.foreign_keys)).target_fullname == "users.id"
    )
    assert (
        next(iter(PasswordResetTokenModel.__table__.c.user_id.foreign_keys)).target_fullname
        == "users.id"
    )
    assert next(iter(UserRoleModel.__table__.c.user_id.foreign_keys)).target_fullname == "users.id"
    assert next(iter(UserRoleModel.__table__.c.role_id.foreign_keys)).target_fullname == "roles.id"

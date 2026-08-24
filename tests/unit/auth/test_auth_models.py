from sqlalchemy.orm import configure_mappers

from ssas.auth.infrastructure.persistence.models.password_reset_token import (
    PasswordResetTokenModel,
)
from ssas.auth.infrastructure.persistence.models.refresh_token import RefreshTokenModel
from ssas.auth.infrastructure.persistence.models.user import UserModel
from ssas.infrastructure.database.base import Base, import_all_models
from ssas.roles.infrastructure.persistence.models.permission import PermissionModel
from ssas.roles.infrastructure.persistence.models.role import RoleModel
from ssas.roles.infrastructure.persistence.models.user_role import UserRoleModel


def test_auth_models_share_the_same_metadata() -> None:
    import_all_models()
    configure_mappers()

    assert UserModel.metadata is Base.metadata
    assert RefreshTokenModel.metadata is Base.metadata
    assert PasswordResetTokenModel.metadata is Base.metadata
    assert RoleModel.metadata is Base.metadata
    assert PermissionModel.metadata is Base.metadata
    assert UserRoleModel.metadata is Base.metadata


def test_auth_tables_and_foreign_keys_are_ready_for_migrations() -> None:
    expected_tables = {
        "usuario",
        "refresh_token",
        "password_reset_token",
        "rol",
        "permiso",
        "rol_permiso",
        "usuario_rol",
    }

    assert expected_tables.issubset(Base.metadata.tables)
    assert (
        next(iter(RefreshTokenModel.__table__.c.usuario_id.foreign_keys)).target_fullname
        == "usuario.id"
    )
    assert (
        next(iter(PasswordResetTokenModel.__table__.c.usuario_id.foreign_keys)).target_fullname
        == "usuario.id"
    )
    assert (
        next(iter(UserRoleModel.__table__.c.usuario_id.foreign_keys)).target_fullname
        == "usuario.id"
    )
    assert next(iter(UserRoleModel.__table__.c.rol_id.foreign_keys)).target_fullname == "rol.id"

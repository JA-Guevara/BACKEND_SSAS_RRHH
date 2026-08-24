from sqlalchemy import Column, ForeignKey, String
from ssah.infrastructure.database.base import Base


class UserRoleModel(Base):
    __tablename__ = "user_roles"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(String, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

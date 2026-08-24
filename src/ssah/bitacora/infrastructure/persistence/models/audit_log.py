from sqlalchemy import Column, String, Text
from ssah.infrastructure.database.base import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    action = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    user_id = Column(String, nullable=True)

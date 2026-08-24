from abc import ABC, abstractmethod


class AuditLogRepository(ABC):
    @abstractmethod
    def add(self, audit_log):
        raise NotImplementedError

    @abstractmethod
    def list(self, filters: dict | None = None):
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, audit_log_id: str):
        raise NotImplementedError

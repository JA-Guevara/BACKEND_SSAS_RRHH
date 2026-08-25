from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.bitacora.application.dto.audit_log_filter import AuditLogFilter
from ssas.bitacora.application.use_cases.get_audit_log import GetAuditLog
from ssas.bitacora.application.use_cases.list_audit_logs import ListAuditLogs
from ssas.bitacora.domain.exceptions import AuditLogNotFoundError
from ssas.bitacora.infrastructure.http.schemas import AuditLogPageSchema, AuditLogSchema
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.core.security.dependencies import CurrentUser, require_scoped_permission
from ssas.infrastructure.database.session import get_session

router = APIRouter(prefix="/bitacora", tags=["bitacora"])


def _target_empresa(current_user: CurrentUser, requested: str | None) -> str | None:
    if current_user.es_plataforma:
        return requested
    if requested is not None and requested != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="No puedes consultar otra empresa")
    return current_user.empresa_id


@router.get("", response_model=AuditLogPageSchema)
async def list_audit_logs(
    empresa_id: str | None = None,
    user_id: str | None = None,
    module: str | None = None,
    action: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    current_user: CurrentUser = Depends(
        require_scoped_permission("bitacora:ver", "platform:bitacora:ver")
    ),
    session: AsyncSession = Depends(get_session),
):
    filters = AuditLogFilter(
        empresa_id=_target_empresa(current_user, empresa_id),
        user_id=user_id,
        module=module,
        action=action,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    return await ListAuditLogs(SqlAlchemyAuditLogRepository(session)).execute(filters)


@router.get("/{audit_log_id}", response_model=AuditLogSchema)
async def get_audit_log(
    audit_log_id: str,
    empresa_id: str | None = None,
    current_user: CurrentUser = Depends(
        require_scoped_permission("bitacora:ver", "platform:bitacora:ver")
    ),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await GetAuditLog(SqlAlchemyAuditLogRepository(session)).execute(
            audit_log_id,
            _target_empresa(current_user, empresa_id),
        )
    except AuditLogNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

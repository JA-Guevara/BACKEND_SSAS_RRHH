from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.bitacora.application.events.role_events import RoleEvents
from ssas.bitacora.application.use_cases.register_audit_event import RegisterAuditEvent
from ssas.bitacora.infrastructure.persistence.repositories.audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from ssas.core.security.dependencies import CurrentUser, require_permission
from ssas.infrastructure.database.session import get_session
from ssas.roles.application.use_cases.assign_permissions import AssignPermissions
from ssas.roles.application.use_cases.create_role import CreateRole
from ssas.roles.application.use_cases.delete_role import DeleteRole
from ssas.roles.application.use_cases.get_role import GetRole
from ssas.roles.application.use_cases.list_roles import ListRoles
from ssas.roles.application.use_cases.update_role import UpdateRole
from ssas.roles.domain.exceptions import (
    DuplicateRoleError,
    PermissionNotFoundError,
    RoleNotFoundError,
)
from ssas.roles.infrastructure.http.schemas import (
    AssignPermissionsRequest,
    CreateRoleRequest,
    RoleSchema,
    UpdateRoleRequest,
)
from ssas.roles.infrastructure.persistence.repositories.permission_repository import (
    PermissionRepository,
)
from ssas.roles.infrastructure.persistence.repositories.role_repository import (
    SqlAlchemyRoleRepository,
)

router = APIRouter(prefix="/roles", tags=["roles"])


def _repository(session: AsyncSession, empresa_id: str) -> SqlAlchemyRoleRepository:
    return SqlAlchemyRoleRepository(session, empresa_id)


def _audit_context(request: Request, current_user: CurrentUser) -> dict[str, str | None]:
    return {
        "empresa_id": current_user.empresa_id,
        "user_id": current_user.id,
        "source_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


def _events(session: AsyncSession) -> RoleEvents:
    repository = SqlAlchemyAuditLogRepository(session)
    return RoleEvents(RegisterAuditEvent(repository))


@router.get("", response_model=list[RoleSchema])
async def list_roles(
    current_user: CurrentUser = Depends(require_permission("roles:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    return await ListRoles(_repository(session, current_user.empresa_id)).execute()


@router.post("", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: CreateRoleRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("roles:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        role = await CreateRole(_repository(session, current_user.empresa_id)).execute(
            empresa_id=current_user.empresa_id,
            **request.model_dump(),
        )
        await _events(session).created(
            record_id=role.id,
            new_data={"nombre": role.name, "codigo": role.codigo},
            **_audit_context(http_request, current_user),
        )
        return role
    except DuplicateRoleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: str,
    current_user: CurrentUser = Depends(require_permission("roles:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await GetRole(_repository(session, current_user.empresa_id)).execute(role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: str,
    request: UpdateRoleRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("roles:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        values = request.model_dump(exclude_unset=True)
        role = await UpdateRole(_repository(session, current_user.empresa_id)).execute(
            role_id, values
        )
        await _events(session).updated(
            record_id=role.id,
            new_data=values,
            **_audit_context(http_request, current_user),
        )
        return role
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateRoleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("roles:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        await DeleteRole(_repository(session, current_user.empresa_id)).execute(role_id)
        await _events(session).deleted(
            record_id=role_id,
            **_audit_context(http_request, current_user),
        )
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{role_id}/permissions", response_model=RoleSchema)
async def assign_permissions(
    role_id: str,
    request: AssignPermissionsRequest,
    http_request: Request,
    current_user: CurrentUser = Depends(require_permission("roles:gestionar")),
    session: AsyncSession = Depends(get_session),
):
    try:
        role = await AssignPermissions(
            _repository(session, current_user.empresa_id), PermissionRepository(session)
        ).execute(role_id, request.permission_ids)
        await _events(session).permissions_assigned(
            record_id=role_id,
            new_data={"permission_ids": request.permission_ids},
            **_audit_context(http_request, current_user),
        )
        return role
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

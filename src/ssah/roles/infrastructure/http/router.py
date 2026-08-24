from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ssah.infrastructure.database.session import get_session
from ssah.roles.application.use_cases.assign_permissions import AssignPermissions
from ssah.roles.application.use_cases.create_role import CreateRole
from ssah.roles.application.use_cases.delete_role import DeleteRole
from ssah.roles.application.use_cases.get_role import GetRole
from ssah.roles.application.use_cases.list_roles import ListRoles
from ssah.roles.application.use_cases.update_role import UpdateRole
from ssah.roles.domain.exceptions import (
    DuplicateRoleError,
    PermissionNotFoundError,
    RoleNotFoundError,
)
from ssah.roles.infrastructure.http.schemas import (
    AssignPermissionsRequest,
    CreateRoleRequest,
    RoleSchema,
    UpdateRoleRequest,
)
from ssah.roles.infrastructure.persistence.repositories.permission_repository import PermissionRepository
from ssah.roles.infrastructure.persistence.repositories.role_repository import SqlAlchemyRoleRepository


router = APIRouter(prefix="/roles", tags=["roles"])


def _repository(session: AsyncSession) -> SqlAlchemyRoleRepository:
    return SqlAlchemyRoleRepository(session)


@router.get("", response_model=list[RoleSchema])
async def list_roles(session: AsyncSession = Depends(get_session)):
    return await ListRoles(_repository(session)).execute()


@router.post("", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(request: CreateRoleRequest, session: AsyncSession = Depends(get_session)):
    try:
        return await CreateRole(_repository(session)).execute(**request.model_dump())
    except DuplicateRoleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{role_id}", response_model=RoleSchema)
async def get_role(role_id: str, session: AsyncSession = Depends(get_session)):
    try:
        return await GetRole(_repository(session)).execute(role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: str,
    request: UpdateRoleRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        values = request.model_dump(exclude_unset=True)
        return await UpdateRole(_repository(session)).execute(role_id, values)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateRoleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str, session: AsyncSession = Depends(get_session)):
    try:
        await DeleteRole(_repository(session)).execute(role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{role_id}/permissions", response_model=RoleSchema)
async def assign_permissions(
    role_id: str,
    request: AssignPermissionsRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await AssignPermissions(
            _repository(session), PermissionRepository(session)
        ).execute(role_id, request.permission_ids)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
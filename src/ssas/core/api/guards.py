from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ssas.config.settings import settings
from ssas.core.security.dependencies import (
    CurrentUser,
    require_scoped_permission,
)
from ssas.infrastructure.database.session import get_session
from ssas.suscripciones.application.policy import SubscriptionPolicy, SubscriptionPolicyError


def permiso(code: str):
    async def guard(
        request: Request,
        user: CurrentUser = Depends(require_scoped_permission(code, f"platform:{code}")),
        session: AsyncSession = Depends(get_session),
    ):
        if request.method != "GET" and not user.es_plataforma:
            try:
                await SubscriptionPolicy(
                    session, settings.subscription_grace_days
                ).require_operational(user.empresa_id)
            except SubscriptionPolicyError as exc:
                raise HTTPException(409, str(exc)) from exc
        return user

    return guard

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ssah.config.settings import settings
from ssah.infrastructure.database.base import import_all_models

import_all_models()

engine = create_async_engine(settings.database_url, echo=settings.app_debug, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Entrega una transacción por petición y revierte automáticamente ante errores."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
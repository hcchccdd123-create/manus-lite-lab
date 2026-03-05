from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session


def settings_dep() -> Settings:
    return get_settings()


async def db_dep(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session

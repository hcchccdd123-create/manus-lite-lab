from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_dep, settings_dep
from app.core.config import Settings
from app.services.provider_router import ProviderRouter
from app.utils.ids import new_request_id

router = APIRouter(tags=['health'])


@router.get('/health')
async def health(
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    router_service = ProviderRouter(settings, db)
    statuses = {}
    for name, provider in router_service.providers.items():
        statuses[name] = await provider.health_check()

    return {'request_id': new_request_id(), 'data': {'status': 'ok', 'providers': statuses}, 'error': None}

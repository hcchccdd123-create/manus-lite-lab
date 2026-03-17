import json

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_dep, settings_dep
from app.api.schemas import ChatRequestIn
from app.core.config import Settings
from app.services.chat_service import ChatService

router = APIRouter(tags=['chat'])


@router.post('/chat/stream')
async def chat_stream(
    payload: ChatRequestIn,
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    service = ChatService(settings, db)

    async def event_generator():
        try:
            async for evt in service.stream_message(
                session_id=payload.session_id,
                message=payload.message,
                provider=payload.provider,
                model=payload.model,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
                enable_thinking=payload.enable_thinking,
            ):
                yield {'event': evt['event'], 'data': json.dumps(evt['data'], ensure_ascii=False)}
        except Exception as err:
            yield {'event': 'error', 'data': json.dumps({'message': str(err)})}

    return EventSourceResponse(event_generator())

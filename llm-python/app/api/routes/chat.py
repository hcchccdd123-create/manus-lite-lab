import json

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_dep, settings_dep
from app.api.schemas import ChatRequestIn, ChatResponseOut, MessageOut
from app.core.config import Settings
from app.core.errors import ProviderError
from app.services.chat_service import ChatService
from app.utils.ids import new_request_id

router = APIRouter(tags=['chat'])


@router.post('/chat')
async def chat(
    payload: ChatRequestIn,
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    service = ChatService(settings, db)
    try:
        result = await service.send_message(
            session_id=payload.session_id,
            message=payload.message,
            provider=payload.provider,
            model=payload.model,
            runtime_mode=payload.runtime_mode,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            enable_thinking=payload.enable_thinking,
            enable_web_search=payload.enable_web_search,
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except ProviderError as err:
        return {
            'request_id': new_request_id(),
            'data': None,
            'error': {'code': err.code, 'message': err.message, 'details': err.details},
        }

    out = ChatResponseOut(
        request_id=result['request_id'],
        session_id=payload.session_id,
        message=MessageOut.model_validate(result['assistant_message'], from_attributes=True),
        summary_updated=result['summary_updated'],
    )
    return {'request_id': out.request_id, 'data': out.model_dump(), 'error': None}


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
                runtime_mode=payload.runtime_mode,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
                enable_thinking=payload.enable_thinking,
                enable_web_search=payload.enable_web_search,
            ):
                yield {'event': evt['event'], 'data': json.dumps(evt['data'], ensure_ascii=False)}
        except Exception as err:
            yield {'event': 'error', 'data': json.dumps({'message': str(err)})}

    return EventSourceResponse(event_generator())

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_dep, settings_dep
from app.api.schemas import ConversationCreate, ConversationOut, ConversationPatch, MessageOut
from app.core.config import Settings
from app.core.errors import NotFoundError
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.message_repo import MessageRepository
from app.services.conversation_service import ConversationService
from app.utils.ids import new_request_id

router = APIRouter(tags=['conversations'])


@router.post('/conversations')
async def create_conversation(
    payload: ConversationCreate,
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    service = ConversationService(settings, ConversationRepository(db))
    conv = await service.create(
        title=payload.title,
        provider=payload.provider,
        model=payload.model,
        system_prompt=payload.system_prompt,
        memory_window_size=payload.memory_window_size,
    )
    return {'request_id': new_request_id(), 'data': ConversationOut.model_validate(conv, from_attributes=True).model_dump(), 'error': None}


@router.get('/conversations')
async def list_conversations(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    service = ConversationService(settings, ConversationRepository(db))
    items = await service.list(status, limit, offset)
    return {
        'request_id': new_request_id(),
        'data': [ConversationOut.model_validate(x, from_attributes=True).model_dump() for x in items],
        'error': None,
    }


@router.get('/conversations/{session_id}')
async def get_conversation(
    session_id: str,
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    service = ConversationService(settings, ConversationRepository(db))
    try:
        conv = await service.get_or_raise(session_id)
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=err.message) from err
    return {'request_id': new_request_id(), 'data': ConversationOut.model_validate(conv, from_attributes=True).model_dump(), 'error': None}


@router.patch('/conversations/{session_id}')
async def patch_conversation(
    session_id: str,
    payload: ConversationPatch,
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    service = ConversationService(settings, ConversationRepository(db))
    try:
        conv = await service.update(session_id, **payload.model_dump())
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=err.message) from err
    return {'request_id': new_request_id(), 'data': ConversationOut.model_validate(conv, from_attributes=True).model_dump(), 'error': None}


@router.delete('/conversations/{session_id}')
async def delete_conversation(
    session_id: str,
    settings: Settings = Depends(settings_dep),
    db: AsyncSession = Depends(db_dep),
):
    service = ConversationService(settings, ConversationRepository(db))
    try:
        conv = await service.update(session_id, status='archived')
    except NotFoundError as err:
        raise HTTPException(status_code=404, detail=err.message) from err
    return {'request_id': new_request_id(), 'data': ConversationOut.model_validate(conv, from_attributes=True).model_dump(), 'error': None}


@router.get('/conversations/{session_id}/messages')
async def list_messages(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    before_sequence_no: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(db_dep),
):
    repo = MessageRepository(db)
    items = await repo.list(session_id, limit=limit, before_sequence_no=before_sequence_no)
    return {
        'request_id': new_request_id(),
        'data': [MessageOut.model_validate(x, from_attributes=True).model_dump() for x in items],
        'error': None,
    }

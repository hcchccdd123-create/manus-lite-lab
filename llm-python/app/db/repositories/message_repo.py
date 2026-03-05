from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message
from app.utils.ids import new_message_id


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _next_sequence_no(self, conversation_id: str) -> int:
        stmt = select(func.max(Message.sequence_no)).where(Message.conversation_id == conversation_id)
        row = await self.db.execute(stmt)
        max_seq = row.scalar_one_or_none()
        return (max_seq or 0) + 1

    async def create(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        provider: str | None,
        model: str | None,
        request_id: str,
        usage: dict | None = None,
    ) -> Message:
        seq = await self._next_sequence_no(conversation_id)
        usage = usage or {}
        msg = Message(
            id=new_message_id(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence_no=seq,
            provider=provider,
            model=model,
            request_id=request_id,
            prompt_tokens=usage.get('prompt_tokens'),
            completion_tokens=usage.get('completion_tokens'),
            total_tokens=usage.get('total_tokens'),
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list(
        self,
        conversation_id: str,
        limit: int,
        before_sequence_no: int | None = None,
    ) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id)
        if before_sequence_no is not None:
            stmt = stmt.where(Message.sequence_no < before_sequence_no)
        stmt = stmt.order_by(Message.sequence_no.desc()).limit(limit)
        rows = await self.db.execute(stmt)
        messages = list(rows.scalars().all())
        messages.reverse()
        return messages

    async def list_since(self, conversation_id: str, sequence_no: int) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.sequence_no > sequence_no)
            .order_by(Message.sequence_no.asc())
        )
        rows = await self.db.execute(stmt)
        return list(rows.scalars().all())

    async def latest_sequence_no(self, conversation_id: str) -> int:
        stmt = select(func.max(Message.sequence_no)).where(Message.conversation_id == conversation_id)
        row = await self.db.execute(stmt)
        return row.scalar_one_or_none() or 0

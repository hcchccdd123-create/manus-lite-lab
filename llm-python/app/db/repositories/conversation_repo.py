from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation
from app.utils.ids import new_session_id
from app.utils.time import utcnow


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        title: str,
        provider: str,
        model: str,
        system_prompt: str | None,
        memory_window_size: int,
    ) -> Conversation:
        conv = Conversation(
            id=new_session_id(),
            title=title,
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            memory_window_size=memory_window_size,
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get(self, conversation_id: str) -> Conversation | None:
        return await self.db.get(Conversation, conversation_id)

    async def list(self, status: str | None, limit: int, offset: int) -> list[Conversation]:
        stmt = select(Conversation).order_by(Conversation.last_active_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Conversation.status == status)
        rows = await self.db.execute(stmt)
        return list(rows.scalars().all())

    async def update(self, conv: Conversation, **kwargs) -> Conversation:
        for key, value in kwargs.items():
            if value is not None:
                setattr(conv, key, value)
        conv.updated_at = utcnow()
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

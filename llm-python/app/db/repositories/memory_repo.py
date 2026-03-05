from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MemorySnapshot
from app.utils.ids import new_snapshot_id


class MemoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def latest(self, conversation_id: str) -> MemorySnapshot | None:
        stmt = (
            select(MemorySnapshot)
            .where(MemorySnapshot.conversation_id == conversation_id)
            .order_by(MemorySnapshot.covered_until_sequence_no.desc())
            .limit(1)
        )
        row = await self.db.execute(stmt)
        return row.scalar_one_or_none()

    async def create_snapshot(
        self,
        *,
        conversation_id: str,
        summary_text: str,
        covered_until_sequence_no: int,
        source_message_count: int,
        summarizer_provider: str,
        summarizer_model: str,
    ) -> MemorySnapshot:
        snap = MemorySnapshot(
            id=new_snapshot_id(),
            conversation_id=conversation_id,
            summary_text=summary_text,
            covered_until_sequence_no=covered_until_sequence_no,
            source_message_count=source_message_count,
            summarizer_provider=summarizer_provider,
            summarizer_model=summarizer_model,
        )
        self.db.add(snap)
        await self.db.commit()
        await self.db.refresh(snap)
        return snap

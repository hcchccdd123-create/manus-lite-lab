from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeBase
from app.utils.ids import new_knowledge_base_id
from app.utils.time import utcnow


class KnowledgeBaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> KnowledgeBase | None:
        stmt = select(KnowledgeBase).where(KnowledgeBase.name == name).limit(1)
        row = await self.db.execute(stmt)
        return row.scalar_one_or_none()

    async def get_or_create_default(self, *, collection_name: str, docs_dir: str) -> KnowledgeBase:
        kb = await self.get_by_name('default')
        if kb is not None:
            kb.collection_name = collection_name
            kb.docs_dir = docs_dir
            kb.status = 'ready'
            kb.updated_at = utcnow()
            await self.db.commit()
            await self.db.refresh(kb)
            return kb

        kb = KnowledgeBase(
            id=new_knowledge_base_id(),
            name='default',
            collection_name=collection_name,
            docs_dir=docs_dir,
            status='ready',
        )
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

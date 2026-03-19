from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeDocument
from app.utils.ids import new_document_id
from app.utils.time import utcnow


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_source_path(self, *, knowledge_base_id: str, source_path: str) -> KnowledgeDocument | None:
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
            .where(KnowledgeDocument.source_path == source_path)
            .limit(1)
        )
        row = await self.db.execute(stmt)
        return row.scalar_one_or_none()

    async def create_or_update(
        self,
        *,
        knowledge_base_id: str,
        source_path: str,
        title: str,
        content_hash: str,
        file_type: str,
    ) -> tuple[KnowledgeDocument, bool]:
        doc = await self.get_by_source_path(knowledge_base_id=knowledge_base_id, source_path=source_path)
        created = doc is None
        if doc is None:
            doc = KnowledgeDocument(
                id=new_document_id(),
                knowledge_base_id=knowledge_base_id,
                source_path=source_path,
                title=title,
                content_hash=content_hash,
                file_type=file_type,
            )
            self.db.add(doc)
        else:
            doc.title = title
            doc.content_hash = content_hash
            doc.file_type = file_type
            doc.updated_at = utcnow()
        await self.db.commit()
        await self.db.refresh(doc)
        return doc, created

    async def mark_status(
        self,
        doc: KnowledgeDocument,
        *,
        status: str,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> KnowledgeDocument:
        doc.status = status
        if chunk_count is not None:
            doc.chunk_count = chunk_count
        doc.error_message = error_message[:255] if error_message else None
        doc.updated_at = utcnow()
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

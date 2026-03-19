from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb
from llama_index.core.node_parser import SentenceSplitter
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.repositories.document_repo import DocumentRepository
from app.db.repositories.knowledge_base_repo import KnowledgeBaseRepository
from app.rag.embedding_client import GLMEmbeddingClient
from app.rag.types import ImportSummary


class RAGIngestionService:
    SUPPORTED_SUFFIXES = {'.md', '.txt', '.pdf'}

    def __init__(self, *, settings: Settings, db: AsyncSession):
        self.settings = settings
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.embedding_client = GLMEmbeddingClient(
            base_url=settings.glm_base_url,
            api_key=settings.glm_api_key,
            model=settings.glm_embedding_model,
            timeout_seconds=settings.provider_timeout_seconds,
        )
        self.splitter = SentenceSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )

    def _client(self):
        return chromadb.HttpClient(host=self.settings.chroma_host, port=self.settings.chroma_port)

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _read_text(self, path: Path) -> str:
        if path.suffix.lower() == '.pdf':
            reader = PdfReader(str(path))
            return '\n'.join((page.extract_text() or '') for page in reader.pages).strip()
        return path.read_text(encoding='utf-8').strip()

    async def ingest_directory(self) -> ImportSummary:
        docs_dir = Path(self.settings.rag_docs_dir)
        docs_dir.mkdir(parents=True, exist_ok=True)
        files = sorted([p for p in docs_dir.rglob('*') if p.is_file() and p.suffix.lower() in self.SUPPORTED_SUFFIXES])

        client = self._client()
        collection = client.get_or_create_collection(
            name=self.settings.chroma_collection,
            metadata={'hnsw:space': 'cosine'},
        )
        kb = await self.kb_repo.get_or_create_default(
            collection_name=self.settings.chroma_collection,
            docs_dir=str(docs_dir),
        )

        imported = 0
        skipped = 0
        failed = 0
        errors: list[str] = []

        for path in files:
            source_path = str(path.relative_to(docs_dir))
            try:
                text = self._read_text(path)
                if not text.strip():
                    raise ValueError('No extractable text found')
                content_hash = self._hash_text(text)
                existing = await self.doc_repo.get_by_source_path(
                    knowledge_base_id=kb.id,
                    source_path=source_path,
                )
                if existing is not None and existing.status == 'indexed' and existing.content_hash == content_hash:
                    skipped += 1
                    continue
                doc, _ = await self.doc_repo.create_or_update(
                    knowledge_base_id=kb.id,
                    source_path=source_path,
                    title=path.stem,
                    content_hash=content_hash,
                    file_type=path.suffix.lower().lstrip('.'),
                )

                await self.doc_repo.mark_status(doc, status='indexing', chunk_count=0, error_message=None)
                nodes = self.splitter.split_text(text)
                if not nodes:
                    nodes = [text]

                embeddings = await self.embedding_client.embed_texts(nodes)
                chunk_ids = [f'{doc.id}:{idx}' for idx in range(len(nodes))]
                try:
                    collection.delete(where={'document_id': doc.id})
                except Exception:
                    pass

                collection.upsert(
                    ids=chunk_ids,
                    documents=nodes,
                    embeddings=embeddings,
                    metadatas=[
                        {
                            'knowledge_base_id': kb.id,
                            'document_id': doc.id,
                            'title': doc.title,
                            'source_path': doc.source_path,
                            'chunk_index': idx,
                        }
                        for idx in range(len(nodes))
                    ],
                )
                await self.doc_repo.mark_status(doc, status='indexed', chunk_count=len(nodes), error_message=None)
                imported += 1
            except Exception as exc:
                failed += 1
                errors.append(f'{source_path}: {exc}')
                existing = await self.doc_repo.get_by_source_path(knowledge_base_id=kb.id, source_path=source_path)
                if existing is not None:
                    await self.doc_repo.mark_status(existing, status='failed', error_message=str(exc))

        return ImportSummary(
            scanned=len(files),
            imported=imported,
            skipped=skipped,
            failed=failed,
            errors=errors,
        )

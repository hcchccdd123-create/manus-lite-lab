from __future__ import annotations

from dataclasses import dataclass

import chromadb

from app.core.errors import RAGUnavailableError
from app.rag.embedding_client import GLMEmbeddingClient
from app.rag.types import RetrievedChunk, RetrievedContext


@dataclass(frozen=True)
class RetrieverConfig:
    host: str
    port: int
    collection_name: str
    top_k: int
    similarity_threshold: float


class RAGRetriever:
    def __init__(self, *, embedding_client: GLMEmbeddingClient, config: RetrieverConfig):
        self.embedding_client = embedding_client
        self.config = config

    def _client(self):
        try:
            return chromadb.HttpClient(host=self.config.host, port=self.config.port)
        except Exception as exc:  # pragma: no cover - exercised in integration path
            raise RAGUnavailableError(f'Could not connect to Chroma server: {exc}') from exc

    async def retrieve(self, query: str) -> RetrievedContext:
        query_embeddings = await self.embedding_client.embed_texts([query])
        client = self._client()
        try:
            collection = client.get_collection(self.config.collection_name)
        except Exception as exc:
            raise RAGUnavailableError(f'Could not open Chroma collection: {exc}') from exc

        try:
            result = collection.query(
                query_embeddings=query_embeddings,
                n_results=self.config.top_k,
                include=['documents', 'metadatas', 'distances'],
            )
        except Exception as exc:
            raise RAGUnavailableError(f'Chroma query failed: {exc}') from exc

        chunks: list[RetrievedChunk] = []
        documents = (result.get('documents') or [[]])[0]
        metadatas = (result.get('metadatas') or [[]])[0]
        distances = (result.get('distances') or [[]])[0]

        for idx, document in enumerate(documents):
            if not document:
                continue
            distance = distances[idx] if idx < len(distances) else None
            if distance is not None and distance > self.config.similarity_threshold:
                continue
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            chunks.append(
                RetrievedChunk(
                    document_id=str(metadata.get('document_id', '')),
                    title=str(metadata.get('title', 'Untitled')),
                    source_path=str(metadata.get('source_path', '')),
                    content=document,
                    distance=distance,
                )
            )

        if not chunks:
            return RetrievedContext(found=False)

        prompt_lines = [
            '以下是知识库检索到的上下文，请优先依据这些内容回答；若上下文不足，再明确说明不足：',
        ]
        source_lines = ['来源摘要：']
        seen_sources: set[tuple[str, str]] = set()
        for idx, chunk in enumerate(chunks, start=1):
            prompt_lines.append(
                f'[{idx}] 标题：{chunk.title}\n来源：{chunk.source_path}\n内容：{chunk.content}'
            )
            source_key = (chunk.title, chunk.source_path)
            if source_key not in seen_sources:
                source_lines.append(f'{len(seen_sources) + 1}. {chunk.title} ({chunk.source_path})')
                seen_sources.add(source_key)

        return RetrievedContext(
            found=True,
            chunks=chunks,
            prompt_context='\n\n'.join(prompt_lines),
            source_summary='\n'.join(source_lines),
        )

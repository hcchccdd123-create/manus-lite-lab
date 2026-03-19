from __future__ import annotations

from dataclasses import dataclass, field


RAG_MISS_NOTICE = '未命中任何文档，以下回答来自通用模型能力。'


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    title: str
    source_path: str
    content: str
    distance: float | None


@dataclass(frozen=True)
class RetrievedContext:
    found: bool
    chunks: list[RetrievedChunk] = field(default_factory=list)
    prompt_context: str = ''
    source_summary: str = ''


@dataclass(frozen=True)
class ImportSummary:
    scanned: int
    imported: int
    skipped: int
    failed: int
    errors: list[str] = field(default_factory=list)

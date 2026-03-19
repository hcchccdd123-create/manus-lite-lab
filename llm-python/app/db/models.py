from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.utils.time import utcnow


class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default='New Chat')
    status: Mapped[str] = mapped_column(String(32), default='active')
    provider: Mapped[str] = mapped_column(String(32), default='ollama')
    model: Mapped[str] = mapped_column(String(128), default='qwen3.5:0.8b')
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    memory_mode: Mapped[str] = mapped_column(String(32), default='window_summary')
    memory_window_size: Mapped[int] = mapped_column(Integer, default=12)
    summary_message_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_active_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index('idx_conversations_last_active_at', 'last_active_at'),
        Index('idx_conversations_status', 'status'),
    )


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        UniqueConstraint('conversation_id', 'sequence_no', name='uq_messages_conversation_sequence'),
        Index('idx_messages_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_messages_conversation_sequence', 'conversation_id', 'sequence_no'),
    )


class MemorySnapshot(Base):
    __tablename__ = 'memory_snapshots'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    covered_until_sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    source_message_count: Mapped[int] = mapped_column(Integer, nullable=False)
    summarizer_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    summarizer_model: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (Index('idx_memory_conversation_updated', 'conversation_id', 'updated_at'),)


class ProviderCallLog(Base):
    __tablename__ = 'provider_call_logs'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    success: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)


class KnowledgeBase(Base):
    __tablename__ = 'knowledge_bases'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    collection_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    docs_dir: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default='ready')
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class KnowledgeDocument(Base):
    __tablename__ = 'documents'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    knowledge_base_id: Mapped[str] = mapped_column(ForeignKey('knowledge_bases.id', ondelete='CASCADE'), nullable=False)
    source_path: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default='pending')
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint('knowledge_base_id', 'source_path', name='uq_documents_kb_source_path'),
        Index('idx_documents_knowledge_base_status', 'knowledge_base_id', 'status'),
    )

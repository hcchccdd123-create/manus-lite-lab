from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ErrorModel(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class Envelope(BaseModel):
    request_id: str
    data: dict | list | None
    error: ErrorModel | None


class ConversationCreate(BaseModel):
    title: str | None = None
    provider: Literal['ollama', 'glm', 'codex'] | None = None
    model: str | None = None
    system_prompt: str | None = None
    memory_window_size: int | None = Field(default=None, ge=4, le=50)


class ConversationPatch(BaseModel):
    title: str | None = None
    status: Literal['active', 'archived'] | None = None
    provider: Literal['ollama', 'glm', 'codex'] | None = None
    model: str | None = None
    system_prompt: str | None = None


class ConversationOut(BaseModel):
    id: str
    title: str
    status: str
    provider: str
    model: str
    system_prompt: str | None
    memory_mode: str
    memory_window_size: int
    summary_message_count: int
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sequence_no: int
    provider: str | None
    model: str | None
    created_at: datetime


class ChatRequestIn(BaseModel):
    session_id: str
    message: str = Field(min_length=1)
    provider: Literal['ollama', 'glm', 'codex'] | None = None
    model: str | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    enable_thinking: bool | None = None


class ChatResponseOut(BaseModel):
    request_id: str
    session_id: str
    message: MessageOut
    summary_updated: bool

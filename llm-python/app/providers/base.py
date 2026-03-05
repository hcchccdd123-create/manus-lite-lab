from typing import Literal, Protocol

from pydantic import BaseModel

ProviderName = Literal['ollama', 'glm', 'codex']


class ChatMessage(BaseModel):
    role: Literal['system', 'user', 'assistant', 'tool']
    content: str


class ChatRequest(BaseModel):
    provider: ProviderName
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    top_p: float | None = None
    repeat_penalty: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    enable_thinking: bool | None = None
    metadata: dict | None = None


class ChatChunk(BaseModel):
    delta: str
    thinking: str | None = None
    finish_reason: str | None = None


class ChatResponse(BaseModel):
    text: str
    usage: dict | None = None
    raw: dict | None = None


class LLMProvider(Protocol):
    name: ProviderName

    async def chat(self, req: ChatRequest) -> ChatResponse:
        raise NotImplementedError

    async def stream_chat(self, req: ChatRequest):
        raise NotImplementedError

    async def health_check(self) -> bool:
        raise NotImplementedError

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# 统一错误结构：当接口失败时，返回错误码、错误信息和附加细节。
class ErrorModel(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


# 通用响应外壳：所有接口尽量保持 request_id/data/error 三段式结构。
class Envelope(BaseModel):
    request_id: str
    data: dict | list | None
    error: ErrorModel | None


# 会话创建请求体：前端新建会话时提交的参数。
class ConversationCreate(BaseModel):
    title: str | None = None
    provider: Literal['ollama', 'glm', 'codex'] | None = None
    model: str | None = None
    system_prompt: str | None = None
    # 上下文窗口大小限制在 4~50，避免过小丢上下文或过大导致成本/延迟上升。
    memory_window_size: int | None = Field(default=None, ge=4, le=50)


# 会话更新请求体：仅更新传入字段，未传字段保持原值。
class ConversationPatch(BaseModel):
    title: str | None = None
    status: Literal['active', 'archived'] | None = None
    provider: Literal['ollama', 'glm', 'codex'] | None = None
    model: str | None = None
    system_prompt: str | None = None


# 会话详情输出：用于列表或详情接口返回会话元数据。
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


# 单条消息输出：表示会话中的一条用户/助手消息。
class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sequence_no: int
    provider: str | None
    model: str | None
    created_at: datetime


# 聊天请求体：发送消息时的输入参数。
class ChatRequestIn(BaseModel):
    session_id: str
    message: str = Field(min_length=1)
    provider: Literal['ollama', 'glm', 'codex'] | None = None
    model: str | None = None
    # 单次请求的 RAG 覆盖开关：True=强制开启，False=强制关闭，None=不覆盖，交给全局配置和意图识别决定。
    use_rag: bool | None = None
    # 采样温度，越高越发散，越低越稳定。
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    # 限制输出 token 数量，避免响应过长。
    max_tokens: int | None = Field(default=None, ge=1)
    # 可选能力开关（由模型/后端决定是否支持）。
    enable_thinking: bool | None = None

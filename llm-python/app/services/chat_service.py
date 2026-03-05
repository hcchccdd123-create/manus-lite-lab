from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.memory_repo import MemoryRepository
from app.db.repositories.message_repo import MessageRepository
from app.memory.context_builder import ContextBuilder
from app.memory.policy import MemoryPolicy
from app.memory.summarizer import Summarizer
from app.providers.base import ChatMessage, ChatRequest
from app.services.provider_router import ProviderRouter
from app.utils.ids import new_request_id
from app.utils.time import utcnow


class ChatService:
    def __init__(self, settings: Settings, db: AsyncSession):
        self.settings = settings
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.memory_repo = MemoryRepository(db)
        self.provider_router = ProviderRouter(settings, db)
        self.policy = MemoryPolicy(
            window_size=settings.memory_window_size,
            summary_trigger_messages=settings.summary_trigger_messages,
            max_context_chars=settings.max_context_chars,
        )
        self.context_builder = ContextBuilder(max_context_chars=self.policy.max_context_chars)
        self.summarizer = Summarizer(self.provider_router)

    async def send_message(
        self,
        *,
        session_id: str,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        enable_thinking: bool | None = None,
    ):
        request_id = new_request_id()
        conv = await self.conversation_repo.get(session_id)
        if conv is None:
            raise ValueError(f'conversation not found: {session_id}')

        provider_name = provider or conv.provider
        model_name = model or conv.model

        await self.message_repo.create(
            conversation_id=session_id,
            role='user',
            content=message,
            provider=None,
            model=None,
            request_id=request_id,
        )

        context_messages = await self._build_context_messages(conv, current_user_message=message)
        req = ChatRequest(
            provider=provider_name,
            model=model_name,
            messages=context_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            enable_thinking=enable_thinking if provider_name == 'ollama' else False,
        )
        resp = await self.provider_router.chat(req, conversation_id=session_id, request_id=request_id)

        assistant_msg = await self.message_repo.create(
            conversation_id=session_id,
            role='assistant',
            content=resp.text,
            provider=provider_name,
            model=model_name,
            request_id=request_id,
            usage=resp.usage,
        )

        conv.last_active_at = utcnow()
        conv.updated_at = utcnow()
        await self.db.commit()

        snapshot = await self._maybe_update_summary(
            session_id=session_id,
            provider=provider_name,
            model=model_name,
            request_id=request_id,
        )

        return {
            'request_id': request_id,
            'assistant_message': assistant_msg,
            'summary_updated': bool(snapshot),
        }

    async def stream_message(
        self,
        *,
        session_id: str,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        enable_thinking: bool | None = None,
    ) -> AsyncGenerator[dict, None]:
        request_id = new_request_id()
        conv = await self.conversation_repo.get(session_id)
        if conv is None:
            raise ValueError(f'conversation not found: {session_id}')

        provider_name = provider or conv.provider
        model_name = model or conv.model

        await self.message_repo.create(
            conversation_id=session_id,
            role='user',
            content=message,
            provider=None,
            model=None,
            request_id=request_id,
        )

        context_messages = await self._build_context_messages(conv, current_user_message=message)
        req = ChatRequest(
            provider=provider_name,
            model=model_name,
            messages=context_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            enable_thinking=enable_thinking if provider_name == 'ollama' else False,
        )

        yield {'event': 'message.start', 'data': {'request_id': request_id}}
        chunks: list[str] = []
        thinking_chunks: list[str] = []
        async for chunk in self.provider_router.stream_chat(req, conversation_id=session_id, request_id=request_id):
            if chunk.thinking:
                thinking_chunks.append(chunk.thinking)
                yield {'event': 'message.thinking', 'data': {'delta': chunk.thinking}}
            if chunk.delta:
                chunks.append(chunk.delta)
                yield {'event': 'message.delta', 'data': {'delta': chunk.delta}}
            if chunk.finish_reason:
                break

        assistant_text = ''.join(chunks).strip()
        await self.message_repo.create(
            conversation_id=session_id,
            role='assistant',
            content=assistant_text,
            provider=provider_name,
            model=model_name,
            request_id=request_id,
        )

        conv.last_active_at = utcnow()
        conv.updated_at = utcnow()
        await self.db.commit()

        snapshot = await self._maybe_update_summary(
            session_id=session_id,
            provider=provider_name,
            model=model_name,
            request_id=request_id,
        )

        if snapshot:
            yield {
                'event': 'memory.updated',
                'data': {
                    'covered_until_sequence_no': snapshot.covered_until_sequence_no,
                },
            }

        yield {
            'event': 'message.end',
            'data': {'text': assistant_text, 'thinking': ''.join(thinking_chunks), 'request_id': request_id},
        }

    async def _build_context_messages(self, conv, current_user_message: str) -> list[ChatMessage]:
        latest_snapshot = await self.memory_repo.latest(conv.id)
        summary_text = latest_snapshot.summary_text if latest_snapshot else None

        recent = await self.message_repo.list(conv.id, limit=conv.memory_window_size)
        recent_messages = [ChatMessage(role=m.role, content=m.content) for m in recent]

        if not recent_messages or recent_messages[-1].role != 'user' or recent_messages[-1].content != current_user_message:
            recent_messages.append(ChatMessage(role='user', content=current_user_message))

        return self.context_builder.build(
            system_prompt=conv.system_prompt,
            summary_text=summary_text,
            recent_messages=recent_messages,
        )

    async def _maybe_update_summary(self, *, session_id: str, provider: str, model: str, request_id: str):
        latest_snapshot = await self.memory_repo.latest(session_id)
        covered_until = latest_snapshot.covered_until_sequence_no if latest_snapshot else 0
        latest_sequence = await self.message_repo.latest_sequence_no(session_id)
        pending_count = latest_sequence - covered_until

        if pending_count < self.policy.summary_trigger_messages:
            return None

        delta_messages = await self.message_repo.list_since(session_id, covered_until)
        chat_messages = [ChatMessage(role=m.role, content=m.content) for m in delta_messages]

        summary_text = await self.summarizer.summarize(
            provider=provider,
            model=model,
            old_summary=latest_snapshot.summary_text if latest_snapshot else None,
            new_messages=chat_messages,
            conversation_id=session_id,
            request_id=request_id,
        )

        snapshot = await self.memory_repo.create_snapshot(
            conversation_id=session_id,
            summary_text=summary_text,
            covered_until_sequence_no=latest_sequence,
            source_message_count=len(chat_messages),
            summarizer_provider=provider,
            summarizer_model=model,
        )

        conv = await self.conversation_repo.get(session_id)
        if conv:
            conv.summary_message_count = latest_sequence
            conv.updated_at = utcnow()
            await self.db.commit()

        return snapshot

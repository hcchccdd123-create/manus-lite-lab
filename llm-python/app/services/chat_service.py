import json
import re
from collections.abc import AsyncGenerator
from time import monotonic

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
from app.services.thinking_loop_guard import ThinkingLoopGuard
from app.tools import get_current_datetime
from app.utils.ids import new_request_id
from app.utils.time import utcnow


NETWORK_QUERY_HINTS = (
    '天气',
    '气温',
    '降雨',
    '台风',
    '空气质量',
    '新闻',
    '热搜',
    '汇率',
    '金价',
    '油价',
    '股价',
    '股市',
    '大盘',
    '指数',
    '行情',
    '收盘',
    '开盘',
    '涨跌',
    '涨幅',
    '跌幅',
    '道指',
    '纳指',
    '标普',
    '恒生',
    '上证',
    '深证',
    '创业板',
    '币价',
    '票房',
    '航班',
    '路况',
    '最新',
    '实时',
    'today',
    'weather',
    'temperature',
    'forecast',
    'news',
    'headline',
    'exchange rate',
    'stock price',
    'market',
    'index',
    'dow',
    'nasdaq',
    's&p',
    'crypto price',
    'latest',
    'live',
    'real-time',
)


def _is_network_query(text: str) -> bool:
    lowered = text.lower()
    if any(token in lowered for token in NETWORK_QUERY_HINTS):
        return True

    # For time-sensitive topics, require web search even if user didn't use a fixed keyword.
    temporal_tokens = ('今天', '今日', '刚刚', '现在', 'latest', 'today', 'now', 'current')
    market_tokens = (
        '股',
        '行情',
        '指数',
        'market',
        'stocks',
        'shares',
        'etf',
        'crypto',
        'btc',
        'eth',
        '黄金',
        '原油',
        '汇率',
    )
    if any(t in lowered for t in temporal_tokens) and any(t in lowered for t in market_tokens):
        return True

    return False


def _unsupported_web_search_message() -> str:
    return (
        '这个问题需要联网搜索才能保证准确性。'
        '当前所选模型不支持联网搜索，请切换到支持联网搜索的模型后再试，避免基于过期信息或推测回答。'
    )


def _build_follow_up_block(user_message: str) -> str:
    lowered = user_message.lower()
    compact = ' '.join(user_message.strip().split())
    topic = compact[:24] if compact else '这个问题'

    if _is_network_query(user_message):
        return (
            '\n\n你可能还想问：\n'
            '1. 这个结论对应的数据来源和更新时间分别是什么？\n'
            '2. 能否按城市/时间范围再细化一次结果？\n'
            '3. 如果数据冲突，应该以哪个来源为准？'
        )

    if any(token in lowered for token in ('代码', 'bug', '报错', 'python', 'java', 'js', 'api', 'sql', 'debug')):
        return (
            '\n\n你可能还想问：\n'
            '1. 这个问题的根因可以怎么快速定位？\n'
            '2. 能给一个最小可复现示例和修复代码吗？\n'
            '3. 修复后应补哪些测试来防止回归？'
        )

    if any(token in lowered for token in ('方案', '计划', '设计', '架构', 'prd', '需求', 'roadmap')):
        return (
            '\n\n你可能还想问：\n'
            '1. 这个方案的优先级和里程碑应该怎么拆？\n'
            '2. 实施过程中最大的风险点是什么，怎么规避？\n'
            '3. 用什么指标判断这次改动是否成功？'
        )

    return (
        '\n\n你可能还想问：\n'
        f'1. 这个问题里最关键的约束条件是什么？（{topic}）\n'
        f'2. 如果要马上落地，第一步最推荐做什么？（{topic}）\n'
        f'3. 有没有更省成本或更稳妥的替代方案？（{topic}）'
    )


def _build_follow_up_block_from_list(questions: list[str]) -> str:
    lines = ['\n\n你可能还想问：']
    for idx, item in enumerate(questions[:3], start=1):
        lines.append(f'{idx}. {item}')
    return '\n'.join(lines)


GREETING_HINTS = {
    'hi',
    'hello',
    'hey',
    '你好',
    '您好',
    '在吗',
    '在不在',
    '早',
    '早上好',
    '晚上好',
    'yo',
}


def _should_append_followups(user_message: str, answer: str) -> bool:
    compact = ' '.join(user_message.strip().split()).lower()
    if not compact:
        return False
    if compact in GREETING_HINTS:
        return False
    if len(compact) <= 4:
        return False
    if len(compact.split()) <= 1 and len(compact) < 8:
        return False
    if '有什么我可以帮助你的吗' in answer:
        return False
    return True


def _fallback_follow_up_questions(user_message: str) -> list[str]:
    block = _build_follow_up_block(user_message)
    candidates: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith(('1. ', '2. ', '3. ')):
            candidates.append(stripped[3:].strip())
    return candidates[:3]


def _termination_notice(reason: str) -> str:
    if reason == 'thinking_timeout':
        return '（系统提示：思考过程耗时过长，已自动终止重复推理并给出当前可用结果。）'
    if reason == 'thinking_guard_triggered':
        return '（系统提示：检测到思考内容重复或过长，已自动终止重复推理并给出当前可用结果。）'
    return ''


def _glm_web_search_tools() -> list[dict]:
    return [
        {
            'type': 'web_search',
            'web_search': {
                'enable': 'True',
                'search_result': 'True',
            },
        }
    ]


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
        supports_web_search = self._supports_web_search(provider_name)
        resolved_tools = self._resolve_tools(provider_name=provider_name)
        web_search_required = _is_network_query(message) and not supports_web_search

        await self.message_repo.create(
            conversation_id=session_id,
            role='user',
            content=message,
            provider=None,
            model=None,
            request_id=request_id,
        )

        if web_search_required:
            warning_message = await self._append_follow_up_questions(
                answer=_unsupported_web_search_message(),
                user_message=message,
                provider_name=provider_name,
                model_name=model_name,
                conversation_id=session_id,
                request_id=request_id,
            )
            yield {'event': 'message.start', 'data': {'request_id': request_id}}
            yield {'event': 'message.delta', 'data': {'delta': warning_message}}
            await self.message_repo.create(
                conversation_id=session_id,
                role='assistant',
                content=warning_message,
                provider=provider_name,
                model=model_name,
                request_id=request_id,
            )
            conv.last_active_at = utcnow()
            conv.updated_at = utcnow()
            await self.db.commit()
            yield {
                'event': 'message.end',
                'data': {
                    'text': warning_message,
                    'thinking': '',
                    'request_id': request_id,
                    'thinking_guard_triggered': False,
                },
            }
            return

        context_messages = await self._build_context_messages(
            conv,
            current_user_message=message,
            web_search_enabled=supports_web_search,
        )
        req = ChatRequest(
            provider=provider_name,
            model=model_name,
            messages=context_messages,
            temperature=temperature,
            top_p=self.settings.generation_top_p,
            repeat_penalty=self.settings.generation_repeat_penalty if provider_name == 'ollama' else None,
            max_tokens=max_tokens,
            stream=True,
            enable_thinking=self._resolve_enable_thinking(provider_name, enable_thinking),
            tools=resolved_tools,
        )

        yield {'event': 'message.start', 'data': {'request_id': request_id}}
        chunks: list[str] = []
        thinking_chunks: list[str] = []
        thinking_guard = ThinkingLoopGuard(
            enabled=self.settings.enable_thinking_loop_guard and provider_name in {'ollama', 'glm'},
            max_chars=self.settings.thinking_loop_max_chars,
            repeat_window=self.settings.thinking_loop_repeat_window,
            repeat_threshold=self.settings.thinking_loop_repeat_threshold,
        )
        started_at = monotonic()
        termination_reason = 'model_completed'
        async for chunk in self.provider_router.stream_chat(req, conversation_id=session_id, request_id=request_id):
            if thinking_guard.enabled and monotonic() - started_at > self.settings.thinking_loop_max_seconds:
                termination_reason = 'thinking_timeout'
                break

            if chunk.thinking:
                filtered = thinking_guard.filter_delta(chunk.thinking)
                if filtered:
                    thinking_chunks.append(filtered)
                    yield {'event': 'message.thinking', 'data': {'delta': filtered}}
                elif thinking_guard.triggered:
                    termination_reason = 'thinking_guard_triggered'
                    break
            if chunk.delta:
                chunks.append(chunk.delta)
                yield {'event': 'message.delta', 'data': {'delta': chunk.delta}}
            if chunk.finish_reason:
                termination_reason = chunk.finish_reason
                break

        assistant_text = ''.join(chunks).strip()
        notice = _termination_notice(termination_reason)
        if notice:
            assistant_text = f'{assistant_text}\n\n{notice}'.strip()
        final_text = await self._append_follow_up_questions(
            answer=assistant_text,
            user_message=message,
            provider_name=provider_name,
            model_name=model_name,
            conversation_id=session_id,
            request_id=request_id,
        )
        await self.message_repo.create(
            conversation_id=session_id,
            role='assistant',
            content=final_text,
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
            'data': {
                'text': final_text,
                'thinking': ''.join(thinking_chunks),
                'request_id': request_id,
                'thinking_guard_triggered': thinking_guard.triggered,
                'termination_reason': termination_reason,
            },
        }

    async def _build_context_messages(
        self,
        conv,
        current_user_message: str,
        web_search_enabled: bool,
    ) -> list[ChatMessage]:
        latest_snapshot = await self.memory_repo.latest(conv.id)
        summary_text = latest_snapshot.summary_text if latest_snapshot else None

        recent = await self.message_repo.list(conv.id, limit=conv.memory_window_size)
        recent_messages = [ChatMessage(role=m.role, content=m.content) for m in recent]

        if not recent_messages or recent_messages[-1].role != 'user' or recent_messages[-1].content != current_user_message:
            recent_messages.append(ChatMessage(role='user', content=current_user_message))

        time_context = get_current_datetime(self.settings.app_timezone)
        runtime_prompt_lines = [
            f"Current datetime ({time_context['timezone']}): {time_context['iso_datetime']}",
            f"Current date ({time_context['timezone']}): {time_context['iso_date']} ({time_context['weekday']})",
            'When user asks about today/now/date/time, never guess and always answer from this runtime context.',
        ]
        if web_search_enabled:
            runtime_prompt_lines.append(
                'Web search is enabled. For facts that depend on current events (weather/news/prices), prefer web search instead of memory.'
            )

        system_prompt_sections: list[str] = []
        if conv.system_prompt:
            system_prompt_sections.append(conv.system_prompt)
        system_prompt_sections.append('\n'.join(runtime_prompt_lines))
        merged_system_prompt = '\n\n'.join(system_prompt_sections)

        return self.context_builder.build(
            system_prompt=merged_system_prompt,
            summary_text=summary_text,
            recent_messages=recent_messages,
        )

    @staticmethod
    def _supports_web_search(provider_name: str) -> bool:
        return provider_name == 'glm'

    def _resolve_tools(self, *, provider_name: str) -> list[dict] | None:
        if not self._supports_web_search(provider_name):
            return None
        return _glm_web_search_tools()

    @staticmethod
    def _resolve_enable_thinking(provider_name: str, enable_thinking: bool | None) -> bool:
        if provider_name not in {'ollama', 'glm'}:
            return False
        if enable_thinking is None:
            return True
        return enable_thinking

    @staticmethod
    def _sanitize_follow_up_question(text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r'^\d+[\.\)\-:\s]+', '', cleaned)
        cleaned = re.sub(r'^[\-*]+\s*', '', cleaned)
        cleaned = cleaned.strip(' "\'')
        if not cleaned:
            return ''
        if not cleaned.endswith(('？', '?')):
            cleaned += '？'
        return cleaned

    @staticmethod
    def _parse_follow_up_json(text: str) -> list[str]:
        payload = text.strip()
        candidates: list[str] = []

        for raw in (payload, re.sub(r'```(?:json)?|```', '', payload).strip()):
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, dict):
                values = parsed.get('questions')
                if isinstance(values, list):
                    candidates = [str(item) for item in values]
                    break
            if isinstance(parsed, list):
                candidates = [str(item) for item in parsed]
                break

        if not candidates:
            return []

        normalized: list[str] = []
        seen = set()
        for item in candidates:
            cleaned = ChatService._sanitize_follow_up_question(item)
            if not cleaned:
                continue
            if cleaned in seen:
                continue
            normalized.append(cleaned)
            seen.add(cleaned)
            if len(normalized) >= 3:
                break
        return normalized

    async def _generate_follow_up_questions_by_model(
        self,
        *,
        user_message: str,
        answer: str,
        provider_name: str,
        model_name: str,
        conversation_id: str,
        request_id: str,
    ) -> list[str]:
        helper_prompt = (
            '你是追问推荐助手。请基于用户问题与助手回答内容，生成3个高质量追问。'
            '要求：具体、有价值、避免空泛，不要重复原问题。'
            '严格输出 JSON：{"questions":["...","...","..."]}，不要输出任何其他文本。'
        )
        req = ChatRequest(
            provider=provider_name,
            model=model_name,
            messages=[
                ChatMessage(role='system', content=helper_prompt),
                ChatMessage(
                    role='user',
                    content=(
                        f'用户问题：{user_message}\n\n'
                        f'助手回答：{answer}\n\n'
                        '请给出3个建议追问。'
                    ),
                ),
            ],
            temperature=0.2,
            top_p=0.9,
            stream=False,
            enable_thinking=False,
            tools=None,
        )
        try:
            resp = await self.provider_router.chat(
                req,
                conversation_id=conversation_id,
                request_id=f'{request_id}-followup',
            )
        except Exception:
            return []
        return self._parse_follow_up_json(resp.text)

    async def _append_follow_up_questions(
        self,
        *,
        answer: str,
        user_message: str,
        provider_name: str,
        model_name: str,
        conversation_id: str,
        request_id: str,
    ) -> str:
        base = answer.strip()
        if not _should_append_followups(user_message, base):
            return base

        model_followups = await self._generate_follow_up_questions_by_model(
            user_message=user_message,
            answer=base,
            provider_name=provider_name,
            model_name=model_name,
            conversation_id=conversation_id,
            request_id=request_id,
        )
        follow_ups = model_followups or _fallback_follow_up_questions(user_message)
        if not follow_ups:
            return base

        follow_up_block = _build_follow_up_block_from_list(follow_ups)
        if not base:
            return follow_up_block.strip()
        return f'{base}{follow_up_block}'

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

from app.providers.base import ChatMessage, ChatRequest

PROMPT = (
    '你是会话记忆压缩器。请将旧摘要与新增对话整合为新的简洁摘要。'
    '保留用户目标、偏好、关键事实、未完成事项，删除寒暄和重复。输出200到600字中文。'
)


class Summarizer:
    def __init__(self, provider_router):
        self.provider_router = provider_router

    async def summarize(
        self,
        *,
        provider: str,
        model: str,
        old_summary: str | None,
        new_messages: list[ChatMessage],
        conversation_id: str,
        request_id: str,
    ) -> str:
        content_parts = [f"旧摘要:\n{old_summary or '无'}\n", '新增消息:\n']
        for msg in new_messages:
            content_parts.append(f'- {msg.role}: {msg.content}')

        req = ChatRequest(
            provider=provider,
            model=model,
            messages=[
                ChatMessage(role='system', content=PROMPT),
                ChatMessage(role='user', content='\n'.join(content_parts)),
            ],
            temperature=0.2,
            stream=False,
        )
        resp = await self.provider_router.chat(req, conversation_id=conversation_id, request_id=request_id)
        return resp.text.strip()

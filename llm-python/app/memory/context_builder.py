from app.providers.base import ChatMessage


class ContextBuilder:
    def __init__(self, max_context_chars: int):
        self.max_context_chars = max_context_chars

    def build(
        self,
        *,
        system_prompt: str | None,
        summary_text: str | None,
        recent_messages: list[ChatMessage],
    ) -> list[ChatMessage]:
        final: list[ChatMessage] = []
        if system_prompt:
            final.append(ChatMessage(role='system', content=system_prompt))
        if summary_text:
            final.append(ChatMessage(role='system', content=f'历史会话摘要：{summary_text}'))
        final.extend(recent_messages)

        total_chars = sum(len(m.content) for m in final)
        while total_chars > self.max_context_chars and len(final) > 2:
            popped = final.pop(2)
            total_chars -= len(popped.content)
        return final

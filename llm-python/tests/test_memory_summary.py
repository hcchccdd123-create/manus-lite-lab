from app.memory.context_builder import ContextBuilder
from app.providers.base import ChatMessage


def test_context_builder_limits_chars():
    builder = ContextBuilder(max_context_chars=20)
    messages = [
        ChatMessage(role='user', content='1234567890'),
        ChatMessage(role='assistant', content='abcdefghij'),
        ChatMessage(role='user', content='xyzxyzxyzx'),
    ]
    out = builder.build(system_prompt='sys', summary_text='sum', recent_messages=messages)
    assert out[0].role == 'system'
    assert out[1].role == 'system'
    assert sum(len(m.content) for m in out) <= 20

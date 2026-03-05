from app.memory.policy import MemoryPolicy


def test_memory_policy_defaults():
    policy = MemoryPolicy(window_size=12, summary_trigger_messages=20, max_context_chars=16000)
    assert policy.window_size == 12
    assert policy.summary_trigger_messages == 20

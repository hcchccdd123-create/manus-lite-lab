from app.services.thinking_loop_guard import ThinkingLoopGuard


def test_guard_passes_normal_thinking_deltas():
    guard = ThinkingLoopGuard(
        enabled=True,
        max_chars=1000,
        repeat_window=8,
        repeat_threshold=4,
    )

    deltas = [
        'Let me break this down into three steps and verify assumptions.',
        'First, I need to inspect the user intent and map it to system constraints.',
        'Second, I should draft an implementation outline with clear boundaries.',
    ]
    filtered = [guard.filter_delta(item) for item in deltas]

    assert filtered == deltas
    assert guard.triggered is False


def test_guard_blocks_repeated_thinking_loop():
    guard = ThinkingLoopGuard(
        enabled=True,
        max_chars=5000,
        repeat_window=12,
        repeat_threshold=4,
    )
    repeated = 'No, providing code examples is fine as long as it is generic and safe.'

    outputs = [guard.filter_delta(repeated) for _ in range(5)]

    assert outputs[:3] == [repeated, repeated, repeated]
    assert outputs[3] == ''
    assert outputs[4] == ''
    assert guard.triggered is True


def test_guard_blocks_when_thinking_chars_too_large():
    guard = ThinkingLoopGuard(
        enabled=True,
        max_chars=80,
        repeat_window=8,
        repeat_threshold=4,
    )

    first = 'This chunk is still acceptable and should pass through.'
    second = 'This second chunk pushes the accumulated thinking text over the max chars budget.'

    assert guard.filter_delta(first) == first
    assert guard.filter_delta(second) == ''
    assert guard.triggered is True

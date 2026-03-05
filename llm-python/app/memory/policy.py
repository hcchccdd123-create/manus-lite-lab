from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryPolicy:
    window_size: int
    summary_trigger_messages: int
    max_context_chars: int

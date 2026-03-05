from collections import deque
import re

_WS_PATTERN = re.compile(r'\s+')


def _normalize(text: str) -> str:
    collapsed = _WS_PATTERN.sub(' ', text).strip().lower()
    return collapsed


def _fingerprint(normalized_text: str, limit: int = 220) -> str:
    if len(normalized_text) <= limit:
        return normalized_text
    return f'{normalized_text[:120]}|{normalized_text[-80:]}'


class ThinkingLoopGuard:
    def __init__(
        self,
        *,
        enabled: bool,
        max_chars: int,
        repeat_window: int,
        repeat_threshold: int,
        min_segment_chars: int = 24,
    ):
        self.enabled = enabled
        self.max_chars = max_chars
        self.repeat_window = repeat_window
        self.repeat_threshold = repeat_threshold
        self.min_segment_chars = min_segment_chars

        self._total_chars = 0
        self._triggered = False
        self._history: deque[str] = deque(maxlen=repeat_window)

    @property
    def triggered(self) -> bool:
        return self._triggered

    def filter_delta(self, delta: str) -> str:
        if not delta or not self.enabled:
            return delta

        self._total_chars += len(delta)
        if self._total_chars > self.max_chars:
            self._triggered = True
            return ''

        normalized = _normalize(delta)
        if len(normalized) < self.min_segment_chars:
            return delta

        fp = _fingerprint(normalized)
        self._history.append(fp)
        repeats = sum(1 for item in self._history if item == fp)
        if repeats >= self.repeat_threshold:
            self._triggered = True
            return ''

        return delta

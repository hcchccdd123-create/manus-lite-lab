import time
import uuid


def _prefix(prefix: str) -> str:
    millis = int(time.time() * 1000)
    suffix = uuid.uuid4().hex[:12]
    return f'{prefix}_{millis:x}{suffix}'


def new_session_id() -> str:
    return _prefix('sess')


def new_message_id() -> str:
    return _prefix('msg')


def new_request_id() -> str:
    return _prefix('req')


def new_log_id() -> str:
    return _prefix('log')


def new_snapshot_id() -> str:
    return _prefix('mem')

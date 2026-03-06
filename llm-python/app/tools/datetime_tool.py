from datetime import datetime

from app.utils.time import resolve_timezone


def get_current_datetime(timezone_name: str) -> dict:
    tz = resolve_timezone(timezone_name)
    now = datetime.now(tz)
    return {
        'tool_name': 'get_current_datetime',
        'timezone': str(tz),
        'iso_datetime': now.isoformat(),
        'iso_date': now.date().isoformat(),
        'weekday': now.strftime('%A'),
        'unix_timestamp': int(now.timestamp()),
    }

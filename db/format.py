from datetime import datetime, timezone


def parse_iso_utc(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_timer_hms(elapsed_seconds: int) -> str:
    if elapsed_seconds < 0:
        elapsed_seconds = 0
    hours, remainder = divmod(int(elapsed_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_duration_short(seconds: float | int | None) -> str:
    if not seconds or seconds <= 0:
        return "—"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes = remainder // 60
    if hours:
        return f"{hours}h {minutes}min"
    if minutes:
        return f"{minutes}min"
    return f"{total}s"


def format_relative_minutes(reference: datetime, now: datetime) -> str:
    delta_minutes = int((now - reference).total_seconds() // 60)
    if delta_minutes < 1:
        return "ultima: poco fa"
    if delta_minutes < 60:
        return f"ultima: {delta_minutes} min fa"
    hours = delta_minutes // 60
    minutes = delta_minutes % 60
    if minutes:
        return f"ultima: {hours}h {minutes}min fa"
    return f"ultima: {hours}h fa"

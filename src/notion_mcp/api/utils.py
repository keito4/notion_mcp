import pytz
from datetime import datetime, timezone
from ..config.settings import get_settings

settings = get_settings()
JST = pytz.timezone(settings.tz)


def to_utc_date_str(dt: datetime) -> str:
    """Convert a datetime to its UTC ISO8601 string representation."""
    return dt.astimezone(timezone.utc).isoformat()

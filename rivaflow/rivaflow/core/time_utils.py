"""Timezone-safe UTC helpers.

``datetime.utcnow()`` is deprecated in Python 3.12+.  The replacement,
``datetime.now(timezone.utc)``, returns a tz-aware datetime whose
``.isoformat()`` appends ``+00:00`` — which breaks SQL string
comparisons against naive timestamps already stored in the DB.

This module provides a drop-in ``utcnow()`` that stays **naive UTC**,
plus ``user_today()`` for computing the current date in the user's
local timezone.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


def utcnow() -> datetime:
    """Return the current UTC time as a **naive** datetime (no tzinfo)."""
    return datetime.now(UTC).replace(tzinfo=None)


def user_today(timezone: str | None = None) -> date:
    """Return today's date in the user's timezone (defaults to UTC)."""
    tz = ZoneInfo(timezone) if timezone else UTC
    return datetime.now(tz).date()

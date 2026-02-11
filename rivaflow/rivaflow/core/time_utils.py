"""Timezone-safe UTC helpers.

``datetime.utcnow()`` is deprecated in Python 3.12+.  The replacement,
``datetime.now(timezone.utc)``, returns a tz-aware datetime whose
``.isoformat()`` appends ``+00:00`` — which breaks SQL string
comparisons against naive timestamps already stored in the DB.

This module provides a drop-in ``utcnow()`` that stays **naive UTC**.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current UTC time as a **naive** datetime (no tzinfo)."""
    return datetime.now(UTC).replace(tzinfo=None)

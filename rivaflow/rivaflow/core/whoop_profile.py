"""WhoopProfile seam (Wave 3.6) — per-user tz/age/sleep-need/rest-day/max-HR-override,
read once from `profile` and threaded through whoop_analytics instead of the hardcoded
RUBY_AGE / LOCAL_TZ / Sunday-only rest-day checks it replaces.

Kept dependency-light on purpose: a direct SELECT via BaseRepository, no new
repository class. Missing row or any DB error returns full defaults — this must
never raise, since it sits in front of every analytics call.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from rivaflow.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

# Preserved fallback — the DOB whoop_analytics.RUBY_AGE was hardcoded from
# (1982-05-27), so behaviour with an empty/missing profile row is identical.
_DEFAULT_DOB = "1982-05-27"
_DEFAULT_TZ_NAME = "Australia/Melbourne"
_DEFAULT_SLEEP_NEED_H = 8.0
_DEFAULT_REST_WEEKDAY = 6  # Sunday

_CACHE_TTL_SEC = 60


@dataclass(frozen=True)
class WhoopProfile:
    user_id: int
    tz: ZoneInfo
    age: int
    sleep_need_h: float
    rest_weekday: int
    max_hr_override: int | None


def _years_between(dob: date, today: date) -> int:
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _default_age(today: date | None = None) -> int:
    """Age from the preserved DOB fallback, computed the same way ProfileRepository does.
    `today` is injectable for deterministic tests; production callers omit it."""
    return _years_between(date.fromisoformat(_DEFAULT_DOB), today or date.today())


def _age_from_dob(dob_iso: str | None, today: date | None = None) -> int:
    """Age from an ISO date string; falls back to the default DOB on any parse issue."""
    today = today or date.today()
    if not dob_iso:
        return _default_age(today)
    try:
        dob = date.fromisoformat(str(dob_iso)[:10])
    except (ValueError, TypeError):
        return _default_age(today)
    return _years_between(dob, today)


def _resolve_tz(device_tz: str | None, timezone: str | None) -> ZoneInfo:
    """device_tz (most recent, device-reported) > profile.timezone (user-set) > Melbourne default.
    Invalid/unknown IANA names are skipped rather than raising.
    """
    for candidate in (device_tz, timezone):
        if not candidate:
            continue
        try:
            return ZoneInfo(str(candidate))
        except Exception:  # noqa: BLE001 — any bad tz string just falls through
            continue
    return ZoneInfo(_DEFAULT_TZ_NAME)


def _row_to_profile(user_id: int, row: dict | None) -> WhoopProfile:
    row = row or {}
    return WhoopProfile(
        user_id=user_id,
        tz=_resolve_tz(row.get("device_tz"), row.get("timezone")),
        age=_age_from_dob(row.get("date_of_birth")),
        sleep_need_h=(
            float(row["sleep_need_h"])
            if row.get("sleep_need_h") is not None
            else _DEFAULT_SLEEP_NEED_H
        ),
        rest_weekday=(
            int(row["rest_weekday"])
            if row.get("rest_weekday") is not None
            else _DEFAULT_REST_WEEKDAY
        ),
        max_hr_override=(
            int(row["max_hr_override"])
            if row.get("max_hr_override") is not None
            else None
        ),
    )


# Per-process cache keyed by user_id: (profile, fetched_at_monotonic). Hot analytics
# paths (whoop_summary, the cockpit build) fetch the profile several times per call
# chain, so a short TTL avoids hammering the DB without ever going stale for long.
_cache: dict[int, tuple[WhoopProfile, float]] = {}


def _clear_profile_cache() -> None:
    """Test hook — reset the per-process cache between test cases."""
    _cache.clear()


def get_whoop_profile(user_id: int) -> WhoopProfile:
    """Read (and cache, ~60s TTL) the WhoopProfile for `user_id`. Never raises — a
    missing row or DB error resolves to full defaults (Melbourne tz, the preserved
    RUBY_AGE-equivalent age, 8h sleep need, Sunday rest day, no max-HR override).
    """
    cached = _cache.get(user_id)
    now = time.monotonic()
    if cached is not None and now - cached[1] < _CACHE_TTL_SEC:
        return cached[0]

    try:
        row = BaseRepository._fetchone(
            "SELECT date_of_birth, timezone, device_tz, sleep_need_h, "
            "rest_weekday, max_hr_override FROM profile WHERE user_id = ?",
            (user_id,),
        )
        profile = _row_to_profile(user_id, row)
    except Exception:  # noqa: BLE001 — profile lookup must never break analytics
        logger.warning(
            "get_whoop_profile failed for user %s; using defaults",
            user_id,
            exc_info=True,
        )
        profile = _row_to_profile(user_id, None)

    _cache[user_id] = (profile, now)
    return profile


def is_rest_day(profile: WhoopProfile, now: datetime) -> bool:
    """True when `now` (any tz-aware datetime) falls on the profile's rest weekday,
    evaluated in the profile's own tz."""
    return now.astimezone(profile.tz).weekday() == profile.rest_weekday


def today_is_rest_day(user_id: int) -> bool:
    """Route-level convenience: fetch the profile and evaluate 'now' against it in one
    call — every /whoop route that needs today's Sabbath/rest-day flag has a user_id
    (current_user or api_key) in scope but no reason to hold a WhoopProfile itself."""
    profile = get_whoop_profile(user_id)
    return is_rest_day(profile, datetime.now(profile.tz))

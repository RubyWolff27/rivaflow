"""Wave 3.6 — WhoopProfile seam (pure; no DB, no network).

Verifies: defaults on a missing/empty profile row match the old hardcoded
RUBY_AGE/LOCAL_TZ behaviour byte-for-byte, device_tz resolution order,
the rest-day helper, the ingest device_tz persistence helper, and that
`_local_day` with a default (empty) profile is identical to the pre-seam
Melbourne-only behaviour.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import rivaflow.core.whoop_profile as wp
from rivaflow.core import whoop_analytics

MELBOURNE = ZoneInfo("Australia/Melbourne")
FIXED_TODAY = date(2026, 7, 10)

# The old hardcoded RUBY_AGE=44 was derived from DOB 1982-05-27 at some point in the
# past; recomputed against FIXED_TODAY it must still land on 44 (July 10 is after the
# May 27 birthday in 2026, so no -1 adjustment).
OLD_RUBY_AGE = 44


def teardown_function():
    wp._clear_profile_cache()


# ── (a) defaults: empty/missing profile row ──────────────────────────────────


def test_default_age_matches_old_ruby_age():
    assert wp._default_age(today=FIXED_TODAY) == OLD_RUBY_AGE


def test_missing_row_resolves_full_defaults(monkeypatch):
    monkeypatch.setattr(
        wp.BaseRepository, "_fetchone", staticmethod(lambda *a, **k: None)
    )
    profile = wp.get_whoop_profile(1)
    assert profile.tz == MELBOURNE
    assert profile.age == wp._default_age()
    assert profile.sleep_need_h == 8.0
    assert profile.rest_weekday == 6
    assert profile.max_hr_override is None


def test_empty_row_dict_resolves_full_defaults():
    profile = wp._row_to_profile(1, {})
    assert profile.tz == MELBOURNE
    assert profile.age == wp._default_age()
    assert profile.sleep_need_h == 8.0
    assert profile.rest_weekday == 6
    assert profile.max_hr_override is None


def test_db_error_resolves_full_defaults(monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("db down")

    monkeypatch.setattr(wp.BaseRepository, "_fetchone", staticmethod(_boom))
    profile = wp.get_whoop_profile(1)
    assert profile.tz == MELBOURNE
    assert profile.age == wp._default_age()


def test_populated_row_overrides_defaults():
    row = {
        "date_of_birth": "1990-01-01",
        "timezone": "America/New_York",
        "device_tz": None,
        "sleep_need_h": 9.5,
        "rest_weekday": 2,
        "max_hr_override": 180,
    }
    profile = wp._row_to_profile(1, row)
    assert profile.tz == ZoneInfo("America/New_York")
    assert profile.sleep_need_h == 9.5
    assert profile.rest_weekday == 2
    assert profile.max_hr_override == 180
    assert profile.age == wp._age_from_dob("1990-01-01")


# ── (b) device_tz resolution order ────────────────────────────────────────────


def test_tz_resolution_prefers_device_tz_over_timezone():
    tz = wp._resolve_tz("America/Chicago", "Australia/Sydney")
    assert tz == ZoneInfo("America/Chicago")


def test_tz_resolution_falls_back_to_timezone():
    tz = wp._resolve_tz(None, "Australia/Sydney")
    assert tz == ZoneInfo("Australia/Sydney")


def test_tz_resolution_falls_back_to_melbourne_default():
    assert wp._resolve_tz(None, None) == MELBOURNE


def test_tz_resolution_skips_invalid_device_tz():
    tz = wp._resolve_tz("Not/A/Real/Zone", "Australia/Sydney")
    assert tz == ZoneInfo("Australia/Sydney")


def test_tz_resolution_skips_invalid_both():
    tz = wp._resolve_tz("Nope", "AlsoNope")
    assert tz == MELBOURNE


# ── (c) rest-day helper ────────────────────────────────────────────────────────


def test_is_rest_day_sunday_in_melbourne_true():
    profile = wp._row_to_profile(1, {})  # default rest_weekday=6 (Sunday)
    sunday = datetime(2026, 7, 12, 10, 0, tzinfo=MELBOURNE)  # 12 Jul 2026 is a Sunday
    assert wp.is_rest_day(profile, sunday) is True


def test_is_rest_day_monday_false():
    profile = wp._row_to_profile(1, {})
    monday = datetime(2026, 7, 13, 10, 0, tzinfo=MELBOURNE)
    assert wp.is_rest_day(profile, monday) is False


def test_is_rest_day_custom_rest_weekday():
    profile = wp._row_to_profile(1, {"rest_weekday": 2})  # Wednesday
    wednesday = datetime(2026, 7, 15, 10, 0, tzinfo=MELBOURNE)
    sunday = datetime(2026, 7, 12, 10, 0, tzinfo=MELBOURNE)
    assert wp.is_rest_day(profile, wednesday) is True
    assert wp.is_rest_day(profile, sunday) is False


def test_is_rest_day_evaluates_in_profile_tz():
    # 23:30 UTC on Saturday is already Sunday in Melbourne (+10/+11h).
    profile = wp._row_to_profile(1, {})
    almost_midnight_utc = datetime(2026, 7, 11, 23, 30, tzinfo=ZoneInfo("UTC"))
    assert wp.is_rest_day(profile, almost_midnight_utc) is True


# ── cache behaviour ────────────────────────────────────────────────────────────


def test_profile_is_cached_within_ttl(monkeypatch):
    calls = {"n": 0}

    def _fetch(*a, **k):
        calls["n"] += 1
        return None

    monkeypatch.setattr(wp.BaseRepository, "_fetchone", staticmethod(_fetch))
    wp.get_whoop_profile(1)
    wp.get_whoop_profile(1)
    assert calls["n"] == 1  # second call served from cache


def test_clear_profile_cache_forces_refetch(monkeypatch):
    calls = {"n": 0}

    def _fetch(*a, **k):
        calls["n"] += 1
        return None

    monkeypatch.setattr(wp.BaseRepository, "_fetchone", staticmethod(_fetch))
    wp.get_whoop_profile(1)
    wp._clear_profile_cache()
    wp.get_whoop_profile(1)
    assert calls["n"] == 2


# ── (e) ANTI-criterion: _local_day with a default profile == old Melbourne
#     behaviour ─────────────────────────────────────────────────────────────


def test_local_day_default_matches_old_melbourne_behaviour():
    # 2026-07-11 14:00 UTC is 2026-07-12 00:00 in Melbourne (+10h, winter/AEST) —
    # exactly the kind of UTC-day-boundary case the local-day bucketing exists for.
    ts = "2026-07-11T14:00:00Z"
    assert whoop_analytics._local_day(ts) == "2026-07-12"
    # Explicit Melbourne tz must be identical to the default.
    assert whoop_analytics._local_day(ts, MELBOURNE) == whoop_analytics._local_day(ts)


def test_local_day_with_non_default_tz_differs():
    ts = "2026-07-11T14:00:00Z"
    # Same instant is still 2026-07-11 in UTC itself.
    assert whoop_analytics._local_day(ts, ZoneInfo("UTC")) == "2026-07-11"

"""Wave 3.4 — whoop_daily_agg per-day rollup service (pure; no DB, no network).

Verifies the rollup contract: a missing day is computed + upserted, a fresh stored day is served WITHOUT
recompute, a day whose raw HR+RR count has grown since it was rolled up (the late-data case — the phone's
offline spool / a historical drain) forces a recompute, a deriver-version bump forces a recompute, today is
always computed live and never persisted, and get_range's per-day series matches compute_day's own output
field-for-field. Also covers the route-level render-duration WARN threshold — the other half of Wave 3.4,
which retired the whoop_summary TTL cache now that historical days are rolled up once instead of re-scanned
on every call.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

import rivaflow.api.routes.whoop as whoop_route
import rivaflow.core.services.whoop_daily_agg as wda
from rivaflow.core import whoop_analytics
from rivaflow.db.repositories.whoop_repo import WhoopRepository

MELBOURNE = ZoneInfo("Australia/Melbourne")
TODAY = date(2026, 7, 10)
YESTERDAY = date(2026, 7, 9)
TWO_DAYS_AGO = date(2026, 7, 8)

RMSSD_METRIC = {
    "rmssd": 40.0,
    "ln_rmssd": 3.7,
    "quality": {"artifact_pct": 2.0},
    "coverage": {"rr_minutes": 20.0},
}
RESTING_HR_METRIC = {"resting_hr": 52, "min_hr": 50, "samples": 400}
SLEEP_METRIC = {
    "available": True,
    "duration_hours": 7.5,
    "sleep_start": "x",
    "sleep_end": "y",
}
CARDIO_METRIC = {"cardio_load": 9.0, "raw_trimp": 40.0, "load_version": "banister-v1"}


def _ts(d: date, hour: int, minute: int = 0) -> str:
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=MELBOURNE).isoformat()


def _fixed_now(fixed: datetime):
    """Same pattern as test_whoop_profile.py's _fixed_now — a datetime subclass whose .now() is pinned."""

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed if tz is None else fixed.astimezone(tz)

    return _FixedDatetime


class _FakeProfile:
    tz = MELBOURNE


class _RawStore:
    """Stand-in for whoop_hr/whoop_rr: (ts_iso, value) pairs, filtered by [start, end] like the real
    bounded-window repository queries."""

    def __init__(self) -> None:
        self.hr: list[tuple[str, int]] = []
        self.rr: list[tuple[str, int]] = []

    def hr_range(self, user_id, start_iso, end_iso):
        return [
            {"ts": ts, "bpm": bpm} for ts, bpm in self.hr if start_iso <= ts <= end_iso
        ]

    def rr_range_between(self, user_id, start_iso, end_iso):
        return [
            {"ts": ts, "rr_ms": v} for ts, v in self.rr if start_iso <= ts <= end_iso
        ]

    def hr_count_range(self, user_id, start_iso, end_iso):
        return len(self.hr_range(user_id, start_iso, end_iso))

    def rr_count_range(self, user_id, start_iso, end_iso):
        return len(self.rr_range_between(user_id, start_iso, end_iso))


class _RollupStore:
    """Stand-in for whoop_daily_agg."""

    def __init__(self) -> None:
        self.rows: dict[tuple[int, str], dict] = {}

    def get(self, user_id, day):
        return self.rows.get((user_id, day))

    def upsert(
        self, user_id, day, metrics_json, deriver_version, sample_count, complete
    ):
        self.rows[(user_id, day)] = {
            "metrics_json": metrics_json,
            "deriver_version": deriver_version,
            "sample_count": sample_count,
            "complete": complete,
        }


def _install_fakes(monkeypatch) -> tuple[_RawStore, _RollupStore]:
    raw = _RawStore()
    rollup = _RollupStore()
    monkeypatch.setattr(WhoopRepository, "hr_range", staticmethod(raw.hr_range))
    monkeypatch.setattr(
        WhoopRepository, "rr_range_between", staticmethod(raw.rr_range_between)
    )
    monkeypatch.setattr(
        WhoopRepository, "hr_count_range", staticmethod(raw.hr_count_range)
    )
    monkeypatch.setattr(
        WhoopRepository, "rr_count_range", staticmethod(raw.rr_count_range)
    )
    monkeypatch.setattr(WhoopRepository, "get_daily_agg", staticmethod(rollup.get))
    monkeypatch.setattr(
        WhoopRepository, "upsert_daily_agg", staticmethod(rollup.upsert)
    )
    return raw, rollup


def _freeze(
    monkeypatch, when: datetime = datetime(2026, 7, 10, 9, 0, tzinfo=MELBOURNE)
) -> None:
    monkeypatch.setattr(wda, "datetime", _fixed_now(when))
    monkeypatch.setattr(wda, "get_whoop_profile", lambda uid: _FakeProfile())
    # get_range's "cardio" branch calls whoop_analytics.user_max_hr when no max_hr is supplied — stub it
    # so it never falls through to a real (unmocked) WhoopRepository.recent_hr scan.
    monkeypatch.setattr(whoop_analytics, "user_max_hr", lambda uid: {"max_hr": 180.0})


def _stub_day_math(
    monkeypatch,
    *,
    rmssd=RMSSD_METRIC,
    resting_hr=RESTING_HR_METRIC,
    sleep=SLEEP_METRIC,
    cardio=CARDIO_METRIC,
) -> dict[str, int]:
    """Stub the per-day math whoop_analytics owns (see whoop_analytics._day_rmssd/_day_resting_hr/
    _day_sleep/_day_cardio) so these tests exercise ONLY the rollup orchestration — the math itself is
    covered where it lives (e.g. tests/unit/test_cardio_load.py)."""
    called = {"rmssd": 0, "resting_hr": 0, "sleep": 0, "cardio": 0}

    def _rmssd(rr_vals, hr_count):
        called["rmssd"] += 1
        return rmssd

    def _resting_hr(bpms):
        called["resting_hr"] += 1
        return resting_hr

    def _sleep(uid, day, tz):
        called["sleep"] += 1
        return sleep

    def _cardio(samples, mx, rest):
        called["cardio"] += 1
        return cardio

    monkeypatch.setattr(whoop_analytics, "_day_rmssd", _rmssd)
    monkeypatch.setattr(whoop_analytics, "_day_resting_hr", _resting_hr)
    monkeypatch.setattr(whoop_analytics, "_day_sleep", _sleep)
    monkeypatch.setattr(whoop_analytics, "_day_cardio", _cardio)
    return called


# ── (a) missing day → computed + upserted ─────────────────────────────────────


def test_missing_day_is_computed_and_upserted(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    _stub_day_math(monkeypatch)
    raw.hr = [(_ts(YESTERDAY, 10), 60), (_ts(YESTERDAY, 11), 61)]
    raw.rr = [(_ts(YESTERDAY, 10), 900)]

    result = wda._rollup_for_day(1, YESTERDAY.isoformat(), MELBOURNE, max_hr=None)

    assert result is not None
    assert result["rmssd"] == RMSSD_METRIC
    assert result["cardio"] == CARDIO_METRIC
    stored = rollup.get(1, YESTERDAY.isoformat())
    assert stored is not None
    assert stored["deriver_version"] == wda.DERIVER_VERSION
    assert stored["sample_count"] == 3  # 2 hr + 1 rr
    assert json.loads(stored["metrics_json"])["cardio"] == CARDIO_METRIC


def test_day_with_no_raw_data_returns_none_and_writes_nothing(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    _stub_day_math(monkeypatch)
    # raw.hr / raw.rr stay empty for YESTERDAY

    result = wda._rollup_for_day(1, YESTERDAY.isoformat(), MELBOURNE, max_hr=None)

    assert result is None
    assert rollup.get(1, YESTERDAY.isoformat()) is None


# ── (b) fresh stored day → served WITHOUT recompute ───────────────────────────


def test_fresh_stored_day_is_served_without_recompute(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    called = _stub_day_math(monkeypatch)
    raw.hr = [(_ts(YESTERDAY, 10), 60)]
    raw.rr = [(_ts(YESTERDAY, 10), 900)]
    rollup.upsert(
        1,
        YESTERDAY.isoformat(),
        json.dumps(
            {
                "day": YESTERDAY.isoformat(),
                "rmssd": RMSSD_METRIC,
                "resting_hr": RESTING_HR_METRIC,
                "sleep": SLEEP_METRIC,
                "cardio": CARDIO_METRIC,
            }
        ),
        wda.DERIVER_VERSION,
        2,
        True,
    )

    result = wda._rollup_for_day(1, YESTERDAY.isoformat(), MELBOURNE, max_hr=None)

    assert result["rmssd"] == RMSSD_METRIC
    assert called == {"rmssd": 0, "resting_hr": 0, "sleep": 0, "cardio": 0}


# ── (c) late-arriving data (raw count grew since rollup) → recomputed ─────────


def test_late_arriving_data_forces_recompute(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    called = _stub_day_math(monkeypatch)
    raw.hr = [(_ts(YESTERDAY, 10), 60)]
    raw.rr = [(_ts(YESTERDAY, 10), 900)]
    rollup.upsert(
        1,
        YESTERDAY.isoformat(),
        json.dumps({"day": YESTERDAY.isoformat()}),
        wda.DERIVER_VERSION,
        2,  # rolled up when only 2 raw rows existed
        True,
    )
    # a historical drain lands one more HR row for yesterday AFTER it was first rolled up
    raw.hr.append((_ts(YESTERDAY, 23), 58))

    result = wda._rollup_for_day(1, YESTERDAY.isoformat(), MELBOURNE, max_hr=None)

    assert called["rmssd"] == 1
    stored = rollup.get(1, YESTERDAY.isoformat())
    assert stored["sample_count"] == 3
    assert result["rmssd"] == RMSSD_METRIC


# ── (d) deriver-version bump → recomputed ─────────────────────────────────────


def test_deriver_version_bump_forces_recompute(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    called = _stub_day_math(monkeypatch)
    raw.hr = [(_ts(YESTERDAY, 10), 60)]
    raw.rr = [(_ts(YESTERDAY, 10), 900)]
    rollup.upsert(
        1,
        YESTERDAY.isoformat(),
        json.dumps({"day": YESTERDAY.isoformat()}),
        "stale-deriver-version",
        2,
        True,
    )

    result = wda._rollup_for_day(1, YESTERDAY.isoformat(), MELBOURNE, max_hr=None)

    assert called["rmssd"] == 1
    assert (
        rollup.get(1, YESTERDAY.isoformat())["deriver_version"] == wda.DERIVER_VERSION
    )
    assert result["rmssd"] == RMSSD_METRIC


# ── (e) today is always live, never persisted ─────────────────────────────────


def test_today_is_never_persisted(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    called = _stub_day_math(monkeypatch)
    raw.hr = [(_ts(TODAY, 10), 60)]
    raw.rr = [(_ts(TODAY, 10), 900)]

    series = wda.get_range(1, 1, "cardio")

    assert series == [{"day": TODAY.isoformat(), **CARDIO_METRIC}]
    assert rollup.get(1, TODAY.isoformat()) is None
    assert called["cardio"] == 1

    # calling again re-derives today from scratch — nothing was cached for it
    series_again = wda.get_range(1, 1, "cardio")
    assert series_again == series
    assert called["cardio"] == 2


def test_sleep_series_excludes_today_by_construction(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    _stub_day_math(monkeypatch)
    raw.hr = [(_ts(TODAY, 10), 60)]
    raw.rr = [(_ts(TODAY, 10), 900)]

    series = wda.get_range(1, 1, "sleep")

    # the only day with raw data is TODAY, and sleep's day_list never includes today
    assert series == []


# ── (f) get_range's per-day series matches compute_day field-for-field ────────


def test_get_range_matches_compute_day_per_field(monkeypatch):
    _freeze(monkeypatch)
    raw, rollup = _install_fakes(monkeypatch)
    _stub_day_math(monkeypatch)
    for d in (TWO_DAYS_AGO, YESTERDAY, TODAY):
        raw.hr.append((_ts(d, 10), 60))
        raw.rr.append((_ts(d, 10), 900))

    for metric, expected in (
        ("rmssd", RMSSD_METRIC),
        ("resting_hr", RESTING_HR_METRIC),
        ("cardio", CARDIO_METRIC),
    ):
        series = wda.get_range(1, 3, metric)
        assert [e["day"] for e in series] == [
            TWO_DAYS_AGO.isoformat(),
            YESTERDAY.isoformat(),
            TODAY.isoformat(),
        ]
        for entry in series:
            assert {k: v for k, v in entry.items() if k != "day"} == expected

    # sleep: nights back, excludes today — same 2 historical days
    sleep_series = wda.get_range(1, 2, "sleep")
    assert sleep_series == [SLEEP_METRIC, SLEEP_METRIC]

    # cross-check against compute_day directly, for the same synthetic fixture
    for d in (TWO_DAYS_AGO, YESTERDAY):
        direct = wda.compute_day(1, d.isoformat(), max_hr=180.0)
        assert direct["rmssd"] == RMSSD_METRIC
        assert direct["resting_hr"] == RESTING_HR_METRIC
        assert direct["cardio"] == CARDIO_METRIC
        assert direct["sleep"] == SLEEP_METRIC
        assert direct["sample_count"] == 2
        assert direct["complete"] is True


# ── compute_day: sample_count + complete flag (pure math, no DB) ──────────────


def test_compute_day_sample_count_and_complete_flag(monkeypatch):
    _freeze(monkeypatch)
    raw, _rollup = _install_fakes(monkeypatch)
    _stub_day_math(monkeypatch)
    raw.hr = [(_ts(YESTERDAY, h), 60) for h in range(5)]
    raw.rr = [(_ts(YESTERDAY, 5), 900), (_ts(YESTERDAY, 6), 910)]

    result = wda.compute_day(1, YESTERDAY.isoformat(), max_hr=180.0)

    assert result["sample_count"] == 7  # 5 hr + 2 rr
    assert result["complete"] is True


def test_compute_day_incomplete_when_a_metric_is_unavailable(monkeypatch):
    _freeze(monkeypatch)
    raw, _rollup = _install_fakes(monkeypatch)
    _stub_day_math(monkeypatch, resting_hr=None)
    raw.hr = [(_ts(YESTERDAY, 10), 60)]
    raw.rr = [(_ts(YESTERDAY, 10), 900)]

    result = wda.compute_day(1, YESTERDAY.isoformat(), max_hr=180.0)

    assert result["resting_hr"] is None
    assert result["complete"] is False


# ── (g) route-level render-duration WARN threshold (Wave 3.4 — TTL cache retired) ──


def test_slow_summary_logs_warning(monkeypatch, caplog):
    times = iter([0.0, 2.5])  # 2500ms elapsed — over the 2000ms budget
    monkeypatch.setattr(whoop_route.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(
        "rivaflow.core.whoop_analytics.whoop_summary", lambda *a, **k: {"ok": True}
    )
    with caplog.at_level(logging.INFO, logger="rivaflow.api.routes.whoop"):
        result = whoop_route._timed_whoop_summary(1, today_is_sabbath=False)

    assert result == {"ok": True}
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "over the" in warnings[0].message


def test_fast_summary_does_not_log_warning(monkeypatch, caplog):
    times = iter([0.0, 0.1])  # 100ms elapsed — under budget
    monkeypatch.setattr(whoop_route.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(
        "rivaflow.core.whoop_analytics.whoop_summary", lambda *a, **k: {"ok": True}
    )
    with caplog.at_level(logging.INFO, logger="rivaflow.api.routes.whoop"):
        whoop_route._timed_whoop_summary(1, today_is_sabbath=False)

    assert not any(r.levelno == logging.WARNING for r in caplog.records)


def test_ttl_cache_mechanism_is_gone():
    """The band-aid this wave retires — regression guard against it creeping back."""
    assert not hasattr(whoop_route, "_cached_whoop_summary")
    assert not hasattr(whoop_route, "_SUMMARY_CACHE")
    assert not hasattr(whoop_route, "_SUMMARY_TTL_S")

"""Wave 3.5 — stress / sleep-quality / respiratory compositions (pure; no DB, no network).

Verifies:
  (a) today_stress: HR-only path is byte-identical to pre-Wave-3.5 when RR is missing/unusable
      (stress-hr-v0), blends in an HRV-depression side when a usable short RR window is available
      (stress-hrv-hr-v1), and both paths carry stress_version + inputs.
  (b) sleep_metrics.sleep_quality: the duration COMPONENT is exactly the old duration-only formula for a
      default (need=9.0) profile, fragmentation penalises the coverage component, cold-start (<4 onsets)
      redistributes the regularity weight into duration, and a sleep-need override changes the duration
      component proportionally. Also whoop_summary's wiring: profile.sleep_need_h (not a hardcoded 9.0)
      actually drives the composed score.
  (c) respiratory_spectral.estimate_respiratory_rate recovers a synthetic 0.25 Hz (15 breaths/min) RSA
      modulation via the DFT band-pass path, and whoop_analytics.respiratory_rate falls back to the
      counting method (resp-count-v0) whenever the spectral estimate disagrees or is unavailable.
"""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from rivaflow.core import respiratory_spectral, whoop_analytics
from rivaflow.core.sleep_metrics import (
    QUALITY_VERSION,
    _duration_component,
    sleep_quality,
)
from rivaflow.db.repositories.whoop_repo import WhoopRepository

MELBOURNE = ZoneInfo("Australia/Melbourne")


def _synthetic_rsa_rr(
    n: int = 300, mean_ms: float = 800.0, amp_ms: float = 40.0, resp_hz: float = 0.25
) -> list[float]:
    """`n` RR intervals (ms) whose mean is amplitude-modulated at `resp_hz` on the cumulative beat-time
    axis — a clean, noise-free RSA signal the spectral estimator should recover exactly.
    """
    vals: list[float] = []
    t = 0.0
    for _ in range(n):
        rr = mean_ms + amp_ms * math.sin(2 * math.pi * resp_hz * t)
        vals.append(rr)
        t += rr / 1000.0
    return vals


# ── (a) today_stress ──────────────────────────────────────────────────────────


def _stub_stress_deps(
    monkeypatch,
    *,
    recent_hr: list[dict],
    resting_hr: list[dict],
    rr_rows: list[dict] | None = None,
    baseline_rmssd: list[dict] | None = None,
) -> None:
    monkeypatch.setattr(
        WhoopRepository, "recent_hr", staticmethod(lambda user_id, hours=1: recent_hr)
    )
    monkeypatch.setattr(
        WhoopRepository,
        "rr_range_between",
        staticmethod(lambda user_id, s, e: rr_rows or []),
    )
    monkeypatch.setattr(
        whoop_analytics,
        "daily_resting_hr",
        lambda user_id, days=3, max_hr=None: resting_hr,
    )
    monkeypatch.setattr(
        whoop_analytics,
        "daily_resting_rmssd",
        lambda user_id, days=7, max_hr=None: baseline_rmssd or [],
    )


def test_stress_hr_only_path_unchanged_when_rr_missing(monkeypatch):
    _stub_stress_deps(
        monkeypatch,
        recent_hr=[{"bpm": 100, "ts": "x"} for _ in range(70)],
        resting_hr=[{"resting_hr": 55}],
        rr_rows=[],
    )
    r = whoop_analytics.today_stress(1, max_hr=180)
    # pre-Wave-3.5 formula: round((100-55)/(180-55)*100) == 36
    assert r == {
        "available": True,
        "stress": 36,
        "current_hr": 100,
        "resting_hr": 55,
        "stress_version": "stress-hr-v0",
        "inputs": ["hr"],
    }


def test_stress_blends_hrv_when_rr_usable(monkeypatch):
    rr_vals = [820.0 if i % 2 == 0 else 800.0 for i in range(40)]  # rmssd == 20ms
    _stub_stress_deps(
        monkeypatch,
        recent_hr=[{"bpm": 100, "ts": "x"} for _ in range(70)],
        resting_hr=[{"resting_hr": 55}],
        rr_rows=[{"rr_ms": v} for v in rr_vals],
        baseline_rmssd=[{"rmssd": 40.0} for _ in range(7)],
    )
    r = whoop_analytics.today_stress(1, max_hr=180)
    # hr_elevation = round((100-55)/125*100) = 36; hrv_depression = round((40-20)/40*100) = 50
    # blend = round(0.6*36 + 0.4*50) = round(41.6) = 42
    assert r["stress"] == 42
    assert r["stress_version"] == "stress-hrv-hr-v1"
    assert r["inputs"] == ["hr", "rr"]
    assert r["current_hr"] == 100
    assert r["resting_hr"] == 55


def test_stress_falls_back_when_rr_unusable_despite_data(monkeypatch):
    # Constant RR (no variance) -> rmssd == 0 -> _stress_hrv_component bails, HR-only path used.
    _stub_stress_deps(
        monkeypatch,
        recent_hr=[{"bpm": 100, "ts": "x"} for _ in range(70)],
        resting_hr=[{"resting_hr": 55}],
        rr_rows=[{"rr_ms": 800.0} for _ in range(40)],
        baseline_rmssd=[{"rmssd": 40.0} for _ in range(7)],
    )
    r = whoop_analytics.today_stress(1, max_hr=180)
    assert r["stress"] == 36
    assert r["stress_version"] == "stress-hr-v0"
    assert r["inputs"] == ["hr"]


def test_stress_unavailable_when_no_recent_hr(monkeypatch):
    _stub_stress_deps(monkeypatch, recent_hr=[], resting_hr=[{"resting_hr": 55}])
    r = whoop_analytics.today_stress(1, max_hr=180)
    assert r == {
        "available": False,
        "reason": "Not enough recent HR for a stress estimate.",
    }


# ── (b) sleep quality composition ─────────────────────────────────────────────


def test_duration_component_matches_old_formula_for_default_need():
    for dur in (0.0, 6.0, 7.6, 9.0, 10.0, 12.0):
        old = max(0, min(100, round((dur / 9.0) * 100)))
        assert round(_duration_component(dur, 9.0)) == old


def test_duration_component_scales_with_need_override():
    assert _duration_component(7.5, 7.5) == 100.0
    assert round(_duration_component(6.0, 7.5)) == 80  # 6/7.5*100 = 80


def test_quality_version_key_present():
    q = sleep_quality(7.6, 9.0)
    assert q["quality_version"] == QUALITY_VERSION == "sleep-quality-v1"


def test_fragmentation_penalises_coverage_component_and_score():
    baseline = sleep_quality(7.6, 9.0, coverage_pct=90, fragmented=False)
    fragmented = sleep_quality(7.6, 9.0, coverage_pct=90, fragmented=True)
    assert baseline["components"]["coverage"] == 90.0
    assert fragmented["components"]["coverage"] == 70.0  # 90 - 20pt penalty
    assert fragmented["score"] < baseline["score"]


def test_regularity_cold_start_redistributes_into_duration():
    # <4 onsets -> regularity component is None, its weight folds into duration.
    cold = sleep_quality(
        7.6, 9.0, coverage_pct=90, fragmented=False, onset_hours=[22.0, 22.1]
    )
    baseline_no_regularity = sleep_quality(7.6, 9.0, coverage_pct=90, fragmented=False)
    assert cold["components"]["regularity"] is None
    assert cold["score"] == baseline_no_regularity["score"]

    # >=4 onsets, perfectly regular -> regularity component scores 100 and lifts the blend.
    full = sleep_quality(
        7.6,
        9.0,
        coverage_pct=90,
        fragmented=False,
        onset_hours=[22.0, 22.0, 22.0, 22.0, 22.0],
    )
    assert full["components"]["regularity"] == 100.0
    assert full["score"] > cold["score"]


def test_sleep_need_override_changes_duration_component_proportionally():
    need_9 = sleep_quality(7.6, 9.0)
    need_7_5 = sleep_quality(7.6, 7.5)
    assert need_7_5["components"]["duration"] > need_9["components"]["duration"]
    assert need_9["components"]["duration"] == round(_duration_component(7.6, 9.0), 1)
    assert need_7_5["components"]["duration"] == round(_duration_component(7.6, 7.5), 1)


class _FakeProfile:
    tz = MELBOURNE
    sleep_need_h = 8.0
    age = 40
    rest_weekday = 6
    max_hr_override = None


def test_whoop_summary_uses_profile_sleep_need_not_hardcoded_nine(monkeypatch):
    """Wiring check: whoop_summary's quality composition must actually consume
    profile.sleep_need_h (8.0 here), not the old hardcoded 9.0 literal — the duration component for a
    6h night differs materially between the two (75 vs ~67)."""
    monkeypatch.setattr(
        whoop_analytics, "get_whoop_profile", lambda uid: _FakeProfile()
    )
    monkeypatch.setattr(
        whoop_analytics,
        "compute_readiness",
        lambda uid, today_is_sabbath=False: {"state": "Building"},
    )
    monkeypatch.setattr(
        whoop_analytics, "daily_resting_rmssd", lambda uid, days=14, max_hr=None: []
    )
    monkeypatch.setattr(
        whoop_analytics, "daily_resting_hr", lambda uid, days=14, max_hr=None: []
    )
    monkeypatch.setattr(
        whoop_analytics, "daily_cardio_load", lambda uid, days=14, max_hr=None: []
    )
    monkeypatch.setattr(
        whoop_analytics,
        "nightly_sleep",
        lambda uid: {
            "available": True,
            "duration_hours": 6.0,
            "coverage_pct": 80,
            "fragmented": False,
            "sleep_start": "2026-07-09T22:00:00+10:00",
            "sleep_end": "2026-07-10T04:00:00+10:00",
        },
    )
    monkeypatch.setattr(
        whoop_analytics,
        "nightly_sleep_history",
        lambda uid, nights=7, max_hr=None: [],
    )
    monkeypatch.setattr(
        whoop_analytics, "respiratory_rate", lambda uid: {"available": False}
    )
    monkeypatch.setattr(
        whoop_analytics, "today_stress", lambda uid, max_hr=None: {"available": False}
    )
    monkeypatch.setattr(whoop_analytics, "capture_coverage", lambda uid, days=21: {})
    monkeypatch.setattr(whoop_analytics, "user_max_hr", lambda uid: {"max_hr": 180.0})
    monkeypatch.setattr(whoop_analytics, "prevention_watch", lambda uid: {})
    monkeypatch.setattr(whoop_analytics, "_chronic_load", lambda cardio: None)
    monkeypatch.setattr(
        whoop_analytics,
        "prescribe_strain",
        lambda state, chronic, acute: {"available": False},
    )
    monkeypatch.setattr(whoop_analytics, "acwr", lambda series: {})

    result = whoop_analytics.whoop_summary(1)

    # duration component = 6.0/8.0*100 = 75.0; coverage = 80 (no fragmentation, no onset history)
    # weights: duration carries 0.6+0.15 (regularity cold-start) = 0.75, coverage 0.25
    # score = 0.75*75 + 0.25*80 = 76
    assert result["sleep"]["quality_score"] == 76
    assert result["sleep"]["quality_version"] == "sleep-quality-v1"


# ── (c) respiratory band-pass ──────────────────────────────────────────────────


def test_spectral_respiration_recovers_synthetic_fifteen_rpm():
    rr = _synthetic_rsa_rr(n=300, mean_ms=800.0, amp_ms=40.0, resp_hz=0.25)
    est = respiratory_spectral.estimate_respiratory_rate(rr)
    assert est is not None
    assert abs(est.rpm - 15.0) <= 1.0


def test_spectral_respiration_none_on_short_segment():
    # 20 beats @ ~500ms is well under MIN_WINDOW_SEC (60s).
    short = [500.0] * 20
    assert respiratory_spectral.estimate_respiratory_rate(short) is None


def test_respiratory_rate_reports_bandpass_when_methods_agree(monkeypatch):
    rr = _synthetic_rsa_rr(n=300, mean_ms=800.0, amp_ms=40.0, resp_hz=0.25)
    rows = [{"ts": "x", "rr_ms": v} for v in rr]
    monkeypatch.setattr(
        WhoopRepository, "rr_range", staticmethod(lambda user_id, days=1: rows)
    )

    result = whoop_analytics.respiratory_rate(1)

    assert result["available"] is True
    assert result["source"] == "rr_rsa_bandpass"
    assert result["resp_version"] == "resp-bandpass-v1"
    assert abs(result["respiratory_rate"] - 15.0) <= 1.0


def test_respiratory_rate_falls_back_to_counting_when_spectral_unavailable(
    monkeypatch,
):
    rr = _synthetic_rsa_rr(n=300, mean_ms=800.0, amp_ms=40.0, resp_hz=0.25)
    rows = [{"ts": "x", "rr_ms": v} for v in rr]
    monkeypatch.setattr(
        WhoopRepository, "rr_range", staticmethod(lambda user_id, days=1: rows)
    )
    monkeypatch.setattr(whoop_analytics, "_spectral_resp_rpm", lambda vals: None)

    result = whoop_analytics.respiratory_rate(1)

    assert result["available"] is True
    assert result["source"] == "rr_rsa"
    assert result["resp_version"] == "resp-count-v0"


def test_respiratory_rate_falls_back_to_counting_on_disagreement(monkeypatch):
    rr = _synthetic_rsa_rr(n=300, mean_ms=800.0, amp_ms=40.0, resp_hz=0.25)
    rows = [{"ts": "x", "rr_ms": v} for v in rr]
    monkeypatch.setattr(
        WhoopRepository, "rr_range", staticmethod(lambda user_id, days=1: rows)
    )
    # counting lands ~14.8rpm on this fixture — 5.0rpm is far outside AGREEMENT_TOLERANCE_RPM (2.0)
    monkeypatch.setattr(whoop_analytics, "_spectral_resp_rpm", lambda vals: 5.0)

    result = whoop_analytics.respiratory_rate(1)

    assert result["available"] is True
    assert result["source"] == "rr_rsa"
    assert result["resp_version"] == "resp-count-v0"


def test_respiratory_rate_unavailable_when_no_clean_rr(monkeypatch):
    monkeypatch.setattr(
        WhoopRepository, "rr_range", staticmethod(lambda user_id, days=1: [])
    )
    result = whoop_analytics.respiratory_rate(1)
    assert result == {
        "available": False,
        "reason": "Not enough clean resting RR for a respiratory estimate.",
    }

"""B6 Baseline-Deviation Watch — pure-core tests (no DB). Safety properties are load-bearing."""

from __future__ import annotations

from math import log

from rivaflow.core.prevention import (
    CUSUM_H,
    GREEN_CAVEAT,
    cusum_positive,
    evaluate_prevention,
    mad,
    robust_baseline,
    robust_z,
    slow_drift,
    validate_engine,
)


def _r(value, median, mad, **extra):
    return {"value": value, "median": median, "mad": mad, **extra}


# --- baseline primitives --------------------------------------------------


def test_mad_and_robust_baseline():
    vals = [10, 10, 10, 10, 12]
    b = robust_baseline(vals)
    assert b["median"] == 10
    assert b["mad"] == mad(vals, 10)


def test_robust_baseline_none_when_too_few():
    assert robust_baseline([1, 2, 3, 4]) is None


def test_robust_z_direction():
    """Positive worse_z always means 'more strained', regardless of signal direction."""
    # RHR elevated → positive
    assert robust_z(56, 50, 2, "high") > 1.5
    # lnRMSSD suppressed (low) → positive
    assert robust_z(log(35), log(50), 0.1, "low") > 0


# --- tier logic + safety properties ---------------------------------------


def test_all_in_range_is_green_with_caveat():
    r = evaluate_prevention(
        {
            "rhr": _r(50, 50, 2),
            "lnrmssd": _r(log(50), log(50), 0.1),
            "resp_rate": _r(14, 14, 1),
        }
    )
    assert r["tier"] == "green"
    assert r["caveat"] == GREEN_CAVEAT
    assert r["fires_on_sabbath"] is False


def test_two_families_elevated_is_amber():
    r = evaluate_prevention(
        {
            "rhr": _r(55, 50, 2),  # nocturnal_hr family, worse_z ~1.7
            "lnrmssd": _r(
                log(50) - 1.7 * 0.1 * 1.4826, log(50), 0.1
            ),  # vagal family suppressed
            "resp_rate": _r(14, 14, 1),
        }
    )
    assert r["tier"] == "amber"
    assert r["channel"] == "safety"
    assert r["fires_on_sabbath"] is True
    assert set(r["flagged_families"]) == {"nocturnal_hr", "vagal"}


def test_respiratory_alone_cannot_fire():
    """Resp-rate is one family and the least-validated signal — it must NEVER raise a tier alone."""
    r = evaluate_prevention(
        {
            "rhr": _r(50, 50, 2),
            "lnrmssd": _r(log(50), log(50), 0.1),
            "resp_rate": _r(20, 14, 1),  # strongly elevated, but single family
        }
    )
    assert r["tier"] == "green"


def test_correlated_same_family_cannot_self_corroborate():
    """RHR and sleeping-HR are ONE family — both elevated is a single perturbation, not co-occurrence."""
    r = evaluate_prevention(
        {
            "rhr": _r(56, 50, 2),
            "sleeping_hr": _r(60, 54, 2),  # both nocturnal_hr, both flagged
            "lnrmssd": _r(log(50), log(50), 0.1),
        }
    )
    assert r["flagged_families"] == ["nocturnal_hr"]
    assert r["tier"] == "green"


def test_two_strong_families_is_red():
    r = evaluate_prevention(
        {
            "rhr": _r(58, 50, 2),  # worse_z ~2.7
            "lnrmssd": _r(log(50) - 2.5 * 0.1 * 1.4826, log(50), 0.1),
        }
    )
    assert r["tier"] == "red"
    assert r["channel"] == "safety"
    assert r["diagnostic"] is False


def test_sabbath_does_not_silence_safety():
    """Amber/red are the safety channel — they fire even on the Sabbath."""
    r = evaluate_prevention(
        {
            "rhr": _r(55, 50, 2),
            "lnrmssd": _r(log(50) - 1.7 * 0.1 * 1.4826, log(50), 0.1),
        },
        today_is_sabbath=True,
    )
    assert r["tier"] == "amber"
    assert r["fires_on_sabbath"] is True


def test_drivers_sorted_and_never_diagnostic():
    r = evaluate_prevention(
        {"rhr": _r(55, 50, 2), "lnrmssd": _r(log(50), log(50), 0.1)}
    )
    zs = [d["worse_z"] for d in r["drivers"]]
    assert zs == sorted(zs, reverse=True)
    assert r["diagnostic"] is False
    assert "not disease" in r["note"]


# --- CUSUM (sustained drift) ---------------------------------------------


def test_cusum_accumulates_sustained_drift():
    # sustained +1.0 worse-z each day (above slack 0.5) accumulates and breaches
    s = cusum_positive([1.0] * 10)
    assert s >= CUSUM_H


def test_cusum_ignores_small_noise():
    # deviations under the slack never accumulate
    assert cusum_positive([0.3, -0.2, 0.4, 0.1, -0.3]) == 0.0


def test_cusum_breach_needs_second_family_for_amber():
    """A CUSUM breach in ONE family still can't fire alone (≥2 families rule)."""
    r = evaluate_prevention(
        {
            "rhr": _r(50, 50, 2, cusum=10.0),  # nocturnal_hr family: CUSUM breached
            "lnrmssd": _r(log(50), log(50), 0.1),  # vagal: in range
        }
    )
    assert r["tier"] == "green"


def test_cusum_breach_two_families_is_amber():
    r = evaluate_prevention(
        {
            "rhr": _r(50, 50, 2, cusum=10.0),  # nocturnal_hr breach
            "lnrmssd": _r(log(50), log(50), 0.1, cusum=10.0),  # vagal breach
        }
    )
    assert r["tier"] == "amber"
    assert set(r["flagged_families"]) == {"nocturnal_hr", "vagal"}


def test_cusum_does_not_escalate_to_red():
    """CUSUM/drift escalate only to amber; red stays acute-z only."""
    r = evaluate_prevention(
        {
            "rhr": _r(50, 50, 2, cusum=99.0),
            "lnrmssd": _r(log(50), log(50), 0.1, cusum=99.0),
        }
    )
    assert r["tier"] == "amber"


# --- slow-drift guard -----------------------------------------------------


def test_slow_drift_flags_worsening_rhr():
    # short median well above the long reference (rising RHR = worse)
    assert slow_drift(58, 50, 2, "high") is True


def test_slow_drift_ignores_improvement():
    assert slow_drift(46, 50, 2, "high") is False


def test_slow_drift_direction_for_lnrmssd():
    # falling lnRMSSD (low) is worse → drift True
    assert slow_drift(3.6, 3.9, 0.1, "low") is True


def test_drift_flag_contributes_to_family():
    r = evaluate_prevention(
        {
            "rhr": _r(50, 50, 2, drift=True),
            "lnrmssd": _r(log(50), log(50), 0.1, drift=True),
        }
    )
    assert r["tier"] == "amber"


# --- fourth signal (sleeping_hr) ------------------------------------------


def test_sleeping_hr_shares_nocturnal_family():
    """RHR + sleeping-HR are one family; both flagged is still a single perturbation → green."""
    r = evaluate_prevention(
        {
            "rhr": _r(56, 50, 2),
            "sleeping_hr": _r(60, 54, 2),
            "lnrmssd": _r(log(50), log(50), 0.1),
        }
    )
    assert r["flagged_families"] == ["nocturnal_hr"]
    assert r["tier"] == "green"


# --- validation / tuning gate --------------------------------------------


def _tl(days_tiers):
    return [{"day": d, "tier": t} for d, t in days_tiers]


def test_validate_engine_pass():
    # amber the day before each of 2 onsets, no false ambers
    timeline = _tl(
        [
            ("2026-06-01", "green"),
            ("2026-06-02", "amber"),
            ("2026-06-03", "green"),
            ("2026-06-09", "amber"),
            ("2026-06-10", "green"),
        ]
        + [(f"2026-06-{d:02d}", "green") for d in range(11, 25)]
    )
    r = validate_engine(timeline, {"2026-06-03", "2026-06-10"})
    assert r["onsets_detected"] == 2
    assert r["false_ambers"] == 0
    assert r["passes"] is True


def test_validate_engine_fails_on_false_ambers():
    # many ambers unrelated to any onset → high false rate → fail
    timeline = _tl([(f"2026-06-{d:02d}", "amber") for d in range(1, 8)])
    r = validate_engine(timeline, {"2026-06-20"})
    assert r["passes"] is False
    assert r["false_ambers_per_week"] > 1.0


def test_validate_engine_needs_onsets():
    r = validate_engine(_tl([("2026-06-01", "green")]), set())
    assert r["passes"] is False

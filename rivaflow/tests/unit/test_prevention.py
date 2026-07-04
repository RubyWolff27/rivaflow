"""B6 Baseline-Deviation Watch — pure-core tests (no DB). Safety properties are load-bearing."""

from __future__ import annotations

from math import log

from rivaflow.core.prevention import (
    GREEN_CAVEAT,
    evaluate_prevention,
    mad,
    robust_baseline,
    robust_z,
)


def _r(value, median, mad):
    return {"value": value, "median": median, "mad": mad}


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

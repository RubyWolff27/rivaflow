"""B5 — StrainPolicy seam + dose-response fit — pure-core tests (no DB)."""

from __future__ import annotations

import pytest

from rivaflow.core.strain_fit import (
    MIN_STATE_DAYS,
    MULT_CLAMP,
    _fit_multipliers_from_samples,
    apply_env_strain_policy,
)
from rivaflow.core.strain_target import (
    STATE_MULTIPLIER,
    STRAIN_CAP,
    StrainPolicy,
    get_strain_policy,
    prescribe_strain,
    set_strain_policy,
)


@pytest.fixture(autouse=True)
def _reset_policy():
    """The active policy is process-global state — every test starts and ends on the default heuristic."""
    set_strain_policy(None)
    yield
    set_strain_policy(None)


# --- (a) default policy is unchanged + (b) policy_version present ---------


def test_prime_unchanged_under_default_policy():
    r = prescribe_strain("Prime", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(11.5)
    assert r["capped"] is False
    assert r["band"] == [9.5, 13.5]
    assert r["policy_version"] == "strain-heuristic-v1"


def test_balanced_unchanged_under_default_policy():
    r = prescribe_strain("Balanced", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(10.0)
    assert r["capped"] is False
    assert r["policy_version"] == "strain-heuristic-v1"


def test_strained_unchanged_under_default_policy():
    r = prescribe_strain("Strained", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(6.0)
    assert r["capped"] is True
    assert r["band"] == [4.0, 8.0]
    assert r["policy_version"] == "strain-heuristic-v1"


def test_rundown_unchanged_under_default_policy():
    r = prescribe_strain("Rundown", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(4.0)
    assert r["capped"] is True
    assert r["policy_version"] == "strain-heuristic-v1"


def test_no_target_states_unchanged_and_carry_no_policy_version():
    assert prescribe_strain("Rest", 10.0) == {
        "available": False,
        "state": "Rest",
        "reason": "Sabbath — rest is prescribed.",
    }
    assert prescribe_strain("Building", None) == {
        "available": False,
        "state": "Building",
        "reason": "Building your baseline — no strain target yet.",
    }
    assert prescribe_strain(None, 10.0)["available"] is False


def test_cap_and_band_unchanged():
    r = prescribe_strain("Prime", chronic_load=20.0)  # 20 * 1.15 = 23 → capped
    assert r["target_load"] == STRAIN_CAP
    assert r["band"][1] == STRAIN_CAP


# --- (c) set/get roundtrip + reset ------------------------------------------


def test_set_get_roundtrip():
    custom = StrainPolicy(version="test-v0", multipliers={"Balanced": 0.8})
    set_strain_policy(custom)
    assert get_strain_policy() is custom
    r = prescribe_strain("Balanced", chronic_load=10.0)
    assert r["target_load"] == pytest.approx(8.0)
    assert r["policy_version"] == "test-v0"


def test_set_none_resets_to_default_heuristic():
    set_strain_policy(StrainPolicy(version="test-v0", multipliers={"Balanced": 0.8}))
    set_strain_policy(None)
    active = get_strain_policy()
    assert active.version == "strain-heuristic-v1"
    assert active.multipliers == STATE_MULTIPLIER


# --- (d) synthetic dose-response fit recovers known crossings -------------


def _linear_samples(
    slope: float, crossing: float, n: int = 10
) -> list[tuple[float, float]]:
    """n noise-free (ratio, delta) points on the line delta = slope * (ratio - crossing), spread across a
    plausible ratio range straddling the crossing — exactly recoverable by OLS."""
    ratios = [crossing + (i - n // 2) * 0.2 for i in range(n)]
    return [(r, slope * (r - crossing)) for r in ratios]


def test_fit_recovers_known_multiplier_per_state():
    known = {"Prime": 1.3, "Balanced": 1.0, "Strained": 0.5, "Rundown": 0.3}
    samples = {state: _linear_samples(-2.0, xing) for state, xing in known.items()}

    policy, report = _fit_multipliers_from_samples(samples)

    assert policy.version == "strain-fitted-v1"
    for state, expected in known.items():
        assert policy.multipliers[state] == pytest.approx(expected, abs=0.01)
        assert report[state]["reason"] == "fitted"
        assert report[state]["fitted"] == pytest.approx(expected, abs=0.01)
        assert report[state]["r2"] == pytest.approx(1.0, abs=1e-6)
        assert report[state]["n"] == 10


# --- (e) sparse states keep the heuristic -----------------------------------


def test_sparse_state_keeps_heuristic():
    samples = {
        "Prime": _linear_samples(-2.0, 1.3),  # 10 points, qualifies
        "Balanced": _linear_samples(-2.0, 1.0)[: MIN_STATE_DAYS - 1],  # too few
        "Strained": [],
        "Rundown": [],
    }
    policy, report = _fit_multipliers_from_samples(samples)

    assert policy.multipliers["Prime"] == pytest.approx(1.3, abs=0.01)

    for state in ("Balanced", "Strained", "Rundown"):
        assert policy.multipliers[state] == STATE_MULTIPLIER[state]
        assert report[state]["reason"] == "insufficient_data"
        assert report[state]["used"] == STATE_MULTIPLIER[state]
        assert report[state]["fitted"] is None


# --- (f) clamping ------------------------------------------------------------


def test_fit_clamps_to_sane_band():
    lo, hi = MULT_CLAMP
    samples = {
        "Prime": _linear_samples(-2.0, hi + 1.0),  # crossing well above the upper clamp
        "Balanced": _linear_samples(
            -2.0, lo - 0.15
        ),  # crossing well below the lower clamp
        "Strained": [],
        "Rundown": [],
    }
    policy, report = _fit_multipliers_from_samples(samples)

    assert policy.multipliers["Prime"] == pytest.approx(hi)
    assert report["Prime"]["used"] == pytest.approx(hi)
    assert policy.multipliers["Balanced"] == pytest.approx(lo)
    assert report["Balanced"]["used"] == pytest.approx(lo)


def test_degenerate_fit_keeps_heuristic():
    """All-identical ratios (no slope determinable) must fall back, not raise or return a bogus crossing."""
    flat = [(1.0, 0.1 * i) for i in range(MIN_STATE_DAYS)]
    samples = {"Prime": flat, "Balanced": [], "Strained": [], "Rundown": []}
    policy, report = _fit_multipliers_from_samples(samples)

    assert policy.multipliers["Prime"] == STATE_MULTIPLIER["Prime"]
    assert report["Prime"]["reason"] == "degenerate_fit"


# --- (g) env-flag application path ------------------------------------------


def test_env_flag_unset_leaves_heuristic():
    calls = []

    def fake_fit(user_id: int):
        calls.append(user_id)
        return {
            "policy": StrainPolicy(version="should-not-apply", multipliers={}),
            "report": {},
        }

    policy = apply_env_strain_policy(1, fit_fn=fake_fit, env={})
    assert policy.version == "strain-heuristic-v1"
    assert calls == []  # never even called the fitter


def test_env_flag_fitted_swaps_active_policy():
    fitted = StrainPolicy(version="strain-fitted-v1", multipliers={"Balanced": 0.77})

    def fake_fit(user_id: int):
        assert user_id == 42
        return {"policy": fitted, "report": {}}

    policy = apply_env_strain_policy(
        42, fit_fn=fake_fit, env={"WHOOP_STRAIN_POLICY": "fitted"}
    )
    assert policy is fitted
    assert get_strain_policy() is fitted


def test_env_flag_fit_failure_never_raises_and_keeps_current_policy():
    def failing_fit(user_id: int):
        raise RuntimeError("DB is down")

    policy = apply_env_strain_policy(
        1, fit_fn=failing_fit, env={"WHOOP_STRAIN_POLICY": "fitted"}
    )
    assert policy.version == "strain-heuristic-v1"  # untouched, never raised

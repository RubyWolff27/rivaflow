"""B6 — Baseline-Deviation Watch (the prevention engine's pure core).

The centrepiece, rebuilt to every safety property the Fable review + confirmation pass demanded
(WHOOP_FUTURE_STATE_PLAN.md B6). Detects *deviation from personal baseline*, NEVER disease.

  - **FOUR signals, no cardiac rhythm.** RHR, lnRMSSD/HF suppression, respiratory-rate rise, nocturnal
    sleeping-HR — the AFib-class signal is not here and never contributes to an always-fire alert.
  - **Signal FAMILIES enforce independence.** RHR and sleeping-HR co-move (alcohol, warm room) so they are
    one "nocturnal-HR" family counted once; lnRMSSD is the vagal family; resp-rate the respiratory family.
    Co-occurrence requires flagged signals across ≥2 DISTINCT families — one perturbation can't self-corroborate.
  - **Robust baselines (median / MAD), not mean±SD**, so a single anomaly can't desensitise the detector.
  - **Respiratory rate can never fire alone** (least-validated signal) — it needs a second family, and a solo
    CUSUM/z breach never raises a tier by itself.
  - **Tier → channel map is explicit.** 🟢 green carries the "green ≠ healthy" caveat; 🟡 amber and 🔴 red are
    the SAFETY channel and fire on Sunday (early-warning, not a coaching nudge). Never diagnostic.
"""

from __future__ import annotations

from datetime import date
from statistics import median

AMBER_Z = 1.5
RED_Z = 2.0
MAD_SCALE = 1.4826  # scales MAD to a normal-consistent SD estimate

# CUSUM — accumulates small day-to-day deviations so a slow multi-day drift trips even when no single
# day breaches the z threshold. k is the slack (ignore deviations under half an SD); h is the decision line.
CUSUM_K = 0.5
CUSUM_H = 4.0
# Slow-drift guard — the recent short baseline this many robust-SDs off a longer stable reference = drift.
SLOW_DRIFT_DELTA = 1.0

# Which family each signal belongs to (co-occurrence counts families, not signals).
SIGNAL_FAMILY = {
    "rhr": "nocturnal_hr",
    "sleeping_hr": "nocturnal_hr",
    "lnrmssd": "vagal",
    "resp_rate": "respiratory",
}
# Direction in which the signal indicates strain/worsening.
WORSE_WHEN = {
    "rhr": "high",
    "sleeping_hr": "high",
    "lnrmssd": "low",
    "resp_rate": "high",
}

GREEN_CAVEAT = (
    "No deviation in the signals I can measure (HR, HRV, breathing) — I'm blind to temperature and blood "
    "oxygen, so trust your symptoms over a green light."
)
AMBER_COPY = (
    "Your autonomics are working harder than your baseline — could be illness, training, alcohol, "
    "heat, or poor sleep. Ease today and watch."
)
RED_COPY = (
    "Strong multi-signal deviation from your baseline — rest and recover. This is not a diagnosis; "
    "if you feel unwell, see a clinician."
)


def mad(values: list[float], med: float | None = None) -> float:
    """Median absolute deviation."""
    if not values:
        return 0.0
    m = med if med is not None else median(values)
    return median([abs(v - m) for v in values])


def robust_baseline(values: list[float]) -> dict | None:
    """Median + MAD baseline. Robust to outliers, unlike mean±SD (a single spike inflates SD and blinds the
    detector to the next anomaly). Returns None with too few points."""
    if len(values) < 5:
        return None
    m = median(values)
    return {"median": m, "mad": mad(values, m)}


def robust_z(value: float, median_: float, mad_: float, worse_when: str) -> float:
    """Signed deviation where POSITIVE always means 'more strained'. Uses MAD-scaled distance; a zero MAD
    falls back to a tiny scale so identical history doesn't divide by zero."""
    scale = MAD_SCALE * mad_ if mad_ > 0 else 1.0
    z = (value - median_) / scale
    return z if worse_when == "high" else -z


def cusum_positive(worse_z_series: list[float], k: float = CUSUM_K) -> float:
    """One-sided (upper) tabular CUSUM in the 'worse' direction. Returns the final accumulator (≥0); a value
    ≥ CUSUM_H signals a sustained drift a single-day z-score would miss. Feed a series of daily worse-z values.
    """
    s = 0.0
    for z in worse_z_series:
        s = max(0.0, s + z - k)
    return s


def slow_drift(
    short_median: float, long_median: float, long_mad: float, worse_when: str
) -> bool:
    """True when the recent short baseline has drifted from a longer stable reference in the worsening
    direction — so a gradual overtraining/subacute shift becomes a flag instead of being absorbed as the
    new 'normal' by the rolling baseline."""
    scale = MAD_SCALE * long_mad if long_mad > 0 else 1.0
    z = (short_median - long_median) / scale
    worse = z if worse_when == "high" else -z
    return worse >= SLOW_DRIFT_DELTA


def evaluate_prevention(
    readings: dict[str, dict], today_is_sabbath: bool = False
) -> dict:
    """Fuse per-signal readings into a tier. `readings` maps signal name → {value, median, mad, cusum?, drift?}
    (cusum = the signal's accumulator from cusum_positive; drift = slow_drift verdict — both optional). Include
    only signals that have a baseline. Deterministic and DB-free. Sabbath does NOT silence this — it is the
    safety channel."""
    if "lnrmssd" not in readings and len(readings) < 2:
        return {
            "available": False,
            "reason": "Building baselines — need more covered days.",
        }

    family_flagged: dict[str, bool] = {}
    family_strong: dict[str, bool] = {}
    drivers: list[dict] = []
    for name, r in readings.items():
        if name not in SIGNAL_FAMILY:
            continue
        wz = robust_z(r["value"], r["median"], r["mad"], WORSE_WHEN[name])
        cusum = float(r.get("cusum", 0.0))
        drift = bool(r.get("drift", False))
        cusum_breach = cusum >= CUSUM_H
        # A signal flags on an ACUTE z spike, a sustained CUSUM drift, or a baseline drift.
        flagged = wz >= AMBER_Z or cusum_breach or drift
        strong = (
            wz >= RED_Z
        )  # red stays acute-only — CUSUM/drift escalate to amber, never straight to red
        fam = SIGNAL_FAMILY[name]
        family_flagged[fam] = family_flagged.get(fam, False) or flagged
        family_strong[fam] = family_strong.get(fam, False) or strong
        drivers.append(
            {
                "signal": name,
                "family": fam,
                "worse_z": round(wz, 2),
                "cusum": round(cusum, 2),
                "cusum_breach": cusum_breach,
                "drift": drift,
                "flagged": flagged,
            }
        )

    flagged_families = [f for f, v in family_flagged.items() if v]
    strong_families = [f for f, v in family_strong.items() if v]
    drivers.sort(key=lambda d: d["worse_z"], reverse=True)

    # ≥2 DISTINCT families required for any alert → resp (one family) can never fire alone.
    if len(strong_families) >= 2:
        tier, channel, headline, caveat = "red", "safety", RED_COPY, None
    elif len(flagged_families) >= 2:
        tier, channel, headline, caveat = "amber", "safety", AMBER_COPY, None
    else:
        tier, channel, headline, caveat = (
            "green",
            "neutral",
            "In range across the signals I can measure.",
            GREEN_CAVEAT,
        )

    return {
        "available": True,
        "tier": tier,
        "channel": channel,
        "fires_on_sabbath": channel
        == "safety",  # amber/red are safety → fire Sunday; green is neutral
        "headline": headline,
        "caveat": caveat,
        "flagged_families": flagged_families,
        "drivers": drivers,
        "diagnostic": False,
        "note": "Detects deviation from your own baseline, not disease. Not a medical device.",
    }


# Acceptance target (WHOOP_FUTURE_STATE_PLAN.md B6): before the engine may fire into any channel it must,
# on a retrospective backtest, flag the last known illness onsets with a low false-amber rate.
ACCEPT_MIN_ONSETS_DETECTED = 2
ACCEPT_MAX_FALSE_AMBER_PER_WEEK = 1.0
DETECTION_LEAD_DAYS = (
    2  # an alert in the 2 days up to (and incl.) an onset counts as caught
)


def validate_engine(
    timeline: list[dict],
    illness_onsets: set[str],
    lead_days: int = DETECTION_LEAD_DAYS,
) -> dict:
    """B6 validation & tuning gate — backtest the engine before it ships to a channel.

    `timeline`: chronological per-day evaluations, each {"day": "YYYY-MM-DD", "tier": "green|amber|red"}.
    `illness_onsets`: the set of days the user retrospectively tagged as feeling ill.
    Detection = an amber/red fired within `lead_days` up to and including the onset. A false amber is an
    amber/red day NOT inside any onset's lead window. Passes only if it catches ≥2 known onsets AND stays
    under 1 false amber/week — otherwise the engine is not yet trustworthy in the safety channel.
    """
    fired = {row["day"] for row in timeline if row.get("tier") in ("amber", "red")}
    onset_dates = {date.fromisoformat(d) for d in illness_onsets}
    fired_dates = {date.fromisoformat(d) for d in fired}

    detected = 0
    for onset in onset_dates:
        window = {onset.toordinal() - k for k in range(lead_days + 1)}
        if any(fd.toordinal() in window for fd in fired_dates):
            detected += 1

    # false ambers = fired days not within any onset's lead window
    covered = set()
    for onset in onset_dates:
        for k in range(lead_days + 1):
            covered.add(onset.toordinal() - k)
    false_ambers = sum(1 for fd in fired_dates if fd.toordinal() not in covered)

    n_days = len(timeline)
    weeks = max(n_days / 7.0, 1e-9)
    false_per_week = false_ambers / weeks

    target_onsets = min(ACCEPT_MIN_ONSETS_DETECTED, len(onset_dates))
    passes = (
        len(onset_dates) >= 1
        and detected >= target_onsets
        and false_per_week <= ACCEPT_MAX_FALSE_AMBER_PER_WEEK
    )
    return {
        "onsets_tagged": len(onset_dates),
        "onsets_detected": detected,
        "false_ambers": false_ambers,
        "false_ambers_per_week": round(false_per_week, 2),
        "days_backtested": n_days,
        "acceptance": {
            "min_onsets_detected": target_onsets,
            "max_false_ambers_per_week": ACCEPT_MAX_FALSE_AMBER_PER_WEEK,
        },
        "passes": passes,
        "verdict": (
            "PASS — safe to arm the safety channel"
            if passes
            else "FAIL — do not fire into any channel until tuned"
        ),
    }

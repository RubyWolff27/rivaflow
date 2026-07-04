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

from statistics import median

AMBER_Z = 1.5
RED_Z = 2.0
MAD_SCALE = 1.4826  # scales MAD to a normal-consistent SD estimate

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


def evaluate_prevention(
    readings: dict[str, dict], today_is_sabbath: bool = False
) -> dict:
    """Fuse per-signal readings into a tier. `readings` maps signal name → {value, median, mad}; include only
    signals that have a baseline. Deterministic and DB-free. Sabbath does NOT silence this — it is the safety
    channel."""
    if "lnrmssd" not in readings and len(readings) < 2:
        return {
            "available": False,
            "reason": "Building baselines — need more covered days.",
        }

    family_worse: dict[str, float] = {}
    drivers: list[dict] = []
    for name, r in readings.items():
        if name not in SIGNAL_FAMILY:
            continue
        wz = robust_z(r["value"], r["median"], r["mad"], WORSE_WHEN[name])
        fam = SIGNAL_FAMILY[name]
        family_worse[fam] = max(family_worse.get(fam, float("-inf")), wz)
        drivers.append(
            {
                "signal": name,
                "family": fam,
                "worse_z": round(wz, 2),
                "flagged": wz >= AMBER_Z,
            }
        )

    flagged_families = [f for f, z in family_worse.items() if z >= AMBER_Z]
    strong_families = [f for f, z in family_worse.items() if z >= RED_Z]
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

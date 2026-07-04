"""B2 — Multi-input Readiness (the pure fusion core).

The daily "push vs rest" verdict Ruby actually asked for (WHOOP_FUTURE_STATE_PLAN.md B2). Reproduces the
WHOOP-Recovery / Fitbit-Daily-Readiness shape from the HR+RR we own: an HRV-led blend of deviation-from-
personal-baseline across four signals, every one scored on its OWN rolling baseline, never population norms.

Two review-mandated properties live here, not in the DB wiring, so they are unit-testable without a database:
  - HRV enters as **lnRMSSD** (log scale). RMSSD is right-skewed, so a Gaussian z on raw RMSSD over-flags
    low-HRV days and under-flags high ones (Plews/Buchheit; this was the B0/physiology critical fix).
  - Every green/in-range verdict carries the **"green ≠ healthy"** caveat — HR/HRV/breathing can read normal
    while a fever or hypoxic event (temperature + SpO2, both locked) is incubating.

Weights are HRV-led with sleep and respiratory rate deliberately down-weighted (resp-rate is our least-
validated signal — WHOOP_FUTURE_STATE_PLAN.md red team). Missing signals are renormalised away so a cold
start on one input doesn't distort the blend; HRV is required (it is the led signal).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev

# HRV-led; sleep + resp down-weighted (resp is needs-validation). Sum to 1.0 when all present.
WEIGHTS = {"hrv": 0.50, "rhr": 0.25, "sleep": 0.15, "resp": 0.10}

# Sign convention: +z on the raw metric → does it mean BETTER recovery (+1) or WORSE (-1)?
DIRECTION = {"hrv": +1, "rhr": -1, "sleep": +1, "resp": -1}

LABELS = {
    "hrv": "HRV (lnRMSSD)",
    "rhr": "Nocturnal resting HR",
    "sleep": "Sleep vs need",
    "resp": "Respiratory rate",
}

MIN_BASELINE_DAYS = 5  # cold-start guard before a signal's z-score is meaningful

GREEN_CAVEAT = (
    "Green means no deviation in the signals I can measure (HR, HRV, breathing) — "
    "I'm blind to temperature and blood oxygen, so trust your symptoms over a green light."
)


def zscore(values: list[float], window: int = 7) -> dict | None:
    """z-score of the latest value vs the personal baseline formed by the PRIOR `window` days.
    Returns None when there aren't enough prior days for a meaningful baseline. Pass values already on the
    intended scale (e.g. lnRMSSD, not RMSSD)."""
    if not values or len(values) < MIN_BASELINE_DAYS + 1:
        return None
    today = values[-1]
    prior = values[-(window + 1):-1]
    if len(prior) < MIN_BASELINE_DAYS:
        prior = values[:-1]
    b_mean = mean(prior)
    b_sd = pstdev(prior) or 1.0
    return {"z": (today - b_mean) / b_sd, "baseline_mean": b_mean, "baseline_sd": b_sd, "n": len(prior)}


@dataclass
class Contributor:
    signal: str
    label: str
    z: float                 # raw z on the metric
    weight: float            # renormalised weight actually applied
    ready_contribution: float  # signed, recovery-oriented contribution to the composite

    def as_dict(self) -> dict:
        return {
            "signal": self.signal,
            "label": self.label,
            "z": round(self.z, 2),
            "weight": round(self.weight, 3),
            "effect": round(self.ready_contribution, 3),
            "direction": "supports recovery" if self.ready_contribution >= 0 else "drags recovery",
        }


def blend_readiness(signal_z: dict[str, float | None], today_is_sabbath: bool = False) -> dict:
    """Fuse per-signal z-scores into one readiness verdict. `signal_z` maps signal name → raw z (or None if
    that signal has no baseline yet). HRV is required; the rest renormalise around what's available."""
    if today_is_sabbath:
        return {
            "state": "Rest",
            "headline": "Sabbath — rest is prescribed. No score today.",
            "driver": "sabbath",
            "score": None,
            "caveat": None,
        }

    if signal_z.get("hrv") is None:
        present = sum(1 for v in signal_z.values() if v is not None)
        return {
            "state": "Building",
            "headline": "Building your HRV baseline — need a few more days of resting RR.",
            "driver": "cold_start",
            "score": None,
            "signals_available": present,
            "caveat": None,
        }

    # Renormalise weights over the signals we actually have.
    available = {k: v for k, v in signal_z.items() if v is not None and k in WEIGHTS}
    wsum = sum(WEIGHTS[k] for k in available)
    contributors: list[Contributor] = []
    composite = 0.0
    for name, z in available.items():
        w = WEIGHTS[name] / wsum
        contribution = w * z * DIRECTION[name]
        composite += contribution
        contributors.append(Contributor(name, LABELS[name], z, w, contribution))

    # Bands on the recovery-oriented composite z (higher = more recovered).
    if composite >= 0.5:
        state, head = "Prime", "Above your baseline — green light to train hard."
    elif composite >= -0.5:
        state, head = "Balanced", "In your normal range — train as planned."
    elif composite >= -1.5:
        state, head = "Strained", "Below baseline — technical/skills over hard rolls today."
    else:
        state, head = "Rundown", "Well below baseline — prioritise recovery."

    contributors.sort(key=lambda c: abs(c.ready_contribution), reverse=True)
    caveat = GREEN_CAVEAT if state in ("Prime", "Balanced") else None

    return {
        "state": state,
        "headline": head,
        "driver": "multi_input_lnrmssd_led",
        "score": max(0, min(100, round(50 + composite * 20))),
        "composite_z": round(composite, 2),
        "contributors": [c.as_dict() for c in contributors],
        "signals_used": [c.signal for c in contributors],
        "caveat": caveat,
    }

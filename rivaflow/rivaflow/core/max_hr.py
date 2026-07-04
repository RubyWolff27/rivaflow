"""B1 — Personalised Max-HR calibration (the pure core).

Kills the hardcoded MAX_HR=190 that distorts every HR zone, strain, and stress value
(WHOOP_CURRENT_STATE.md §3; WHOOP_FUTURE_STATE_PLAN.md B1). 190 is a ~30yo default (220−30); Ruby's
age-predicted max is ~177 (Tanaka), so the old constant sat ~13 bpm too high and inflated every zone.

Two review-mandated guards live here:
  - **Artifact-rejected sustained plateau**, not a 1-sample spike. Optical HR throws motion/cadence-lock
    spikes; a lone high sample must NOT set max-HR. We take the highest HR *held continuously* for a
    plateau window (≥10 s), computed as the max over sliding windows of the window minimum.
  - **Sub-maximal floor + uncertainty band.** A low-endurance athlete who rarely reaches true max will
    under-observe HRmax, so when the observed sustained max sits below the age-predicted (Tanaka) value we
    treat it as a FLOOR and fall back to Tanaka, flagged — never silently trusting an under-estimate.
    Every estimate carries a band (Tanaka population SD ≈ ±10 bpm) because downstream zones inherit its error.
"""

from __future__ import annotations

from collections import deque

TANAKA_INTERCEPT = 208.0
TANAKA_SLOPE = 0.7
POP_SD = 10          # Tanaka population SD ≈ ±10 bpm — the honest band on a predicted max
OBSERVED_BAND = 5    # tighter band when we have a measured sustained max
DEFAULT_PLATEAU_SEC = 10
HR_FLOOR, HR_CEILING = 30, 220   # reject impossible readings before calibrating


def tanaka_max(age: float) -> float:
    """Age-predicted maximum HR (Tanaka 2001): 208 − 0.7·age. Population mean, SD ≈ ±10 bpm."""
    return TANAKA_INTERCEPT - TANAKA_SLOPE * age


def sustained_max(hr: list[int], window: int) -> int | None:
    """Highest HR held continuously for `window` samples = max over sliding windows of the window minimum.
    A 1-sample spike can't raise it (the rest of its window pulls the minimum down), so motion/cadence
    artifact is rejected. O(n) via a monotonic deque. Returns None if there aren't `window` samples."""
    if window <= 0 or len(hr) < window:
        return None
    dq: deque[int] = deque()   # indices, values increasing → front is the window minimum
    best: int | None = None
    for i, v in enumerate(hr):
        while dq and hr[dq[-1]] >= v:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - window:
            dq.popleft()
        if i >= window - 1:
            wmin = hr[dq[0]]
            if best is None or wmin > best:
                best = wmin
    return best


def calibrate_max_hr(hr_samples: list[int], age: float, plateau_sec: int = DEFAULT_PLATEAU_SEC,
                     hz: float = 1.0) -> dict:
    """Calibrate a personal max-HR from HR samples + age. Prefers an artifact-rejected observed sustained
    max when it exceeds the age-predicted value; otherwise falls back to Tanaka with the observed value
    flagged as a sub-maximal floor. Always returns a usable `max_hr` (Tanaka when no data)."""
    tanaka = tanaka_max(age)
    window = max(1, int(round(plateau_sec * hz)))
    hr = [int(x) for x in hr_samples if x is not None and HR_FLOOR <= int(x) <= HR_CEILING]
    observed = sustained_max(hr, window)

    if observed is not None and observed >= tanaka:
        estimate = float(observed)
        source, floor = "observed_sustained", False
        band = (float(observed - OBSERVED_BAND), float(observed + OBSERVED_BAND))
        note = "Observed sustained max at/above age-predicted — using the measured value."
    else:
        estimate = tanaka
        source = "tanaka_default"
        floor = observed is not None and observed < tanaka
        band = (tanaka - POP_SD, tanaka + POP_SD)
        if floor:
            note = (f"Observed sustained max {observed} is below age-predicted {round(tanaka)} — likely "
                    f"sub-maximal effort; treating observed as a floor and using the Tanaka estimate. "
                    f"One true max-effort test would anchor this.")
        else:
            note = "Not enough near-max effort captured — using the age-predicted (Tanaka) estimate."

    return {
        "max_hr": round(estimate),
        "source": source,
        "observed_sustained": observed,
        "tanaka": round(tanaka),
        "floor": floor,
        "uncertainty": [round(band[0]), round(band[1])],
        "plateau_sec": plateau_sec,
        "samples": len(hr),
        "note": note,
    }

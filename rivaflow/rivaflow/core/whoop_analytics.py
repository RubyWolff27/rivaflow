"""WHOOP analytics — Ruby Readiness Score + BJJ roll HR analytics.

Computed on-VPS from the whoop_* stream tables (Phase 2). Personal / n-of-1: every score is relative
to Ruby's OWN rolling baseline, not population norms. Cold-start returns a "building baseline" state
until enough data has accrued. Wrist-PPG HRV is only trustworthy at rest, so readiness uses at-rest
HRV only, and BJJ session analytics use HR (not HRV) because motion corrupts beat-to-beat intervals.
"""

from __future__ import annotations

from statistics import mean, pstdev

from rivaflow.db.repositories.whoop_repo import WhoopRepository

# Ruby's profile-tuned constants
MAX_HR = 190                      # HR-zone ceiling (44yo; refine from measured max later)
READINESS_MIN_BASELINE_DAYS = 5   # cold-start guard before a score is meaningful


def compute_readiness(user_id: int, today_is_sabbath: bool = False) -> dict:
    """Readiness from at-rest HRV vs the user's rolling 7-day baseline (Plews/Buchheit style).

    Sabbath-silent: on a rest day it blesses the rest instead of scoring. Conservative bands for a
    masters, NSAID-sensitive, low-endurance athlete — 'Strained' pushes toward technical work, not hard rolls.
    """
    if today_is_sabbath:
        return {"state": "Rest", "headline": "Sabbath — rest is prescribed. No score today.",
                "driver": "sabbath", "score": None}

    hrv = WhoopRepository.hrv_range(user_id, days=14, at_rest_only=True)
    vals = [h["rmssd"] for h in hrv if h.get("rmssd") is not None]
    if len(vals) < READINESS_MIN_BASELINE_DAYS:
        return {"state": "Building",
                "headline": f"Building your HRV baseline ({len(vals)}/{READINESS_MIN_BASELINE_DAYS} days).",
                "driver": "cold_start", "score": None, "samples": len(vals)}

    baseline = vals[-7:] if len(vals) >= 7 else vals
    b_mean = mean(baseline)
    b_sd = pstdev(baseline) or 1.0
    today = vals[-1]
    z = (today - b_mean) / b_sd

    if z >= 0.5:
        state, head = "Prime", "HRV above baseline — green light to train hard."
    elif z >= -0.5:
        state, head = "Balanced", "HRV in your normal range — train as planned."
    elif z >= -1.5:
        state, head = "Strained", "HRV below baseline — technical/skills over hard rolls today."
    else:
        state, head = "Rundown", "HRV well below baseline — prioritise recovery."

    return {
        "state": state, "headline": head, "driver": "hrv_vs_baseline",
        "score": max(0, min(100, round(50 + z * 20))),
        "today_rmssd": round(today, 1), "baseline_rmssd": round(b_mean, 1),
        "z": round(z, 2), "baseline_days": len(baseline),
    }


def hr_zone(bpm: int, max_hr: int = MAX_HR) -> int:
    """5-zone model (% of max HR)."""
    pct = bpm / max_hr
    if pct < 0.60:
        return 1
    if pct < 0.70:
        return 2
    if pct < 0.80:
        return 3
    if pct < 0.90:
        return 4
    return 5


def bjj_session_analytics(user_id: int, start_iso: str, end_iso: str) -> dict:
    """Per-session HR analytics for a BJJ window: time-in-zone, avg/max, and best between-round HR
    recovery (a hard fitness marker that improves as you progress). HR only — HRV is invalid in motion.
    Fields mirror RivaFlow's garmin_* session columns so WHOOP sessions sit beside Garmin.
    """
    hr = WhoopRepository.hr_range(user_id, start_iso, end_iso)
    bpms = [h["bpm"] for h in hr if h.get("bpm")]
    if not bpms:
        return {"available": False,
                "reason": "No HR captured in this window — reboot the strap before the next session."}

    zone_secs = {z: 0 for z in range(1, 6)}
    for b in bpms:
        zone_secs[hr_zone(b)] += 1   # standard-HR stream is ~1 sample/sec

    # Best 60s HR drop after a peak — approximates between-round recovery.
    best_recovery = 0
    for i in range(len(bpms)):
        window = bpms[i:i + 60]
        if len(window) >= 30:
            best_recovery = max(best_recovery, window[0] - min(window))

    return {
        "available": True,
        "avg_hr": round(mean(bpms)),
        "max_hr": max(bpms),
        "duration_sec": len(bpms),
        "hr_zone_secs": zone_secs,
        "best_60s_hr_recovery": best_recovery,
        "samples": len(bpms),
    }

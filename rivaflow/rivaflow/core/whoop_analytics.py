"""WHOOP analytics — Ruby Readiness Score + BJJ roll HR analytics.

Computed on-VPS from the whoop_* stream tables (Phase 2). Personal / n-of-1: every score is relative
to Ruby's OWN rolling baseline, not population norms. Cold-start returns a "building baseline" state
until enough data has accrued. Wrist-PPG HRV is only trustworthy at rest, so readiness uses at-rest
HRV only, and BJJ session analytics use HR (not HRV) because motion corrupts beat-to-beat intervals.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt
from statistics import mean, pstdev

from rivaflow.db.repositories.whoop_repo import WhoopRepository

# Ruby's profile-tuned constants
MAX_HR = 190                      # HR-zone ceiling (44yo; refine from measured max later)
READINESS_MIN_BASELINE_DAYS = 5   # cold-start guard before a score is meaningful


def _parse_ts(ts: str) -> datetime:
    """Parse a stored ISO timestamp (handles trailing Z)."""
    return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))


def daily_resting_hr(user_id: int, days: int = 14) -> list[dict]:
    """Per-day resting HR ≈ the 5th-percentile of the day's HR — a robust resting proxy from whoop_hr
    (the true minimum is noisy). Needs >=60 samples/day. Falls out of the HR stream we already capture,
    so no extra plumbing."""
    hr = WhoopRepository.recent_hr(user_id, hours=days * 24)
    by_day: dict[str, list[int]] = defaultdict(list)
    for h in hr:
        bpm, ts = h.get("bpm"), h.get("ts")
        if bpm and ts:
            by_day[str(ts)[:10]].append(int(bpm))
    out: list[dict] = []
    for day in sorted(by_day):
        vals = sorted(by_day[day])
        if len(vals) < 60:
            continue
        idx = max(0, int(len(vals) * 0.05))
        out.append({"day": day, "resting_hr": vals[idx], "min_hr": vals[0], "samples": len(vals)})
    return out


def _longest_low_block(order: list[int], med: dict, threshold: int, max_bridge: int) -> tuple:
    """Longest run of 'asleep' buckets (median <= threshold), bridging up to max_bridge awake buckets.
    Returns (start_idx, end_idx, span) or (None, None, 0)."""
    best_s = best_e = None
    best_span = 0
    cur_s = cur_e = None
    gap = 0
    for i in order:
        if med[i] <= threshold:
            cur_s = i if cur_s is None else cur_s
            cur_e = i
            gap = 0
        elif cur_s is not None:
            gap += 1
            if gap > max_bridge:
                if cur_e - cur_s > best_span:
                    best_span, best_s, best_e = cur_e - cur_s, cur_s, cur_e
                cur_s = cur_e = None
                gap = 0
    if cur_s is not None and cur_e - cur_s > best_span:
        best_span, best_s, best_e = cur_e - cur_s, cur_s, cur_e
    return best_s, best_e, best_span


def nightly_sleep(user_id: int, lookback_hours: int = 20) -> dict:
    """Estimate last night's sleep from the overnight HR pattern. HR drops and stays low during sleep.
    Robust to real fluctuation + gaps: bins HR into 5-min buckets (median), flags a bucket 'asleep' when
    its median is within ~12 bpm of the night's lowest bucket, then finds the longest sleep block —
    bridging brief wakes (up to ~15 min of higher HR) so a single toss-and-turn doesn't split the night.
    Honest HR-based sleep DURATION + timing, NOT WHOOP-style staging (which needs a proprietary model)."""
    hr = WhoopRepository.recent_hr(user_id, hours=lookback_hours)
    pts = [(_parse_ts(str(h["ts"])), int(h["bpm"])) for h in hr if h.get("bpm") and h.get("ts")]
    if len(pts) < 120:
        return {"available": False, "reason": "Not enough overnight HR captured for a sleep estimate yet."}
    pts.sort(key=lambda p: p[0])

    t0 = pts[0][0]
    bucket_bpms: dict[int, list[int]] = defaultdict(list)
    bucket_time: dict[int, datetime] = {}
    for t, b in pts:
        idx = int((t - t0).total_seconds() // 300)   # 5-minute bucket
        bucket_bpms[idx].append(b)
        bucket_time.setdefault(idx, t)
    order = sorted(bucket_bpms)
    med = {i: sorted(bucket_bpms[i])[len(bucket_bpms[i]) // 2] for i in order}

    threshold = min(med.values()) + 12               # "asleep" band above the night's quietest bucket
    best_s, best_e, best_span = _longest_low_block(order, med, threshold, max_bridge=3)

    if best_s is None or best_span < 6:              # < ~30 min → not a real sleep block
        return {"available": False, "reason": "No sustained overnight low-HR sleep window detected."}

    start_t, end_t = bucket_time[best_s], bucket_time[best_e]
    duration_hours = (end_t - start_t).total_seconds() / 3600
    sleep_bpms = [b for i in order if best_s <= i <= best_e for b in bucket_bpms[i]]
    return {
        "available": True,
        "sleep_start": start_t.isoformat(),
        "sleep_end": end_t.isoformat(),
        "duration_hours": round(duration_hours, 1),
        "avg_sleeping_hr": round(mean(sleep_bpms)),
        "min_hr": min(sleep_bpms),
        "source": "hr_bucketed_window",
        "method": "HR-based sleep duration/timing (not WHOOP staging).",
    }


def whoop_summary(user_id: int, today_is_sabbath: bool = False) -> dict:
    """One-call rollup for a thin display client: readiness + HRV (today+trend) + resting HR (today+trend)
    + last night's sleep. The phone/dashboard fetches THIS and just renders it — no client-side compute."""
    hrv = daily_resting_rmssd(user_id, days=14)
    rhr = daily_resting_hr(user_id, days=14)
    return {
        "readiness": compute_readiness(user_id, today_is_sabbath=today_is_sabbath),
        "hrv_today": hrv[-1] if hrv else None,
        "hrv_trend": hrv,
        "resting_hr_today": rhr[-1] if rhr else None,
        "resting_hr_trend": rhr,
        "sleep": nightly_sleep(user_id),
    }


def daily_resting_rmssd(user_id: int, days: int = 21) -> list[dict]:
    """Per-day resting HRV (RMSSD, ms) derived from the whoop_rr intervals already flowing — so
    readiness works without a separate HRV feed. 'Resting' = RR in a plausible band (HR ~40-90 bpm →
    667-1500 ms); successive-difference outliers (>400 ms, i.e. motion/ectopy) are dropped. Needs
    >=20 resting intervals/day. RMSSD = sqrt(mean of squared successive RR differences)."""
    rr = WhoopRepository.rr_range(user_id, days)
    by_day: dict[str, list[int]] = defaultdict(list)
    for r in rr:
        rr_ms, ts = r.get("rr_ms"), r.get("ts")
        if rr_ms and ts and 667 <= rr_ms <= 1500:
            by_day[str(ts)[:10]].append(rr_ms)
    out: list[dict] = []
    for day in sorted(by_day):
        vals = by_day[day]
        if len(vals) < 20:
            continue
        diffs = [vals[i + 1] - vals[i] for i in range(len(vals) - 1) if abs(vals[i + 1] - vals[i]) < 400]
        if len(diffs) < 10:
            continue
        out.append({"day": day, "rmssd": round(sqrt(sum(d * d for d in diffs) / len(diffs)), 1)})
    return out


def compute_readiness(user_id: int, today_is_sabbath: bool = False) -> dict:
    """Readiness from at-rest HRV vs the user's rolling 7-day baseline (Plews/Buchheit style).

    Sabbath-silent: on a rest day it blesses the rest instead of scoring. Conservative bands for a
    masters, NSAID-sensitive, low-endurance athlete — 'Strained' pushes toward technical work, not hard rolls.
    """
    if today_is_sabbath:
        return {"state": "Rest", "headline": "Sabbath — rest is prescribed. No score today.",
                "driver": "sabbath", "score": None}

    # Derive daily resting RMSSD from the RR intervals already flowing (no separate HRV feed needed).
    daily = daily_resting_rmssd(user_id, days=21)
    vals = [d["rmssd"] for d in daily]
    if len(vals) < READINESS_MIN_BASELINE_DAYS:
        return {"state": "Building",
                "headline": f"Building your HRV baseline ({len(vals)}/{READINESS_MIN_BASELINE_DAYS} days).",
                "driver": "cold_start", "score": None, "samples": len(vals)}

    today = vals[-1]
    prior = vals[-8:-1] if len(vals) >= 8 else vals[:-1]   # baseline = the days BEFORE today
    b_mean = mean(prior)
    b_sd = pstdev(prior) or 1.0
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
        "z": round(z, 2), "baseline_days": len(prior), "source": "rr_derived",
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

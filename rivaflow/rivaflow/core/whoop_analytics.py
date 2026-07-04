"""WHOOP analytics — Ruby Readiness Score + BJJ roll HR analytics.

Computed on-VPS from the whoop_* stream tables (Phase 2). Personal / n-of-1: every score is relative
to Ruby's OWN rolling baseline, not population norms. Cold-start returns a "building baseline" state
until enough data has accrued. Wrist-PPG HRV is only trustworthy at rest, so readiness uses at-rest
HRV only, and BJJ session analytics use HR (not HRV) because motion corrupts beat-to-beat intervals.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import log1p
from statistics import mean, pstdev
from zoneinfo import ZoneInfo

from rivaflow.core.rr_quality import assess_rr, ln_rmssd, rmssd
from rivaflow.db.repositories.whoop_repo import WhoopRepository

# Ruby's profile-tuned constants
MAX_HR = 190                      # HR-zone ceiling (44yo; refine from measured max later)
READINESS_MIN_BASELINE_DAYS = 5   # cold-start guard before a score is meaningful

# Ruby is Melbourne-based. All day-bucketing + display use his local day, not UTC (which would split the
# day at ~10am and skew daily HRV/resting-HR). TODO(travel): switch to the device-reported tz per-ingest.
LOCAL_TZ = ZoneInfo("Australia/Melbourne")


def _parse_ts(ts: str) -> datetime:
    """Parse a stored ISO timestamp (handles trailing Z), returning a tz-aware datetime."""
    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=ZoneInfo("UTC"))


def _local_day(ts) -> str:
    """UTC timestamp → Ruby's LOCAL (Melbourne) calendar day 'YYYY-MM-DD' — so a day is his day."""
    try:
        dt = ts if isinstance(ts, datetime) else _parse_ts(str(ts))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(LOCAL_TZ).date().isoformat()
    except (ValueError, TypeError):
        return str(ts)[:10]


def daily_resting_hr(user_id: int, days: int = 14) -> list[dict]:
    """Per-day resting HR ≈ the 5th-percentile of the day's HR — a robust resting proxy from whoop_hr
    (the true minimum is noisy). Needs >=60 samples/day. Falls out of the HR stream we already capture,
    so no extra plumbing."""
    hr = WhoopRepository.recent_hr(user_id, hours=days * 24)
    by_day: dict[str, list[int]] = defaultdict(list)
    for h in hr:
        bpm, ts = h.get("bpm"), h.get("ts")
        if bpm and ts:
            by_day[_local_day(ts)].append(int(bpm))
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
    """One-call rollup for a thin display client: everything the VPS computes, so the phone/dashboard
    fetches THIS and just renders it — no client-side compute. Readiness, HRV, resting HR, sleep (+quality),
    respiratory rate, cardio load/strain, and stress — benchmarked against WHOOP/Oura/Hume, all from the
    HR+RR we already capture."""
    hrv = daily_resting_rmssd(user_id, days=14)
    rhr = daily_resting_hr(user_id, days=14)
    cardio = daily_cardio_load(user_id, days=7)
    sleep = nightly_sleep(user_id)
    if sleep.get("available"):
        # Simple quality score vs Ruby's >9h sleep-need (DNA): duration is the dominant driver.
        sleep["quality_score"] = max(0, min(100, round((sleep["duration_hours"] / 9.0) * 100)))
    return {
        "readiness": compute_readiness(user_id, today_is_sabbath=today_is_sabbath),
        "hrv_today": hrv[-1] if hrv else None,
        "hrv_trend": hrv,
        "resting_hr_today": rhr[-1] if rhr else None,
        "resting_hr_trend": rhr,
        "sleep": sleep,
        "respiratory_rate": respiratory_rate(user_id),
        "cardio_load_today": cardio[-1] if cardio else None,
        "cardio_load_trend": cardio,
        "stress": today_stress(user_id),
    }


def daily_resting_rmssd(user_id: int, days: int = 21) -> list[dict]:
    """Per-day resting HRV (RMSSD, ms) derived from the whoop_rr intervals already flowing — so readiness
    works without a separate HRV feed. Every day's series passes through the B0 QC gate (rr_quality):
    a widened bradycardia band (36-133 bpm) + Malik-style relative (>20%) artifact filter + ectopy
    interpolation, replacing the old fixed 667-1500 ms band and absolute <400 ms drop. Each value carries
    its artifact-% and only days within the artifact budget are emitted."""
    rr = WhoopRepository.rr_range(user_id, days)
    by_day: dict[str, list[int]] = defaultdict(list)
    for r in rr:
        rr_ms, ts = r.get("rr_ms"), r.get("ts")
        if rr_ms and ts:
            by_day[_local_day(ts)].append(int(rr_ms))
    out: list[dict] = []
    for day in sorted(by_day):
        q = assess_rr(by_day[day])
        if not q.usable:
            continue
        value = rmssd(q.cleaned)
        if value is None:
            continue
        out.append({
            "day": day,
            "rmssd": round(value, 1),
            "ln_rmssd": round(ln_rmssd(q.cleaned), 3),
            "quality": q.as_meta(),
        })
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


def respiratory_rate(user_id: int, days: int = 1) -> dict:
    """Respiratory rate from RR-interval oscillation (respiratory sinus arrhythmia): the heart speeds up
    on inhale and slows on exhale, so the resting RR series oscillates at the breathing frequency. We
    detrend the resting RR tachogram (subtract a centred moving average) and count breathing cycles.
    Oura/WHOOP surface this — and it IS computable from the RR we already capture, no extra sensor."""
    rr = WhoopRepository.rr_range(user_id, days)
    vals = [int(r["rr_ms"]) for r in rr if r.get("rr_ms") and 667 <= r["rr_ms"] <= 1500]
    if len(vals) < 120:
        return {"available": False, "reason": "Not enough resting RR intervals for a respiratory estimate."}

    window = 10
    osc = []
    for i in range(len(vals)):
        lo, hi = max(0, i - window // 2), min(len(vals), i + window // 2 + 1)
        osc.append(vals[i] - sum(vals[lo:hi]) / (hi - lo))
    breaths = sum(1 for i in range(1, len(osc)) if osc[i - 1] < 0 <= osc[i])   # one up-crossing per breath
    minutes = sum(vals) / 60000.0
    if minutes < 2 or breaths < 4:
        return {"available": False, "reason": "Insufficient signal for a respiratory estimate."}
    rpm = breaths / minutes
    if not (6 <= rpm <= 30):
        return {"available": False, "reason": "Respiratory estimate out of plausible range."}
    return {"available": True, "respiratory_rate": round(rpm, 1), "breaths": breaths,
            "minutes": round(minutes, 1), "source": "rr_rsa"}


def daily_cardio_load(user_id: int, days: int = 7) -> list[dict]:
    """Daily cardio load / strain from HR-zone-weighted minutes (Banister-TRIMP style), hard zones
    weighted exponentially, compressed to a ~0–21 scale (WHOOP-strain feel). From the HR we capture."""
    hr = WhoopRepository.recent_hr(user_id, hours=days * 24)
    zone_weight = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
    by_day: dict[str, float] = defaultdict(float)
    for h in hr:
        bpm, ts = h.get("bpm"), h.get("ts")
        if bpm and ts:
            by_day[_local_day(ts)] += zone_weight[hr_zone(int(bpm))] / 60.0   # ~1 sample/s → per-minute
    out = []
    for day in sorted(by_day):
        raw = by_day[day]
        out.append({"day": day, "cardio_load": round(min(21.0, 6.0 * log1p(raw / 20.0)), 1),
                    "raw_trimp": round(raw, 1)})
    return out


def today_stress(user_id: int) -> dict:
    """Light stress proxy: how elevated recent HR sits within the HR reserve above resting (0–100).
    WHOOP/Hume blend HRV+HR; this HR-elevation version is honest and always-available."""
    recent = WhoopRepository.recent_hr(user_id, hours=1)
    bpms = [int(h["bpm"]) for h in recent if h.get("bpm")]
    rhr_list = daily_resting_hr(user_id, days=3)
    if not bpms or not rhr_list:
        return {"available": False, "reason": "Not enough recent HR for a stress estimate."}
    rest = rhr_list[-1]["resting_hr"]
    cur = mean(bpms[-60:]) if len(bpms) >= 60 else mean(bpms)
    stress = max(0, min(100, round((cur - rest) / max(1, MAX_HR - rest) * 100)))
    return {"available": True, "stress": stress, "current_hr": round(cur), "resting_hr": rest}

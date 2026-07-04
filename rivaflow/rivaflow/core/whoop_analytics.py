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
from statistics import mean
from zoneinfo import ZoneInfo

from rivaflow.core.coverage import assess_coverage, coverage_in_days
from rivaflow.core.hrv_spectral import MIN_BEATS, frequency_domain, poincare
from rivaflow.core.max_hr import calibrate_max_hr
from rivaflow.core.prevention import evaluate_prevention, robust_baseline
from rivaflow.core.readiness import blend_readiness, zscore
from rivaflow.core.rr_quality import assess_rr, clean_segments, ln_rmssd, rmssd
from rivaflow.core.strain_target import prescribe_strain
from rivaflow.db.repositories.whoop_repo import WhoopRepository

# Ruby's profile-tuned constants
RUBY_AGE = 44                     # TODO(profile): derive from DOB 1982-05-27 once wired to the profile repo
MAX_HR = 190                      # FALLBACK ONLY — real ceiling comes from user_max_hr() (B1). Kept so
                                  # hr_zone() has a default; a ~30yo value, ~13 bpm above Ruby's ~177.
READINESS_MIN_BASELINE_DAYS = 5   # cold-start guard before a score is meaningful


def user_max_hr(user_id: int, days: int = 90) -> dict:
    """B1 — Ruby's calibrated max-HR from recent HR: artifact-rejected sustained plateau, Tanaka sanity band,
    sub-maximal floor flag, uncertainty band. Everything zone/strain/stress derived should use this, not the
    MAX_HR fallback. Falls back to the age-predicted value when there isn't enough near-max effort captured."""
    hr = [int(h["bpm"]) for h in WhoopRepository.recent_hr(user_id, hours=days * 24) if h.get("bpm")]
    return calibrate_max_hr(hr, RUBY_AGE)

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
    max_hr = user_max_hr(user_id)                 # B1 — compute once, thread into every HR-zone consumer
    readiness = compute_readiness(user_id, today_is_sabbath=today_is_sabbath)
    hrv = daily_resting_rmssd(user_id, days=14)
    rhr = daily_resting_hr(user_id, days=14)
    cardio = daily_cardio_load(user_id, days=14, max_hr=max_hr["max_hr"])
    sleep = nightly_sleep(user_id)
    if sleep.get("available"):
        # Simple quality score vs Ruby's >9h sleep-need (DNA): duration is the dominant driver.
        sleep["quality_score"] = max(0, min(100, round((sleep["duration_hours"] / 9.0) * 100)))
    acute = cardio[-1]["cardio_load"] if cardio else None
    strain = prescribe_strain(readiness.get("state"), _chronic_load(cardio), acute)
    return {
        "readiness": readiness,
        "strain_target": strain,
        "hrv_today": hrv[-1] if hrv else None,
        "hrv_trend": hrv,
        "resting_hr_today": rhr[-1] if rhr else None,
        "resting_hr_trend": rhr,
        "sleep": sleep,
        "respiratory_rate": respiratory_rate(user_id),
        "cardio_load_today": cardio[-1] if cardio else None,
        "cardio_load_trend": cardio,
        "stress": today_stress(user_id, max_hr=max_hr["max_hr"]),
        "coverage": capture_coverage(user_id, days=21),
        "max_hr": max_hr,
    }


def _chronic_load(cardio: list[dict]) -> float | None:
    """Chronic (usual) daily strain = mean of recent daily cardio-load, EXCLUDING today (the day in progress
    shouldn't lower its own target). Needs a few days to be meaningful; None otherwise."""
    prior = [c["cardio_load"] for c in cardio[:-1]] if len(cardio) > 1 else []
    return round(mean(prior), 1) if len(prior) >= 3 else None


def strain_target(user_id: int, today_is_sabbath: bool = False) -> dict:
    """B5 — standalone strain-target endpoint: today's readiness → prescribed daily 0–21 load, capped when
    Strained. (whoop_summary computes this inline from shared data; this is the direct-call path for /whoop.)"""
    readiness = compute_readiness(user_id, today_is_sabbath=today_is_sabbath)
    cardio = daily_cardio_load(user_id, days=14)
    acute = cardio[-1]["cardio_load"] if cardio else None
    return prescribe_strain(readiness.get("state"), _chronic_load(cardio), acute)


def _signal_reading(series: list[float]) -> dict | None:
    """Today's value + a robust (median/MAD) baseline from the PRIOR days — the shape the prevention engine
    consumes. Returns None until there's a baseline."""
    if len(series) < 6:
        return None
    base = robust_baseline(series[:-1])
    if base is None:
        return None
    return {"value": series[-1], "median": base["median"], "mad": base["mad"]}


def prevention_watch(user_id: int, days: int = 21) -> dict:
    """B6 — Baseline-Deviation Watch. Builds robust per-signal baselines from the coverage-gated daily series
    and evaluates co-occurrence across signal families. Fires on the safety channel (incl. Sunday). The four
    signals (no cardiac rhythm): RHR + sleeping-HR (nocturnal-HR family), lnRMSSD (vagal), resp-rate (respiratory)."""
    rhr = [d["resting_hr"] for d in daily_resting_hr(user_id, days=days)]
    lnr = [d["ln_rmssd"] for d in daily_resting_rmssd(user_id, days=days)]
    resp = [d["respiratory_rate"] for d in daily_respiratory_rate(user_id, days=days)]

    readings: dict[str, dict] = {}
    for name, series in (("rhr", rhr), ("lnrmssd", lnr), ("resp_rate", resp)):
        r = _signal_reading([float(x) for x in series])
        if r is not None:
            readings[name] = r
    return evaluate_prevention(readings)


def hrv_lab(user_id: int, days: int = 2) -> dict:
    """B4 — frequency-domain + non-linear HRV (web deep-dive 'HRV Lab'). Picks the longest clean, contiguous
    resting-RR segment from recent nights and runs Lomb-Scargle spectral + Poincaré on it — only if it clears
    the ≥5-min / ≥150-beat bar. Artifact-% travels with the result (HF band carries beat-detection jitter)."""
    rr = [int(r["rr_ms"]) for r in WhoopRepository.rr_range(user_id, days) if r.get("rr_ms")]
    resting = [v for v in rr if 667 <= v <= 1500]
    segments = clean_segments(resting, min_len=MIN_BEATS)
    if not segments:
        return {"available": False, "reason": "No contiguous resting RR segment of ≥150 beats yet."}
    seg = max(segments, key=sum)                       # longest by total time
    fseg = [float(v) for v in seg]
    fd = frequency_domain(fseg)
    if fd is None:
        return {"available": False, "reason": "Longest clean segment is under the 5-min stationary window."}
    pc = poincare(fseg)
    return {
        "available": True,
        "frequency_domain": fd.as_dict(),
        "poincare": pc.as_dict() if pc else None,
        "quality": assess_rr(seg).as_meta(),
    }


def _rr_by_day(user_id: int, days: int) -> dict[str, list[int]]:
    """All whoop_rr intervals bucketed by Ruby's local day (any band — band filtering happens downstream)."""
    by_day: dict[str, list[int]] = defaultdict(list)
    for r in WhoopRepository.rr_range(user_id, days):
        rr_ms, ts = r.get("rr_ms"), r.get("ts")
        if rr_ms and ts:
            by_day[_local_day(ts)].append(int(rr_ms))
    return by_day


def _hr_count_by_day(user_id: int, days: int) -> dict[str, int]:
    """HR sample count per local day — the HR-coverage side of the B3 guard (contrast against RR minutes)."""
    counts: dict[str, int] = defaultdict(int)
    for h in WhoopRepository.recent_hr(user_id, hours=days * 24):
        if h.get("bpm") and h.get("ts"):
            counts[_local_day(h["ts"])] += 1
    return counts


def daily_resting_rmssd(user_id: int, days: int = 21) -> list[dict]:
    """Per-day resting HRV (RMSSD, ms) derived from the whoop_rr intervals already flowing — so readiness
    works without a separate HRV feed. Each day passes TWO gates before it can anchor a baseline: the B3
    coverage guard (enough usable, contiguous RR — excludes RR-starved charging nights the HR view masks)
    and the B0 QC gate (widened bradycardia band + Malik relative filter + ectopy interpolation). Each value
    carries its artifact-% and RR-minutes; under-covered or over-artifact days are dropped."""
    by_day = _rr_by_day(user_id, days)
    hr_counts = _hr_count_by_day(user_id, days)
    out: list[dict] = []
    for day in sorted(by_day):
        cov = assess_coverage(by_day[day], hr_counts.get(day, 0))
        if not cov.sufficient:
            continue
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
            "coverage": cov.as_dict(),
        })
    return out


def compute_readiness(user_id: int, today_is_sabbath: bool = False) -> dict:
    """B2 — Multi-input Readiness. An lnRMSSD-led blend of four deviation-from-baseline signals (HRV, nocturnal
    resting HR, sleep-vs-need, respiratory rate), each scored on the user's OWN rolling baseline. The fusion
    math + the 'green ≠ healthy' caveat live in rivaflow.core.readiness (pure, unit-tested); this function only
    gathers the series. Sabbath-silent; cold-start returns 'Building' until HRV has a baseline. Conservative
    bands for a masters, NSAID-sensitive, low-endurance athlete — 'Strained' pushes toward technical work."""
    if today_is_sabbath:
        return blend_readiness({}, today_is_sabbath=True)

    # Each series is oldest→newest; the QC gate (B0) already sits inside the HRV/resp helpers.
    ln_series = [d["ln_rmssd"] for d in daily_resting_rmssd(user_id, days=21)]
    rhr_series = [d["resting_hr"] for d in daily_resting_hr(user_id, days=21)]
    resp_series = [d["respiratory_rate"] for d in daily_respiratory_rate(user_id, days=21)]

    hrv_z = zscore(ln_series)
    rhr_z = zscore(rhr_series)
    resp_z = zscore(resp_series)

    # Sleep is a down-weighted proxy vs the >9h DNA need (a personal sleep-need/debt baseline is B9).
    sleep = nightly_sleep(user_id)
    sleep_z = None
    if sleep.get("available"):
        sleep_z = max(-3.0, min(2.0, (sleep["duration_hours"] - 9.0) / 1.5))

    result = blend_readiness({
        "hrv": hrv_z["z"] if hrv_z else None,
        "rhr": rhr_z["z"] if rhr_z else None,
        "resp": resp_z["z"] if resp_z else None,
        "sleep": sleep_z,
    })
    if hrv_z:   # surface the led signal's provenance for the deep-dive
        result["today_ln_rmssd"] = round(ln_series[-1], 3)
        result["hrv_baseline"] = {"ln_mean": round(hrv_z["baseline_mean"], 3), "days": hrv_z["n"]}
    result["source"] = "rr_derived"
    return result


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


def bjj_session_analytics(user_id: int, start_iso: str, end_iso: str, max_hr: int | None = None) -> dict:
    """Per-session HR analytics for a BJJ window: time-in-zone, avg/max, and best between-round HR
    recovery (a hard fitness marker that improves as you progress). HR only — HRV is invalid in motion.
    Fields mirror RivaFlow's garmin_* session columns so WHOOP sessions sit beside Garmin. Zones use the
    B1-calibrated max-HR (not the 190 fallback).
    """
    hr = WhoopRepository.hr_range(user_id, start_iso, end_iso)
    bpms = [h["bpm"] for h in hr if h.get("bpm")]
    if not bpms:
        return {"available": False,
                "reason": "No HR captured in this window — reboot the strap before the next session."}

    mx = max_hr or user_max_hr(user_id)["max_hr"]
    zone_secs = {z: 0 for z in range(1, 6)}
    for b in bpms:
        zone_secs[hr_zone(b, mx)] += 1   # standard-HR stream is ~1 sample/sec

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


def _resp_rpm(vals: list[int]) -> float | None:
    """Breaths/min from a resting RR series via respiratory sinus arrhythmia: the heart speeds up on inhale
    and slows on exhale, so the resting tachogram oscillates at the breathing frequency. Detrend (subtract a
    centred moving average) and count up-crossings. Returns None if the signal is too short/implausible.
    ⚠️ Crude RSA estimate (needs-validation; a band-pass upgrade is future work) — down-weighted in readiness."""
    if len(vals) < 120:
        return None
    window = 10
    osc = []
    for i in range(len(vals)):
        lo, hi = max(0, i - window // 2), min(len(vals), i + window // 2 + 1)
        osc.append(vals[i] - sum(vals[lo:hi]) / (hi - lo))
    breaths = sum(1 for i in range(1, len(osc)) if osc[i - 1] < 0 <= osc[i])   # one up-crossing per breath
    minutes = sum(vals) / 60000.0
    if minutes < 2 or breaths < 4:
        return None
    rpm = breaths / minutes
    return rpm if 6 <= rpm <= 30 else None


def respiratory_rate(user_id: int, days: int = 1) -> dict:
    """Today's respiratory rate from the resting RR tachogram (RSA). Oura/WHOOP surface this and it IS
    computable from the RR we already capture, no extra sensor — but see the needs-validation caveat in _resp_rpm."""
    rr = WhoopRepository.rr_range(user_id, days)
    vals = [int(r["rr_ms"]) for r in rr if r.get("rr_ms") and 667 <= r["rr_ms"] <= 1500]
    clean = assess_rr(vals).cleaned
    rpm = _resp_rpm([int(v) for v in clean])
    if rpm is None:
        return {"available": False, "reason": "Not enough clean resting RR for a respiratory estimate."}
    return {"available": True, "respiratory_rate": round(rpm, 1),
            "minutes": round(sum(clean) / 60000.0, 1), "source": "rr_rsa"}


def daily_respiratory_rate(user_id: int, days: int = 21) -> list[dict]:
    """Per-day resting respiratory rate — the baseline series the B2 readiness blend needs for its
    (down-weighted) resp-rate signal. Gated by the B3 coverage guard (same as HRV) so RR-starved nights are
    excluded; the estimate itself uses the tighter 667–1500 ms resting band the RSA method needs."""
    by_day = _rr_by_day(user_id, days)
    hr_counts = _hr_count_by_day(user_id, days)
    out: list[dict] = []
    for day in sorted(by_day):
        if not assess_coverage(by_day[day], hr_counts.get(day, 0)).sufficient:
            continue
        resting = [v for v in by_day[day] if 667 <= v <= 1500]
        clean = assess_rr(resting).cleaned
        rpm = _resp_rpm([int(v) for v in clean])
        if rpm is not None:
            out.append({"day": day, "respiratory_rate": round(rpm, 1)})
    return out


def capture_coverage(user_id: int, days: int = 21) -> dict:
    """B3 surface — per-day RR/HR coverage + a coverage-in-days summary for the Data-integrity panel. This is
    the number that governs whether time-baseline builds can trust their baseline. RR is measured separately
    from HR precisely so a charging-away night (HR backfilled, RR missing) shows up as a gap, not false health."""
    by_day = _rr_by_day(user_id, days)
    hr_counts = _hr_count_by_day(user_id, days)
    all_days = sorted(set(by_day) | set(hr_counts))
    reports = [assess_coverage(by_day.get(day, []), hr_counts.get(day, 0)) for day in all_days]
    return {
        "summary": coverage_in_days(reports),
        "days": [{"day": day, **rep.as_dict()} for day, rep in zip(all_days, reports)],
    }


def daily_cardio_load(user_id: int, days: int = 7, max_hr: int | None = None) -> list[dict]:
    """Daily cardio load / strain from HR-zone-weighted minutes (Banister-TRIMP style), hard zones
    weighted exponentially, compressed to a ~0–21 scale (WHOOP-strain feel). Zones use the B1-calibrated
    max-HR (not the 190 fallback), so the strain scale is correct for Ruby."""
    hr = WhoopRepository.recent_hr(user_id, hours=days * 24)
    mx = max_hr or user_max_hr(user_id)["max_hr"]
    zone_weight = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
    by_day: dict[str, float] = defaultdict(float)
    for h in hr:
        bpm, ts = h.get("bpm"), h.get("ts")
        if bpm and ts:
            by_day[_local_day(ts)] += zone_weight[hr_zone(int(bpm), mx)] / 60.0   # ~1 sample/s → per-minute
    out = []
    for day in sorted(by_day):
        raw = by_day[day]
        out.append({"day": day, "cardio_load": round(min(21.0, 6.0 * log1p(raw / 20.0)), 1),
                    "raw_trimp": round(raw, 1)})
    return out


def today_stress(user_id: int, max_hr: int | None = None) -> dict:
    """Light stress proxy: how elevated recent HR sits within the HR reserve above resting (0–100).
    WHOOP/Hume blend HRV+HR; this HR-elevation version is honest and always-available. Reserve uses the
    B1-calibrated max-HR (not the 190 fallback)."""
    recent = WhoopRepository.recent_hr(user_id, hours=1)
    bpms = [int(h["bpm"]) for h in recent if h.get("bpm")]
    rhr_list = daily_resting_hr(user_id, days=3)
    if not bpms or not rhr_list:
        return {"available": False, "reason": "Not enough recent HR for a stress estimate."}
    mx = max_hr or user_max_hr(user_id)["max_hr"]
    rest = rhr_list[-1]["resting_hr"]
    cur = mean(bpms[-60:]) if len(bpms) >= 60 else mean(bpms)
    stress = max(0, min(100, round((cur - rest) / max(1, mx - rest) * 100)))
    return {"available": True, "stress": stress, "current_hr": round(cur), "resting_hr": rest}

"""Risk assessment and summary generation for insights analytics.

Overtraining risk scoring, recovery insights, and digest summary.
"""

import statistics
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from rivaflow.core.services.insights_math import (
    _linear_slope,
    _pearson_r,
)
from rivaflow.db.repositories import (
    ReadinessRepository,
    SessionRepository,
)


def compute_overtraining_risk(
    session_repo: SessionRepository,
    readiness_repo: ReadinessRepository,
    get_training_load_fn,
    user_id: int,
) -> dict[str, Any]:
    """6 factors = 0-100 risk score (20+20+15+15+15+15)."""
    end = date.today()
    start_14d = end - timedelta(days=14)
    start_7d = end - timedelta(days=7)
    start_90d = end - timedelta(days=90)

    # Factor 1: ACWR spike (20 pts)
    load_data = get_training_load_fn(user_id, days=90)
    acwr = load_data["current_acwr"]
    if acwr >= 1.5:
        acwr_risk = 20
    elif acwr >= 1.3:
        acwr_risk = 12
    elif acwr >= 1.1:
        acwr_risk = 4
    else:
        acwr_risk = 0

    # Factor 2: Readiness decline (14-day slope, 20 pts)
    readiness = readiness_repo.get_by_date_range(user_id, start_14d, end)
    readiness_scores = [r["composite_score"] for r in readiness]
    readiness_slope = _linear_slope(readiness_scores)
    if readiness_slope < -0.5:
        readiness_risk = 20
    elif readiness_slope < -0.2:
        readiness_risk = 12
    elif readiness_slope < 0:
        readiness_risk = 4
    else:
        readiness_risk = 0

    # Factor 3: Hotspot mentions (7d, 15 pts)
    readiness_7d = readiness_repo.get_by_date_range(user_id, start_7d, end)
    hotspot_count = sum(1 for r in readiness_7d if r.get("hotspot_note"))
    if hotspot_count >= 4:
        hotspot_risk = 15
    elif hotspot_count >= 2:
        hotspot_risk = 10
    elif hotspot_count >= 1:
        hotspot_risk = 3
    else:
        hotspot_risk = 0

    # Factor 4: Intensity creep (15 pts)
    sessions_90d = session_repo.get_by_date_range(user_id, start_90d, end)
    if len(sessions_90d) >= 5:
        half = len(sessions_90d) // 2
        first_half = [s.get("intensity", 0) or 0 for s in sessions_90d[:half]]
        second_half = [s.get("intensity", 0) or 0 for s in sessions_90d[half:]]
        avg_first = statistics.mean(first_half) if first_half else 0
        avg_second = statistics.mean(second_half) if second_half else 0
        intensity_diff = avg_second - avg_first
        if intensity_diff >= 1.0:
            intensity_risk = 15
        elif intensity_diff >= 0.5:
            intensity_risk = 10
        elif intensity_diff >= 0.2:
            intensity_risk = 3
        else:
            intensity_risk = 0
    else:
        intensity_risk = 0

    # Factor 5: HRV decline (15 pts) — WHOOP biometrics
    hrv_risk = 0
    # Factor 6: Recovery decline (15 pts) — WHOOP biometrics
    recovery_decline_risk = 0

    try:
        from rivaflow.db.repositories.whoop_connection_repo import (
            WhoopConnectionRepository,
        )
        from rivaflow.db.repositories.whoop_recovery_cache_repo import (
            WhoopRecoveryCacheRepository,
        )

        conn = WhoopConnectionRepository.get_by_user_id(user_id)
        if conn and conn.get("is_active"):
            end_dt = end.isoformat() + "T23:59:59"
            start_dt = start_14d.isoformat()
            recs = WhoopRecoveryCacheRepository.get_by_date_range(
                user_id, start_dt, end_dt
            )

            # HRV decline: slope over 14-day HRV values
            hrv_values = [r["hrv_ms"] for r in recs if r.get("hrv_ms") is not None]
            if len(hrv_values) >= 3:
                hrv_slope = _linear_slope(hrv_values)
                if hrv_slope < -1.0:
                    hrv_risk = 15
                elif hrv_slope < -0.5:
                    hrv_risk = 10
                elif hrv_slope < 0:
                    hrv_risk = 3

            # Recovery decline: consecutive days with recovery < 34%
            consecutive_red = 0
            max_consecutive = 0
            for r in recs:
                rs = r.get("recovery_score")
                if rs is not None and rs < 34:
                    consecutive_red += 1
                    max_consecutive = max(max_consecutive, consecutive_red)
                else:
                    consecutive_red = 0

            if max_consecutive >= 3:
                recovery_decline_risk = 15
            elif max_consecutive >= 2:
                recovery_decline_risk = 10
            elif max_consecutive >= 1:
                recovery_decline_risk = 5
    except Exception:
        pass

    total_risk = (
        acwr_risk
        + readiness_risk
        + hotspot_risk
        + intensity_risk
        + hrv_risk
        + recovery_decline_risk
    )

    if total_risk >= 60:
        level = "red"
    elif total_risk >= 30:
        level = "yellow"
    else:
        level = "green"

    recommendations = []
    if acwr_risk >= 12:
        recommendations.append("Reduce training volume — ACWR is elevated.")
    if readiness_risk >= 12:
        recommendations.append(
            "Readiness trending down — prioritize sleep and recovery."
        )
    if hotspot_risk >= 10:
        recommendations.append("Multiple injury hotspots noted — consider rest days.")
    if intensity_risk >= 10:
        recommendations.append("Intensity creeping up — mix in lighter sessions.")
    if hrv_risk >= 10:
        recommendations.append("HRV declining — your nervous system needs recovery.")
    if recovery_decline_risk >= 10:
        recommendations.append(
            "Multiple low-recovery days — prioritize sleep and rest."
        )
    if not recommendations:
        recommendations.append("Training load looks healthy. Keep it up!")

    return {
        "risk_score": total_risk,
        "level": level,
        "factors": {
            "acwr_spike": {"score": acwr_risk, "max": 20},
            "readiness_decline": {
                "score": readiness_risk,
                "max": 20,
            },
            "hotspot_mentions": {
                "score": hotspot_risk,
                "max": 15,
            },
            "intensity_creep": {
                "score": intensity_risk,
                "max": 15,
            },
            "hrv_decline": {"score": hrv_risk, "max": 15},
            "recovery_decline": {
                "score": recovery_decline_risk,
                "max": 15,
            },
        },
        "recommendations": recommendations,
    }


def compute_recovery_insights(
    session_repo: SessionRepository,
    readiness_repo: ReadinessRepository,
    user_id: int,
    days: int = 90,
) -> dict[str, Any]:
    """Sleep -> next-day performance, optimal rest days analysis."""
    end = date.today()
    start = end - timedelta(days=days)

    readiness = readiness_repo.get_by_date_range(user_id, start, end)
    sessions = session_repo.get_by_date_range(user_id, start, end)

    # Sleep -> next-day performance Pearson r
    sleep_values = []
    next_day_sub_rates = []

    for r in readiness:
        next_day = r["check_date"] + timedelta(days=1)
        matching_sessions = [s for s in sessions if s["session_date"] == next_day]
        if not matching_sessions:
            continue

        sleep = r.get("sleep", 0) or 0
        total_for = sum(s.get("submissions_for", 0) or 0 for s in matching_sessions)
        total_against = sum(
            s.get("submissions_against", 0) or 0 for s in matching_sessions
        )
        sr = total_for / total_against if total_against > 0 else float(total_for)

        sleep_values.append(float(sleep))
        next_day_sub_rates.append(sr)

    sleep_correlation = _pearson_r(sleep_values, next_day_sub_rates)

    # Optimal rest days analysis
    session_dates = sorted(set(s["session_date"] for s in sessions))

    rest_day_performance: dict[int, list[float]] = defaultdict(list)

    for s in sessions:
        # Find days since last session
        days_since = 0
        for prev_date in reversed(session_dates):
            if prev_date < s["session_date"]:
                days_since = (s["session_date"] - prev_date).days
                break

        total_for = s.get("submissions_for", 0) or 0
        total_against = s.get("submissions_against", 0) or 0
        sr = total_for / total_against if total_against > 0 else float(total_for)
        rest_day_performance[days_since].append(sr)

    rest_analysis = []
    for rest_days, rates in sorted(rest_day_performance.items()):
        if rest_days > 7:
            continue
        rest_analysis.append(
            {
                "rest_days": rest_days,
                "avg_sub_rate": round(statistics.mean(rates), 2) if rates else 0,
                "sessions": len(rates),
            }
        )

    # Find optimal rest
    optimal = 0
    best_rate = -1.0
    for entry in rest_analysis:
        if entry["sessions"] >= 2 and entry["avg_sub_rate"] > best_rate:
            best_rate = entry["avg_sub_rate"]
            optimal = entry["rest_days"]

    insight = ""
    if abs(sleep_correlation) >= 0.3:
        insight += (
            f"Sleep quality correlates with next-day "
            f"performance (r={sleep_correlation}). "
        )
    if optimal > 0:
        insight += (
            f"Optimal: {optimal} rest day{'s' if optimal > 1 else ''} "
            f"between sessions."
        )
    elif not insight:
        insight = "Not enough data for recovery analysis yet."

    return {
        "sleep_correlation": sleep_correlation,
        "optimal_rest_days": optimal,
        "rest_analysis": rest_analysis,
        "insight": insight,
        "data_points": len(sleep_values),
    }


def compute_insights_summary(
    get_training_load_fn,
    get_overtraining_risk_fn,
    get_technique_effectiveness_fn,
    get_session_quality_scores_fn,
    user_id: int,
) -> dict[str, Any]:
    """Lightweight dashboard digest."""
    load = get_training_load_fn(user_id, days=90)
    risk = get_overtraining_risk_fn(user_id)
    technique = get_technique_effectiveness_fn(user_id)
    quality = get_session_quality_scores_fn(user_id)

    money_moves = [t["name"] for t in technique.get("money_moves", [])[:3]]

    # Pick top insight
    top_insight = ""
    if risk["level"] == "red":
        top_insight = "Overtraining risk is HIGH. Prioritize recovery."
    elif load["current_zone"] == "danger":
        top_insight = "Training load in danger zone. Reduce volume."
    elif load["current_zone"] == "sweet_spot":
        top_insight = "Training load is in the sweet spot. Keep it up!"
    elif quality["avg_quality"] >= 70:
        top_insight = "Session quality is excellent."
    else:
        top_insight = "Keep training consistently."

    return {
        "acwr": load["current_acwr"],
        "acwr_zone": load["current_zone"],
        "risk_score": risk["risk_score"],
        "risk_level": risk["level"],
        "game_breadth": technique["game_breadth"],
        "avg_session_quality": quality["avg_quality"],
        "money_moves": money_moves,
        "top_insight": top_insight,
    }

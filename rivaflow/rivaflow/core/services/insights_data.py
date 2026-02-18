"""Data aggregation methods for insights analytics.

Correlation, training load, technique effectiveness, session quality,
partner progression, and check-in trend calculations.
"""

import statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from rivaflow.core.services.insights_math import (
    _ewma,
    _linear_slope,
    _pearson_r,
    _shannon_entropy,
)
from rivaflow.db.repositories import (
    FriendRepository,
    GlossaryRepository,
    ReadinessRepository,
    SessionRepository,
    SessionRollRepository,
)
from rivaflow.db.repositories.session_technique_repo import (
    SessionTechniqueRepository,
)


def compute_readiness_performance_correlation(
    session_repo: SessionRepository,
    readiness_repo: ReadinessRepository,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """Match readiness to same-day sessions, compute Pearson r."""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    readiness = readiness_repo.get_by_date_range(user_id, start_date, end_date)
    sessions = session_repo.get_by_date_range(user_id, start_date, end_date)

    readiness_by_date = {r["check_date"]: r for r in readiness}

    scatter = []
    scores = []
    sub_rates = []

    for s in sessions:
        r = readiness_by_date.get(s["session_date"])
        if not r:
            continue

        total_for = s.get("submissions_for", 0) or 0
        total_against = s.get("submissions_against", 0) or 0
        sr = total_for / total_against if total_against > 0 else float(total_for)

        scatter.append(
            {
                "date": s["session_date"].isoformat(),
                "readiness": r["composite_score"],
                "sub_rate": round(sr, 2),
                "intensity": s.get("intensity", 0),
            }
        )
        scores.append(float(r["composite_score"]))
        sub_rates.append(sr)

    r_value = _pearson_r(scores, sub_rates)

    # Find optimal readiness zone (bucket by 4-point ranges)
    buckets: dict[str, list[float]] = defaultdict(list)
    for sc, sr in zip(scores, sub_rates):
        bucket_low = int(sc // 4) * 4
        key = f"{bucket_low}-{bucket_low + 3}"
        buckets[key].append(sr)

    optimal_zone = ""
    best_avg = -1.0
    for zone, rates in buckets.items():
        avg = statistics.mean(rates) if rates else 0
        if avg > best_avg and len(rates) >= 2:
            best_avg = avg
            optimal_zone = zone

    insight = ""
    if abs(r_value) >= 0.4:
        insight = (
            f"Your readiness strongly correlates with performance "
            f"(r={r_value}). Best sessions when readiness {optimal_zone}."
        )
    elif abs(r_value) >= 0.2:
        insight = (
            f"Moderate correlation between readiness and performance "
            f"(r={r_value}). Optimal readiness zone: {optimal_zone}."
        )
    elif scatter:
        insight = (
            "Weak correlation between readiness and performance. "
            "Your performance is consistent regardless of readiness."
        )
    else:
        insight = "Not enough data to correlate readiness with performance."

    return {
        "r_value": r_value,
        "scatter": scatter,
        "optimal_zone": optimal_zone,
        "insight": insight,
        "data_points": len(scatter),
    }


def compute_training_load_management(
    session_repo: SessionRepository,
    user_id: int,
    days: int = 90,
) -> dict[str, Any]:
    """EWMA acute (7d) vs chronic (28d) training load."""
    end = date.today()
    start = end - timedelta(days=days + 28)

    sessions = session_repo.get_by_date_range(user_id, start, end)

    # Daily load = sum(intensity * duration) per day
    daily_load: dict[str, float] = defaultdict(float)
    for s in sessions:
        day_key = s["session_date"].isoformat()
        intensity = s.get("intensity", 0) or 0
        duration = s.get("duration_mins", 0) or 0
        daily_load[day_key] += intensity * duration

    # Build ordered daily series
    current = start
    daily_values = []
    dates = []
    while current <= end:
        day_key = current.isoformat()
        daily_values.append(daily_load.get(day_key, 0.0))
        dates.append(day_key)
        current += timedelta(days=1)

    acute = _ewma(daily_values, 7)
    chronic = _ewma(daily_values, 28)

    # Build ACWR series (only for the requested days, not warmup)
    warmup = 28
    acwr_series = []
    for i in range(warmup, len(daily_values)):
        c = chronic[i]
        a = acute[i]
        acwr = round(a / c, 2) if c > 0 else 0.0
        zone = "undertrained"
        if acwr >= 1.5:
            zone = "danger"
        elif acwr >= 1.3:
            zone = "caution"
        elif acwr >= 0.8:
            zone = "sweet_spot"

        acwr_series.append(
            {
                "date": dates[i],
                "acute": a,
                "chronic": c,
                "acwr": acwr,
                "zone": zone,
                "daily_load": daily_values[i],
            }
        )

    current_acwr = acwr_series[-1]["acwr"] if acwr_series else 0.0
    current_zone = acwr_series[-1]["zone"] if acwr_series else "undertrained"

    zone_labels = {
        "undertrained": "Undertrained (<0.8)",
        "sweet_spot": "Sweet Spot (0.8-1.3)",
        "caution": "Caution (1.3-1.5)",
        "danger": "Danger (>1.5)",
    }

    insight = (
        f"Your ACWR is {current_acwr} — "
        f"{zone_labels.get(current_zone, current_zone)}."
    )
    if current_zone == "danger":
        insight += " Consider reducing training load to prevent overtraining."
    elif current_zone == "caution":
        insight += " Monitor closely and prioritize recovery."
    elif current_zone == "sweet_spot":
        insight += " Excellent training load balance."
    else:
        insight += " Consider increasing training frequency or intensity."

    return {
        "acwr_series": acwr_series,
        "current_acwr": current_acwr,
        "current_zone": current_zone,
        "insight": insight,
    }


def compute_technique_effectiveness(
    session_repo: SessionRepository,
    roll_repo: SessionRollRepository,
    glossary_repo: GlossaryRepository,
    technique_repo: SessionTechniqueRepository,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """Cross-ref submissions with technique training frequency."""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    sessions = session_repo.get_by_date_range(user_id, start_date, end_date)
    session_ids = [s["id"] for s in sessions]

    # Get rolls for submission data
    rolls_by_session = roll_repo.get_by_session_ids(user_id, session_ids)

    # Count submissions by movement
    sub_counts: Counter = Counter()
    for rolls in rolls_by_session.values():
        for roll in rolls:
            for mid in roll.get("submissions_for") or []:
                sub_counts[mid] += 1

    # Count technique training frequency
    techs_by_session = technique_repo.batch_get_by_session_ids(session_ids)
    train_counts: Counter = Counter()
    for techs in techs_by_session.values():
        for tech in techs:
            mid = tech.get("movement_id")
            if mid:
                train_counts[mid] += 1

    # Build glossary lookup
    movements = glossary_repo.list_all()
    movement_map = {m["id"]: m for m in movements}

    # All unique movement IDs
    all_ids = set(sub_counts.keys()) | set(train_counts.keys())

    if not all_ids:
        return {
            "techniques": [],
            "game_breadth": 0,
            "money_moves": [],
            "insight": "Not enough technique data yet.",
        }

    # Calculate medians for quadrant thresholds
    sub_values = [sub_counts.get(mid, 0) for mid in all_ids]
    train_values = [train_counts.get(mid, 0) for mid in all_ids]
    median_sub = statistics.median(sub_values) if sub_values else 0
    median_train = statistics.median(train_values) if train_values else 0

    techniques = []
    for mid in all_ids:
        subs = sub_counts.get(mid, 0)
        trains = train_counts.get(mid, 0)
        movement = movement_map.get(mid)
        if not movement:
            continue

        # Quadrant classification
        if subs > median_sub and trains > median_train:
            quadrant = "money_move"
        elif subs > median_sub and trains <= median_train:
            quadrant = "natural"
        elif subs <= median_sub and trains > median_train:
            quadrant = "developing"
        else:
            quadrant = "untested"

        techniques.append(
            {
                "id": mid,
                "name": movement["name"],
                "category": movement.get("category", "other"),
                "submissions": subs,
                "training_count": trains,
                "quadrant": quadrant,
            }
        )

    # Shannon entropy for game breadth
    sub_count_values = [t["submissions"] for t in techniques if t["submissions"] > 0]
    game_breadth = _shannon_entropy(sub_count_values)

    money_moves = [t for t in techniques if t["quadrant"] == "money_move"]
    money_moves.sort(key=lambda t: t["submissions"], reverse=True)

    insight = f"Game breadth: {game_breadth}/100. "
    if money_moves:
        names = ", ".join(t["name"] for t in money_moves[:3])
        insight += f"Money moves: {names}."
    else:
        insight += "No clear money moves yet — keep training!"

    return {
        "techniques": techniques,
        "game_breadth": game_breadth,
        "money_moves": money_moves[:5],
        "insight": insight,
    }


def compute_partner_progression(
    session_repo: SessionRepository,
    roll_repo: SessionRollRepository,
    friend_repo: FriendRepository,
    user_id: int,
    partner_id: int,
) -> dict[str, Any]:
    """Rolling 5-roll window sub rate against a specific partner."""
    partner = friend_repo.get_by_id(user_id, partner_id)
    if not partner:
        return {
            "progression": [],
            "trend": "unknown",
            "partner": None,
            "insight": "Partner not found.",
        }

    # Get all rolls with this partner
    rolls = roll_repo.get_by_partner_id(user_id, partner_id)
    # Also get by name
    name_rolls = roll_repo.list_by_partner_name(user_id, partner["name"])

    # Deduplicate by roll ID
    seen_ids: set[int] = set()
    all_rolls = []
    for r in rolls + name_rolls:
        if r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            all_rolls.append(r)

    if len(all_rolls) < 3:
        return {
            "progression": [],
            "trend": "insufficient_data",
            "partner": {
                "name": partner["name"],
                "belt_rank": partner.get("belt_rank"),
            },
            "insight": (
                f"Only {len(all_rolls)} rolls logged with "
                f"{partner['name']}. Need 3+ for progression."
            ),
        }

    # Sort by session date
    session_cache: dict[int, date] = {}
    for r in all_rolls:
        sid = r["session_id"]
        if sid not in session_cache:
            s = session_repo.get_by_id(user_id, sid)
            session_cache[sid] = s["session_date"] if s else date.today()

    all_rolls.sort(key=lambda r: session_cache[r["session_id"]])

    # Calculate per-roll sub result (1 = sub for, -1 = sub against, 0 = neutral)
    results = []
    for r in all_rolls:
        subs_for = len(r.get("submissions_for") or [])
        subs_against = len(r.get("submissions_against") or [])
        score = subs_for - subs_against
        results.append(
            {
                "date": session_cache[r["session_id"]].isoformat(),
                "subs_for": subs_for,
                "subs_against": subs_against,
                "score": score,
            }
        )

    # Rolling 5-roll window sub rate
    window = 5
    progression = []
    for i in range(len(results)):
        start_idx = max(0, i - window + 1)
        window_results = results[start_idx : i + 1]
        total_for = sum(r["subs_for"] for r in window_results)
        total_against = sum(r["subs_against"] for r in window_results)
        rate = (
            round(total_for / total_against, 2)
            if total_against > 0
            else float(total_for)
        )
        progression.append(
            {
                "roll_number": i + 1,
                "date": results[i]["date"],
                "rolling_sub_rate": rate,
                "window_size": len(window_results),
            }
        )

    # Trend detection via slope
    if len(progression) >= 3:
        rates = [p["rolling_sub_rate"] for p in progression]
        slope = _linear_slope(rates)
        if slope > 0.05:
            trend = "improving"
        elif slope < -0.05:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    trend_labels = {
        "improving": "improving against",
        "declining": "declining against",
        "stable": "stable against",
    }
    trend_text = trend_labels.get(trend, "")
    insight = (
        f"Performance {trend_text} {partner['name']}."
        if trend_text
        else f"Not enough data against {partner['name']} yet."
    )

    return {
        "progression": progression,
        "trend": trend,
        "partner": {
            "name": partner["name"],
            "belt_rank": partner.get("belt_rank"),
        },
        "insight": insight,
    }


def compute_session_quality_scores(
    session_repo: SessionRepository,
    technique_repo: SessionTechniqueRepository,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """Composite per-session quality score (0-100)."""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    sessions = session_repo.get_by_date_range(user_id, start_date, end_date)

    if not sessions:
        return {
            "sessions": [],
            "avg_quality": 0,
            "top_sessions": [],
            "weekly_trend": [],
            "insight": "No sessions to score.",
        }

    # Determine max values for normalization
    max_intensity = 5.0
    max_rolls = max((s.get("rolls", 0) or 0 for s in sessions), default=1) or 1
    max_subs = max((s.get("submissions_for", 0) or 0 for s in sessions), default=1) or 1

    # Get technique counts
    session_ids = [s["id"] for s in sessions]
    techs = technique_repo.batch_get_by_session_ids(session_ids)
    max_techs = max((len(t) for t in techs.values()), default=1) or 1

    scored = []
    for s in sessions:
        intensity = s.get("intensity", 0) or 0
        rolls = s.get("rolls", 0) or 0
        subs_for = s.get("submissions_for", 0) or 0
        tech_count = len(techs.get(s["id"], []))

        # 4 components, 25 points each
        intensity_score = (intensity / max_intensity) * 25
        sub_score = (subs_for / max_subs) * 25
        tech_score = (tech_count / max_techs) * 25
        volume_score = (rolls / max_rolls) * 25

        quality = round(intensity_score + sub_score + tech_score + volume_score, 1)

        scored.append(
            {
                "session_id": s["id"],
                "date": s["session_date"].isoformat(),
                "quality": quality,
                "breakdown": {
                    "intensity": round(intensity_score, 1),
                    "submissions": round(sub_score, 1),
                    "techniques": round(tech_score, 1),
                    "volume": round(volume_score, 1),
                },
                "class_type": s["class_type"],
                "gym": s["gym_name"],
            }
        )

    scored.sort(key=lambda x: x["quality"], reverse=True)
    avg_quality = round(statistics.mean([s["quality"] for s in scored]), 1)

    # Weekly trend
    weekly: dict[str, list[float]] = defaultdict(list)
    for s in scored:
        d = date.fromisoformat(s["date"])
        week_key = d.strftime("%Y-W%U")
        weekly[week_key].append(s["quality"])

    weekly_trend = [
        {
            "week": k,
            "avg_quality": round(statistics.mean(v), 1),
            "sessions": len(v),
        }
        for k, v in sorted(weekly.items())
    ]

    insight = f"Average session quality: {avg_quality}/100. "
    if scored:
        insight += (
            f"Best session: {scored[0]['date']} " f"({scored[0]['quality']}/100)."
        )

    return {
        "sessions": scored,
        "avg_quality": avg_quality,
        "top_sessions": scored[:3],
        "weekly_trend": weekly_trend,
        "insight": insight,
    }


def compute_checkin_trends(
    user_id: int,
    days: int = 30,
) -> dict[str, Any]:
    """Analyse daily check-in data for energy, quality, and rest trends."""
    from rivaflow.db.repositories.checkin_repo import CheckinRepository

    repo = CheckinRepository()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    checkins = repo.get_checkins_range(user_id, start_date, end_date)

    if not checkins:
        return {
            "energy_trend": [],
            "quality_trend": [],
            "rest_days": 0,
            "training_days": 0,
            "avg_energy": None,
            "avg_quality": None,
            "energy_slope": None,
            "quality_slope": None,
            "rest_pattern": [],
        }

    # Extract energy and quality time series
    energy_points: list[dict[str, Any]] = []
    quality_points: list[dict[str, Any]] = []
    rest_dates: set[str] = set()
    training_dates: set[str] = set()

    for c in checkins:
        d = c.get("check_date", "")
        if c.get("energy_level"):
            energy_points.append({"date": d, "value": c["energy_level"]})
        if c.get("training_quality"):
            quality_points.append({"date": d, "value": c["training_quality"]})
        if c.get("checkin_type") == "rest":
            rest_dates.add(d)
        elif c.get("checkin_type") in ("session", "evening") and c.get(
            "training_quality"
        ):
            training_dates.add(d)

    energy_vals = [p["value"] for p in energy_points]
    quality_vals = [p["value"] for p in quality_points]

    return {
        "energy_trend": energy_points,
        "quality_trend": quality_points,
        "rest_days": len(rest_dates),
        "training_days": len(training_dates),
        "avg_energy": (round(statistics.mean(energy_vals), 1) if energy_vals else None),
        "avg_quality": (
            round(statistics.mean(quality_vals), 1) if quality_vals else None
        ),
        "energy_slope": (
            round(_linear_slope(energy_vals), 3) if len(energy_vals) >= 3 else None
        ),
        "quality_slope": (
            round(_linear_slope(quality_vals), 3) if len(quality_vals) >= 3 else None
        ),
        "rest_pattern": sorted(rest_dates),
    }

"""Readiness and recovery analytics service."""

import statistics
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from rivaflow.db.repositories import (
    ReadinessRepository,
    SessionRepository,
)
from rivaflow.db.repositories.whoop_recovery_cache_repo import (
    WhoopRecoveryCacheRepository,
)


class ReadinessAnalyticsService:
    """Business logic for readiness and recovery analytics."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()
        self.recovery_cache_repo = WhoopRecoveryCacheRepository()

    def get_readiness_trends(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get readiness and recovery analytics.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - readiness_over_time: Daily readiness scores
            - training_load_vs_readiness: Scatter plot data
            - recovery_patterns: Day of week averages
            - injury_timeline: Hotspot tracking
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        readiness_records = self.readiness_repo.get_by_date_range(
            user_id, start_date, end_date
        )
        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )

        # Readiness over time
        readiness_over_time = []
        for record in readiness_records:
            readiness_over_time.append(
                {
                    "date": record["check_date"].isoformat(),
                    "composite_score": record["composite_score"],
                    "sleep": record["sleep"],
                    "stress": record["stress"],
                    "soreness": record["soreness"],
                    "energy": record["energy"],
                }
            )

        # Training load vs readiness (combine sessions with readiness on same day)
        load_vs_readiness = []
        for session in sessions:
            # Find readiness for same day
            matching_readiness = next(
                (
                    r
                    for r in readiness_records
                    if r["check_date"] == session["session_date"]
                ),
                None,
            )
            if matching_readiness:
                load_vs_readiness.append(
                    {
                        "date": session["session_date"].isoformat(),
                        "readiness": matching_readiness["composite_score"],
                        "intensity": session["intensity"],
                        "duration": session["duration_mins"],
                        "class_type": session["class_type"],
                    }
                )

        # Recovery patterns by day of week
        day_of_week_readiness = defaultdict(list)
        for record in readiness_records:
            day_name = record["check_date"].strftime("%A")
            day_of_week_readiness[day_name].append(record["composite_score"])

        recovery_patterns = []
        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            scores = day_of_week_readiness[day]
            recovery_patterns.append(
                {
                    "day": day,
                    "avg_readiness": round(statistics.mean(scores), 1) if scores else 0,
                    "count": len(scores),
                }
            )

        # Injury timeline (hotspots)
        injury_timeline = [
            {
                "date": r["check_date"].isoformat(),
                "hotspot": r.get("hotspot_note", ""),
            }
            for r in readiness_records
            if r.get("hotspot_note")
        ]

        # Weight tracking
        weight_records = [
            r for r in readiness_records if r.get("weight_kg") is not None
        ]
        weight_over_time = []
        for record in weight_records:
            weight_over_time.append(
                {
                    "date": record["check_date"].isoformat(),
                    "weight_kg": round(record["weight_kg"], 1),
                }
            )

        # Calculate weight stats
        weight_stats = {}
        if weight_records:
            weights = [r["weight_kg"] for r in weight_records]
            weight_stats = {
                "has_data": True,
                "start_weight": round(weights[0], 1),
                "end_weight": round(weights[-1], 1),
                "weight_change": round(weights[-1] - weights[0], 2),
                "min_weight": round(min(weights), 1),
                "max_weight": round(max(weights), 1),
                "avg_weight": round(statistics.mean(weights), 1),
            }
        else:
            weight_stats = {
                "has_data": False,
                "start_weight": None,
                "end_weight": None,
                "weight_change": None,
                "min_weight": None,
                "max_weight": None,
                "avg_weight": None,
            }

        # Summary stats for frontend
        composite_scores = [
            r["composite_score"]
            for r in readiness_records
            if r.get("composite_score") is not None
        ]
        summary = {}
        if composite_scores:
            best_idx = max(
                range(len(readiness_records)),
                key=lambda i: readiness_records[i].get("composite_score") or 0,
            )
            worst_idx = min(
                range(len(readiness_records)),
                key=lambda i: readiness_records[i].get("composite_score")
                or float("inf"),
            )
            summary = {
                "avg_composite_score": round(statistics.mean(composite_scores), 1),
                "best_day": readiness_records[best_idx]["check_date"].isoformat(),
                "worst_day": readiness_records[worst_idx]["check_date"].isoformat(),
                "days_logged": len(readiness_records),
            }

        # Component averages for frontend breakdown
        component_averages = {}
        for key in ("sleep", "stress", "soreness", "energy"):
            vals = [r[key] for r in readiness_records if r.get(key) is not None]
            if vals:
                component_averages[key] = round(statistics.mean(vals), 1)

        return {
            "readiness_over_time": readiness_over_time,
            "trends": readiness_over_time,
            "training_load_vs_readiness": load_vs_readiness,
            "recovery_patterns": recovery_patterns,
            "injury_timeline": injury_timeline,
            "weight_over_time": weight_over_time,
            "weight_stats": weight_stats,
            "summary": summary,
            "component_averages": component_averages,
        }

    def get_weight_trend(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Raw weight points + 7-day simple moving average + stats."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        readiness_records = self.readiness_repo.get_by_date_range(
            user_id, start_date, end_date
        )

        weight_records = [
            r for r in readiness_records if r.get("weight_kg") is not None
        ]

        if not weight_records:
            return {
                "raw_points": [],
                "sma_7day": [],
                "stats": {"has_data": False},
            }

        raw_points = [
            {
                "date": r["check_date"].isoformat(),
                "weight_kg": round(r["weight_kg"], 1),
            }
            for r in weight_records
        ]

        # 7-day simple moving average
        weights = [r["weight_kg"] for r in weight_records]
        sma_7day = []
        for i in range(len(weights)):
            window_start = max(0, i - 6)
            window = weights[window_start : i + 1]
            sma_7day.append(
                {
                    "date": weight_records[i]["check_date"].isoformat(),
                    "sma": round(statistics.mean(window), 1),
                }
            )

        weight_stats = {
            "has_data": True,
            "start_weight": round(weights[0], 1),
            "end_weight": round(weights[-1], 1),
            "weight_change": round(weights[-1] - weights[0], 2),
            "min_weight": round(min(weights), 1),
            "max_weight": round(max(weights), 1),
            "avg_weight": round(statistics.mean(weights), 1),
            "data_points": len(weights),
        }

        return {
            "raw_points": raw_points,
            "sma_7day": sma_7day,
            "stats": weight_stats,
        }

    def get_whoop_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get Whoop fitness tracker analytics.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - strain_vs_performance: Whoop strain with submission ratio
            - heart_rate_zones: HR analysis by class type
            - calorie_burn: Calorie analysis
            - recovery_correlation: Strain vs next-day readiness
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )
        whoop_sessions = [s for s in sessions if s.get("whoop_strain") is not None]

        # Strain vs performance
        strain_vs_performance = []
        for session in whoop_sessions:
            sub_ratio = 0
            if session["submissions_against"] > 0:
                sub_ratio = round(
                    session["submissions_for"] / session["submissions_against"], 2
                )

            strain_vs_performance.append(
                {
                    "date": session["session_date"].isoformat(),
                    "strain": session.get("whoop_strain"),
                    "submissions_for": session["submissions_for"],
                    "submissions_against": session["submissions_against"],
                    "sub_ratio": sub_ratio,
                }
            )

        # Heart rate zones by class type
        hr_by_class = defaultdict(lambda: {"avg_hr": [], "max_hr": []})
        for session in whoop_sessions:
            if session.get("whoop_avg_hr"):
                hr_by_class[session["class_type"]]["avg_hr"].append(
                    session["whoop_avg_hr"]
                )
            if session.get("whoop_max_hr"):
                hr_by_class[session["class_type"]]["max_hr"].append(
                    session["whoop_max_hr"]
                )

        heart_rate_zones = []
        for class_type, hrs in hr_by_class.items():
            heart_rate_zones.append(
                {
                    "class_type": class_type,
                    "avg_hr": (
                        round(statistics.mean(hrs["avg_hr"])) if hrs["avg_hr"] else 0
                    ),
                    "max_hr": (
                        round(statistics.mean(hrs["max_hr"])) if hrs["max_hr"] else 0
                    ),
                    "sessions": len(hrs["avg_hr"]),
                }
            )

        # Calorie burn analysis
        calorie_analysis = defaultdict(lambda: {"calories": [], "duration": []})
        for session in whoop_sessions:
            if session.get("whoop_calories"):
                calorie_analysis[session["class_type"]]["calories"].append(
                    session["whoop_calories"]
                )
                calorie_analysis[session["class_type"]]["duration"].append(
                    session["duration_mins"]
                )

        calorie_burn = []
        for class_type, data in calorie_analysis.items():
            total_cals = sum(data["calories"])
            total_mins = sum(data["duration"])
            calorie_burn.append(
                {
                    "class_type": class_type,
                    "total_calories": total_cals,
                    "avg_calories": (
                        round(statistics.mean(data["calories"]))
                        if data["calories"]
                        else 0
                    ),
                    "calories_per_min": (
                        round(total_cals / total_mins, 1) if total_mins > 0 else 0
                    ),
                    "sessions": len(data["calories"]),
                }
            )

        # Recovery correlation (Whoop strain vs next day readiness)
        readiness_records = self.readiness_repo.get_by_date_range(
            user_id, start_date, end_date
        )
        recovery_correlation = []

        for session in whoop_sessions:
            if session.get("whoop_strain"):
                next_day = session["session_date"] + timedelta(days=1)
                next_readiness = next(
                    (r for r in readiness_records if r["check_date"] == next_day), None
                )
                if next_readiness:
                    recovery_correlation.append(
                        {
                            "date": session["session_date"].isoformat(),
                            "strain": session["whoop_strain"],
                            "next_day_readiness": next_readiness["composite_score"],
                        }
                    )

        # ---- Phase 2 recovery trends from whoop_recovery_cache ----
        recovery_records = self.recovery_cache_repo.get_by_date_range(
            user_id, start_date.isoformat(), end_date.isoformat() + "T23:59:59"
        )

        # HRV trend (daily values + 7-day moving average)
        hrv_trend = []
        hrv_values_window: list[float] = []
        for rec in reversed(recovery_records):  # oldest first
            hrv = rec.get("hrv_ms")
            if hrv is not None:
                hrv_values_window.append(hrv)
                window = hrv_values_window[-7:]
                hrv_trend.append(
                    {
                        "date": rec["cycle_start"][:10],
                        "hrv_ms": round(hrv, 1),
                        "7day_avg": round(statistics.mean(window), 1),
                    }
                )

        # RHR trend
        rhr_trend = []
        rhr_values_window: list[float] = []
        for rec in reversed(recovery_records):
            rhr = rec.get("resting_hr")
            if rhr is not None:
                rhr_values_window.append(rhr)
                window = rhr_values_window[-7:]
                rhr_trend.append(
                    {
                        "date": rec["cycle_start"][:10],
                        "resting_hr": round(rhr, 1),
                        "7day_avg": round(statistics.mean(window), 1),
                    }
                )

        # Recovery over time
        recovery_over_time = []
        for rec in reversed(recovery_records):
            recovery_over_time.append(
                {
                    "date": rec["cycle_start"][:10],
                    "recovery_score": rec.get("recovery_score"),
                    "sleep_performance": rec.get("sleep_performance"),
                }
            )

        # Strain vs recovery (join workout cache + recovery cache by date)
        from rivaflow.db.repositories.whoop_workout_cache_repo import (
            WhoopWorkoutCacheRepository,
        )

        workout_cache = WhoopWorkoutCacheRepository()
        cached_workouts = workout_cache.get_by_user_and_time_range(
            user_id, start_date.isoformat(), end_date.isoformat() + "T23:59:59"
        )
        rec_by_date = {}
        for rec in recovery_records:
            d = rec["cycle_start"][:10]
            rec_by_date[d] = rec

        strain_vs_recovery = []
        for w in cached_workouts:
            w_date = str(w.get("start_time", ""))[:10]
            matched_rec = rec_by_date.get(w_date)
            if matched_rec and w.get("strain") is not None:
                strain_vs_recovery.append(
                    {
                        "date": w_date,
                        "strain": w["strain"],
                        "recovery_score": matched_rec.get("recovery_score"),
                    }
                )

        # Heart rate zone distribution from workout cache
        import json as _json

        zone_keys = [
            "zone_one_milli",
            "zone_two_milli",
            "zone_three_milli",
            "zone_four_milli",
            "zone_five_milli",
        ]
        zone_distribution: list[dict] = []
        zone_totals = [0.0] * 5
        zone_workout_count = 0

        for w in cached_workouts:
            # Try zone_durations column first, fall back to raw_data
            zd = w.get("zone_durations")
            if isinstance(zd, str):
                try:
                    zd = _json.loads(zd)
                except (ValueError, TypeError):
                    zd = None

            if not zd:
                raw = w.get("raw_data")
                if isinstance(raw, str):
                    try:
                        raw = _json.loads(raw)
                    except (ValueError, TypeError):
                        raw = None
                if isinstance(raw, dict):
                    zd = (
                        raw.get("score", {}).get("zone_duration")
                        if raw.get("score")
                        else None
                    )

            if not isinstance(zd, dict):
                continue

            millis = [float(zd.get(k, 0) or 0) for k in zone_keys]
            total_ms = sum(millis)
            if total_ms <= 0:
                continue

            w_date = str(w.get("start_time", ""))[:10]
            entry = {
                "date": w_date,
                "total_mins": round(total_ms / 60000, 1),
            }
            for i, zk in enumerate(zone_keys):
                entry[f"zone_{i + 1}_pct"] = round(millis[i] / total_ms * 100, 1)
                entry[f"zone_{i + 1}_mins"] = round(millis[i] / 60000, 1)
                zone_totals[i] += millis[i]
            zone_distribution.append(entry)
            zone_workout_count += 1

        # Aggregate zone averages
        zone_averages: dict = {}
        if zone_workout_count > 0:
            total_all = sum(zone_totals)
            if total_all > 0:
                zone_averages = {
                    f"zone_{i + 1}_avg_pct": round(zone_totals[i] / total_all * 100, 1)
                    for i in range(5)
                }
                zone_averages["workouts"] = zone_workout_count

        # Sleep composition breakdown
        sleep_breakdown = []
        for rec in reversed(recovery_records):
            total_ms = (
                (rec.get("light_sleep_ms") or 0)
                + (rec.get("slow_wave_ms") or 0)
                + (rec.get("rem_sleep_ms") or 0)
                + (rec.get("awake_ms") or 0)
            )
            if total_ms > 0:
                sleep_breakdown.append(
                    {
                        "date": rec["cycle_start"][:10],
                        "light_pct": round(
                            (rec.get("light_sleep_ms") or 0) / total_ms * 100, 1
                        ),
                        "sws_pct": round(
                            (rec.get("slow_wave_ms") or 0) / total_ms * 100, 1
                        ),
                        "rem_pct": round(
                            (rec.get("rem_sleep_ms") or 0) / total_ms * 100, 1
                        ),
                        "awake_pct": round(
                            (rec.get("awake_ms") or 0) / total_ms * 100, 1
                        ),
                    }
                )

        # Summary averages
        hrv_all = [r.get("hrv_ms") for r in recovery_records if r.get("hrv_ms")]
        rhr_all = [r.get("resting_hr") for r in recovery_records if r.get("resting_hr")]
        rec_all = [
            r.get("recovery_score")
            for r in recovery_records
            if r.get("recovery_score") is not None
        ]

        return {
            "strain_vs_performance": strain_vs_performance,
            "heart_rate_zones": heart_rate_zones,
            "calorie_burn": calorie_burn,
            "recovery_correlation": recovery_correlation,
            "hrv_trend": hrv_trend,
            "rhr_trend": rhr_trend,
            "recovery_over_time": recovery_over_time,
            "strain_vs_recovery": strain_vs_recovery,
            "sleep_breakdown": sleep_breakdown,
            "zone_distribution": zone_distribution,
            "zone_averages": zone_averages,
            "summary": {
                "total_whoop_sessions": len(whoop_sessions),
                "avg_strain": (
                    round(
                        statistics.mean(
                            [
                                s["whoop_strain"]
                                for s in whoop_sessions
                                if s.get("whoop_strain")
                            ]
                        ),
                        1,
                    )
                    if whoop_sessions
                    else 0
                ),
                "total_calories": sum(
                    s.get("whoop_calories", 0) for s in whoop_sessions
                ),
                "avg_hrv": (round(statistics.mean(hrv_all), 1) if hrv_all else None),
                "avg_rhr": (round(statistics.mean(rhr_all), 1) if rhr_all else None),
                "avg_recovery": (
                    round(statistics.mean(rec_all), 1) if rec_all else None
                ),
            },
        }

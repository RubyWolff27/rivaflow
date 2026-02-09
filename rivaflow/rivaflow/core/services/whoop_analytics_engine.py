"""Sport science analytics engine — WHOOP biometrics × BJJ performance."""

import statistics
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from rivaflow.core.services.insights_analytics import (
    _linear_slope,
    _pearson_r,
)
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.whoop_recovery_cache_repo import (
    WhoopRecoveryCacheRepository,
)
from rivaflow.db.repositories.whoop_workout_cache_repo import (
    WhoopWorkoutCacheRepository,
)


class WhoopAnalyticsEngine:
    """Correlate WHOOP physiological data with BJJ performance."""

    def __init__(self):
        self.session_repo = SessionRepository()

    # ------------------------------------------------------------------
    # 1. Recovery × Performance correlation
    # ------------------------------------------------------------------

    def get_recovery_performance_correlation(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """Correlate WHOOP recovery score with next-day session sub rate."""
        end = date.today()
        start = end - timedelta(days=days)

        start_dt = start.isoformat()
        end_dt = end.isoformat() + "T23:59:59"

        recs = WhoopRecoveryCacheRepository.get_by_date_range(user_id, start_dt, end_dt)
        sessions = self.session_repo.get_by_date_range(user_id, start, end)

        if not recs or not sessions:
            return {
                "r_value": 0.0,
                "scatter": [],
                "zones": {},
                "optimal_zone": "",
                "insight": "Not enough data for recovery-performance correlation.",
            }

        # Index sessions by date
        sessions_by_date: dict[str, list[dict]] = defaultdict(list)
        for s in sessions:
            sessions_by_date[s["session_date"].isoformat()].append(s)

        # Match recovery → next-day session
        recovery_scores: list[float] = []
        sub_rates: list[float] = []
        scatter: list[dict] = []

        for rec in recs:
            rs = rec.get("recovery_score")
            if rs is None:
                continue

            # Try same-day and next-day
            cycle_start = rec.get("cycle_start", "")
            if not cycle_start:
                continue
            cs_date = cycle_start[:10]
            # Next day
            try:
                d = date.fromisoformat(cs_date)
            except ValueError:
                continue
            next_day = (d + timedelta(days=1)).isoformat()

            matched = sessions_by_date.get(next_day, [])
            if not matched:
                matched = sessions_by_date.get(cs_date, [])
            if not matched:
                continue

            total_for = sum(s.get("submissions_for", 0) or 0 for s in matched)
            total_against = sum(s.get("submissions_against", 0) or 0 for s in matched)
            sr = total_for / total_against if total_against > 0 else float(total_for)

            recovery_scores.append(float(rs))
            sub_rates.append(sr)
            scatter.append(
                {
                    "date": cs_date,
                    "recovery_score": rs,
                    "sub_rate": round(sr, 2),
                }
            )

        r_value = _pearson_r(recovery_scores, sub_rates)

        # Zone bucketing (red 0-33, yellow 34-66, green 67-100)
        zone_data: dict[str, list[float]] = {
            "red": [],
            "yellow": [],
            "green": [],
        }
        for rs, sr in zip(recovery_scores, sub_rates):
            if rs < 34:
                zone_data["red"].append(sr)
            elif rs < 67:
                zone_data["yellow"].append(sr)
            else:
                zone_data["green"].append(sr)

        zones = {}
        for zone, rates in zone_data.items():
            zones[zone] = {
                "avg_sub_rate": (round(statistics.mean(rates), 2) if rates else 0),
                "sessions": len(rates),
            }

        # Optimal zone
        optimal_zone = ""
        best_avg = -1.0
        for zone, info in zones.items():
            if info["sessions"] >= 2 and info["avg_sub_rate"] > best_avg:
                best_avg = info["avg_sub_rate"]
                optimal_zone = zone

        insight = ""
        if abs(r_value) >= 0.3:
            insight = (
                f"Strong correlation between WHOOP recovery and BJJ"
                f" performance (r={r_value}). Best performance in"
                f" {optimal_zone} zone."
            )
        elif scatter:
            insight = (
                f"Moderate/weak correlation (r={r_value}). Your"
                f" performance is relatively consistent across"
                f" recovery levels."
            )
        else:
            insight = "Not enough matched data for analysis."

        return {
            "r_value": r_value,
            "scatter": scatter,
            "zones": zones,
            "optimal_zone": optimal_zone,
            "insight": insight,
        }

    # ------------------------------------------------------------------
    # 2. Strain efficiency
    # ------------------------------------------------------------------

    def get_strain_efficiency(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """Efficiency = submissions / strain for sessions with WHOOP data."""
        end = date.today()
        start = end - timedelta(days=days)

        sessions = self.session_repo.get_by_date_range(user_id, start, end)

        efficiencies: list[float] = []
        by_class_type: dict[str, list[float]] = defaultdict(list)
        by_gym: dict[str, list[float]] = defaultdict(list)
        top_sessions: list[dict] = []

        for s in sessions:
            wo = WhoopWorkoutCacheRepository.get_by_session_id(s["id"])
            if not wo:
                continue
            strain = wo.get("strain")
            if not strain or strain <= 0:
                continue

            subs = s.get("submissions_for", 0) or 0
            eff = round(subs / strain, 3)
            efficiencies.append(eff)

            ct = s.get("class_type", "other")
            by_class_type[ct].append(eff)

            gym = s.get("gym_name", "Unknown")
            by_gym[gym].append(eff)

            top_sessions.append(
                {
                    "session_id": s["id"],
                    "date": s["session_date"].isoformat(),
                    "strain": strain,
                    "submissions": subs,
                    "efficiency": eff,
                }
            )

        if not efficiencies:
            return {
                "overall_efficiency": 0,
                "by_class_type": {},
                "by_gym": {},
                "top_sessions": [],
                "insight": "No sessions with WHOOP strain data yet.",
            }

        overall = round(statistics.mean(efficiencies), 3)
        top_sessions.sort(key=lambda x: x["efficiency"], reverse=True)

        ct_summary = {
            ct: round(statistics.mean(vals), 3) for ct, vals in by_class_type.items()
        }
        gym_summary = {g: round(statistics.mean(vals), 3) for g, vals in by_gym.items()}

        best_ct = max(ct_summary, key=ct_summary.get) if ct_summary else "N/A"
        insight = (
            f"Overall strain efficiency: {overall} subs/strain."
            f" Most efficient class type: {best_ct}."
        )

        return {
            "overall_efficiency": overall,
            "by_class_type": ct_summary,
            "by_gym": gym_summary,
            "top_sessions": top_sessions[:5],
            "insight": insight,
        }

    # ------------------------------------------------------------------
    # 3. HRV performance predictor
    # ------------------------------------------------------------------

    def get_hrv_performance_predictor(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """Correlate pre-session HRV with session quality."""
        end = date.today()
        start = end - timedelta(days=days)

        start_dt = start.isoformat()
        end_dt = end.isoformat() + "T23:59:59"

        recs = WhoopRecoveryCacheRepository.get_by_date_range(user_id, start_dt, end_dt)
        sessions = self.session_repo.get_by_date_range(user_id, start, end)

        if not recs or not sessions:
            return {
                "r_value": 0.0,
                "scatter": [],
                "hrv_threshold": 0,
                "quality_above": 0,
                "quality_below": 0,
                "insight": "Not enough data for HRV prediction.",
            }

        # Index recovery by date
        rec_by_date: dict[str, dict] = {}
        for r in recs:
            cs = r.get("cycle_start", "")
            if cs:
                rec_by_date[cs[:10]] = r

        # Compute session quality
        max_intensity = 5.0
        max_rolls = max((s.get("rolls", 0) or 0 for s in sessions), default=1) or 1
        max_subs = (
            max(
                (s.get("submissions_for", 0) or 0 for s in sessions),
                default=1,
            )
            or 1
        )

        hrv_vals: list[float] = []
        quality_vals: list[float] = []
        scatter: list[dict] = []

        for s in sessions:
            s_date = s["session_date"].isoformat()
            # Check same day or day before
            rec = rec_by_date.get(s_date)
            if not rec:
                prev = (s["session_date"] - timedelta(days=1)).isoformat()
                rec = rec_by_date.get(prev)
            if not rec:
                continue

            hrv = rec.get("hrv_ms")
            if hrv is None:
                continue

            intensity = s.get("intensity", 0) or 0
            subs = s.get("submissions_for", 0) or 0
            rolls = s.get("rolls", 0) or 0
            # Quality: weighted composite
            quality = (
                (intensity / max_intensity) * 30
                + (subs / max_subs) * 30
                + (rolls / max_rolls) * 20
                + 20  # base for having a session
            )
            quality = round(min(quality, 100), 1)

            hrv_vals.append(float(hrv))
            quality_vals.append(quality)
            scatter.append(
                {
                    "date": s_date,
                    "hrv_ms": hrv,
                    "quality": quality,
                }
            )

        r_value = _pearson_r(hrv_vals, quality_vals)

        # Find HRV threshold that separates good/bad quality
        hrv_threshold = 0
        quality_above = 0.0
        quality_below = 0.0
        if hrv_vals:
            median_hrv = statistics.median(hrv_vals)
            hrv_threshold = round(median_hrv)
            above = [q for h, q in zip(hrv_vals, quality_vals) if h >= median_hrv]
            below = [q for h, q in zip(hrv_vals, quality_vals) if h < median_hrv]
            quality_above = round(statistics.mean(above), 1) if above else 0
            quality_below = round(statistics.mean(below), 1) if below else 0

        insight = ""
        if abs(r_value) >= 0.3:
            insight = (
                f"HRV predicts performance (r={r_value})."
                f" Sessions with HRV >= {hrv_threshold}ms average"
                f" {quality_above}/100 quality vs {quality_below}"
                f" below."
            )
        elif scatter:
            insight = (
                f"Weak HRV-performance link (r={r_value})."
                f" Threshold HRV: {hrv_threshold}ms."
            )
        else:
            insight = "Not enough matched data yet."

        return {
            "r_value": r_value,
            "scatter": scatter,
            "hrv_threshold": hrv_threshold,
            "quality_above": quality_above,
            "quality_below": quality_below,
            "insight": insight,
        }

    # ------------------------------------------------------------------
    # 4. Sleep × Performance analysis
    # ------------------------------------------------------------------

    def get_sleep_performance_analysis(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """Correlate sleep metrics (REM%, SWS%, hours) with quality."""
        end = date.today()
        start = end - timedelta(days=days)

        start_dt = start.isoformat()
        end_dt = end.isoformat() + "T23:59:59"

        recs = WhoopRecoveryCacheRepository.get_by_date_range(user_id, start_dt, end_dt)
        sessions = self.session_repo.get_by_date_range(user_id, start, end)

        if not recs or not sessions:
            return {
                "rem_r": 0.0,
                "sws_r": 0.0,
                "total_sleep_r": 0.0,
                "scatter": [],
                "optimal_rem_pct": 0,
                "optimal_sws_pct": 0,
                "insight": "Not enough data for sleep analysis.",
            }

        sessions_by_date: dict[str, list[dict]] = defaultdict(list)
        for s in sessions:
            sessions_by_date[s["session_date"].isoformat()].append(s)

        max_subs = (
            max(
                (s.get("submissions_for", 0) or 0 for s in sessions),
                default=1,
            )
            or 1
        )

        rem_pcts: list[float] = []
        sws_pcts: list[float] = []
        sleep_hours_list: list[float] = []
        qualities: list[float] = []
        scatter: list[dict] = []

        for rec in recs:
            cs = rec.get("cycle_start", "")
            if not cs:
                continue
            cs_date = cs[:10]
            try:
                d = date.fromisoformat(cs_date)
            except ValueError:
                continue
            next_day = (d + timedelta(days=1)).isoformat()

            matched = sessions_by_date.get(next_day, sessions_by_date.get(cs_date, []))
            if not matched:
                continue

            dur_ms = rec.get("sleep_duration_ms")
            rem_ms = rec.get("rem_sleep_ms")
            sws_ms = rec.get("slow_wave_ms")

            if dur_ms is None or dur_ms <= 0:
                continue

            sleep_hrs = dur_ms / 3_600_000
            rem_pct = (rem_ms / dur_ms * 100) if rem_ms is not None else None
            sws_pct = (sws_ms / dur_ms * 100) if sws_ms is not None else None

            total_for = sum(s.get("submissions_for", 0) or 0 for s in matched)
            quality = round((total_for / max_subs) * 100, 1)

            if rem_pct is not None:
                rem_pcts.append(rem_pct)
            if sws_pct is not None:
                sws_pcts.append(sws_pct)
            sleep_hours_list.append(sleep_hrs)
            qualities.append(quality)

            scatter.append(
                {
                    "date": cs_date,
                    "sleep_hours": round(sleep_hrs, 1),
                    "rem_pct": (round(rem_pct, 1) if rem_pct is not None else None),
                    "sws_pct": (round(sws_pct, 1) if sws_pct is not None else None),
                    "quality": quality,
                }
            )

        rem_r = _pearson_r(rem_pcts, qualities[: len(rem_pcts)])
        sws_r = _pearson_r(sws_pcts, qualities[: len(sws_pcts)])
        total_sleep_r = _pearson_r(sleep_hours_list, qualities)

        optimal_rem = round(statistics.median(rem_pcts), 1) if rem_pcts else 0
        optimal_sws = round(statistics.median(sws_pcts), 1) if sws_pcts else 0

        parts = []
        if abs(total_sleep_r) >= 0.2:
            parts.append(
                f"Total sleep correlates with performance" f" (r={total_sleep_r})"
            )
        if abs(rem_r) >= 0.2:
            parts.append(f"REM sleep matters (r={rem_r})")
        if abs(sws_r) >= 0.2:
            parts.append(f"Deep sleep matters (r={sws_r})")
        insight = (
            ". ".join(parts) + "."
            if parts
            else ("Weak sleep-performance correlation so far.")
        )

        return {
            "rem_r": rem_r,
            "sws_r": sws_r,
            "total_sleep_r": total_sleep_r,
            "scatter": scatter,
            "optimal_rem_pct": optimal_rem,
            "optimal_sws_pct": optimal_sws,
            "insight": insight,
        }

    # ------------------------------------------------------------------
    # 5. Cardiovascular drift (RHR trend)
    # ------------------------------------------------------------------

    def get_cardiovascular_drift(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """Weekly avg RHR trend with slope classification."""
        end = date.today()
        start = end - timedelta(days=days)

        start_dt = start.isoformat()
        end_dt = end.isoformat() + "T23:59:59"

        recs = WhoopRecoveryCacheRepository.get_by_date_range(user_id, start_dt, end_dt)

        if not recs:
            return {
                "weekly_rhr": [],
                "slope": 0.0,
                "trend": "insufficient_data",
                "current_rhr": None,
                "baseline_rhr": None,
                "insight": "Not enough RHR data for trend analysis.",
            }

        # Group by ISO week
        weekly: dict[str, list[float]] = defaultdict(list)
        for r in recs:
            rhr = r.get("resting_hr")
            if rhr is None:
                continue
            cs = r.get("cycle_start", "")
            if not cs:
                continue
            try:
                d = date.fromisoformat(cs[:10])
            except ValueError:
                continue
            week_key = d.strftime("%Y-W%U")
            weekly[week_key].append(float(rhr))

        if len(weekly) < 2:
            current = recs[-1].get("resting_hr")
            return {
                "weekly_rhr": [],
                "slope": 0.0,
                "trend": "insufficient_data",
                "current_rhr": current,
                "baseline_rhr": current,
                "insight": "Need 2+ weeks of RHR data for trend.",
            }

        weekly_avgs = []
        for wk in sorted(weekly.keys()):
            vals = weekly[wk]
            weekly_avgs.append(
                {
                    "week": wk,
                    "avg_rhr": round(statistics.mean(vals), 1),
                    "data_points": len(vals),
                }
            )

        avg_values = [w["avg_rhr"] for w in weekly_avgs]
        slope = _linear_slope(avg_values)

        if slope < -0.3:
            trend = "improving"
        elif slope > 0.3:
            trend = "rising"
        else:
            trend = "stable"

        current_rhr = weekly_avgs[-1]["avg_rhr"]
        baseline_rhr = weekly_avgs[0]["avg_rhr"]

        trend_labels = {
            "improving": "declining (improving fitness)",
            "rising": "rising (possible fatigue)",
            "stable": "stable",
        }
        insight = (
            f"RHR trend: {trend_labels[trend]}."
            f" Current: {current_rhr} bpm,"
            f" baseline: {baseline_rhr} bpm"
            f" (slope: {slope:+.2f} bpm/week)."
        )

        return {
            "weekly_rhr": weekly_avgs,
            "slope": slope,
            "trend": trend,
            "current_rhr": current_rhr,
            "baseline_rhr": baseline_rhr,
            "insight": insight,
        }

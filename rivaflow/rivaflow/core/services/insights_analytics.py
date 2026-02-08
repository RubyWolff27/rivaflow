"""Advanced insights analytics engine — correlation, trends, and predictions.

Pure Python math (no numpy). Uses Pearson r, EWMA, Shannon entropy.
"""

import math
import statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

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

# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


def _pearson_r(xs: list[float], ys: list[float]) -> float:
    """Compute Pearson correlation coefficient. Returns 0 if insufficient data."""
    n = len(xs)
    if n < 3 or len(ys) != n:
        return 0.0
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return round(num / (denom_x * denom_y), 3)


def _ewma(values: list[float], span: int) -> list[float]:
    """Exponentially weighted moving average."""
    if not values:
        return []
    alpha = 2.0 / (span + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return [round(r, 2) for r in result]


def _shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy normalized to 0-100 scale."""
    total = sum(counts)
    if total == 0 or len(counts) <= 1:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    raw = -sum(p * math.log2(p) for p in probs)
    max_entropy = math.log2(len(probs))
    if max_entropy == 0:
        return 0.0
    return round((raw / max_entropy) * 100, 1)


def _linear_slope(ys: list[float]) -> float:
    """Simple linear regression slope over index 0..n-1."""
    n = len(ys)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2.0
    mean_y = statistics.mean(ys)
    num = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(ys))
    denom = sum((i - mean_x) ** 2 for i in range(n))
    if denom == 0:
        return 0.0
    return round(num / denom, 4)


class InsightsAnalyticsService:
    """Data-science-driven insights engine."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()
        self.roll_repo = SessionRollRepository()
        self.friend_repo = FriendRepository()
        self.glossary_repo = GlossaryRepository()
        self.technique_repo = SessionTechniqueRepository()

    # ------------------------------------------------------------------
    # 1. Readiness × Performance correlation
    # ------------------------------------------------------------------

    def get_readiness_performance_correlation(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Match readiness to same-day sessions, compute Pearson r."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        readiness = self.readiness_repo.get_by_date_range(user_id, start_date, end_date)
        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

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

    # ------------------------------------------------------------------
    # 2. Training load management (ACWR)
    # ------------------------------------------------------------------

    def get_training_load_management(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """EWMA acute (7d) vs chronic (28d) training load."""
        end = date.today()
        start = end - timedelta(days=days + 28)

        sessions = self.session_repo.get_by_date_range(user_id, start, end)

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

        insight = f"Your ACWR is {current_acwr} — {zone_labels.get(current_zone, current_zone)}."
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

    # ------------------------------------------------------------------
    # 3. Technique effectiveness
    # ------------------------------------------------------------------

    def get_technique_effectiveness(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Cross-ref submissions with technique training frequency."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)
        session_ids = [s["id"] for s in sessions]

        # Get rolls for submission data
        rolls_by_session = self.roll_repo.get_by_session_ids(user_id, session_ids)

        # Count submissions by movement
        sub_counts: Counter = Counter()
        for rolls in rolls_by_session.values():
            for roll in rolls:
                for mid in roll.get("submissions_for") or []:
                    sub_counts[mid] += 1

        # Count technique training frequency
        techs_by_session = self.technique_repo.batch_get_by_session_ids(session_ids)
        train_counts: Counter = Counter()
        for techs in techs_by_session.values():
            for tech in techs:
                mid = tech.get("movement_id")
                if mid:
                    train_counts[mid] += 1

        # Build glossary lookup
        movements = self.glossary_repo.list_all()
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
        sub_count_values = [
            t["submissions"] for t in techniques if t["submissions"] > 0
        ]
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

    # ------------------------------------------------------------------
    # 4. Partner progression
    # ------------------------------------------------------------------

    def get_partner_progression(
        self,
        user_id: int,
        partner_id: int,
    ) -> dict[str, Any]:
        """Rolling 5-roll window sub rate against a specific partner."""
        partner = self.friend_repo.get_by_id(user_id, partner_id)
        if not partner:
            return {
                "progression": [],
                "trend": "unknown",
                "partner": None,
                "insight": "Partner not found.",
            }

        # Get all rolls with this partner
        rolls = self.roll_repo.get_by_partner_id(user_id, partner_id)
        # Also get by name
        name_rolls = self.roll_repo.list_by_partner_name(user_id, partner["name"])

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
                s = self.session_repo.get_by_id(user_id, sid)
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

    # ------------------------------------------------------------------
    # 5. Session quality scores
    # ------------------------------------------------------------------

    def get_session_quality_scores(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Composite per-session quality score (0-100)."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

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
        max_subs = (
            max((s.get("submissions_for", 0) or 0 for s in sessions), default=1) or 1
        )

        # Get technique counts
        session_ids = [s["id"] for s in sessions]
        techs = self.technique_repo.batch_get_by_session_ids(session_ids)
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

    # ------------------------------------------------------------------
    # 6. Overtraining risk
    # ------------------------------------------------------------------

    def get_overtraining_risk(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """4 factors x 25pts = 0-100 risk score."""
        end = date.today()
        start_14d = end - timedelta(days=14)
        start_7d = end - timedelta(days=7)
        start_90d = end - timedelta(days=90)

        # Factor 1: ACWR spike (25 pts)
        load_data = self.get_training_load_management(user_id, days=90)
        acwr = load_data["current_acwr"]
        if acwr >= 1.5:
            acwr_risk = 25
        elif acwr >= 1.3:
            acwr_risk = 15
        elif acwr >= 1.1:
            acwr_risk = 5
        else:
            acwr_risk = 0

        # Factor 2: Readiness decline (14-day slope, 25 pts)
        readiness = self.readiness_repo.get_by_date_range(user_id, start_14d, end)
        readiness_scores = [r["composite_score"] for r in readiness]
        readiness_slope = _linear_slope(readiness_scores)
        if readiness_slope < -0.5:
            readiness_risk = 25
        elif readiness_slope < -0.2:
            readiness_risk = 15
        elif readiness_slope < 0:
            readiness_risk = 5
        else:
            readiness_risk = 0

        # Factor 3: Hotspot mentions (7d, 25 pts)
        readiness_7d = self.readiness_repo.get_by_date_range(user_id, start_7d, end)
        hotspot_count = sum(1 for r in readiness_7d if r.get("hotspot_note"))
        if hotspot_count >= 4:
            hotspot_risk = 25
        elif hotspot_count >= 2:
            hotspot_risk = 15
        elif hotspot_count >= 1:
            hotspot_risk = 5
        else:
            hotspot_risk = 0

        # Factor 4: Intensity creep (25 pts)
        sessions_90d = self.session_repo.get_by_date_range(user_id, start_90d, end)
        if len(sessions_90d) >= 5:
            half = len(sessions_90d) // 2
            first_half = [s.get("intensity", 0) or 0 for s in sessions_90d[:half]]
            second_half = [s.get("intensity", 0) or 0 for s in sessions_90d[half:]]
            avg_first = statistics.mean(first_half) if first_half else 0
            avg_second = statistics.mean(second_half) if second_half else 0
            intensity_diff = avg_second - avg_first
            if intensity_diff >= 1.0:
                intensity_risk = 25
            elif intensity_diff >= 0.5:
                intensity_risk = 15
            elif intensity_diff >= 0.2:
                intensity_risk = 5
            else:
                intensity_risk = 0
        else:
            intensity_risk = 0

        total_risk = acwr_risk + readiness_risk + hotspot_risk + intensity_risk

        if total_risk >= 60:
            level = "red"
        elif total_risk >= 30:
            level = "yellow"
        else:
            level = "green"

        recommendations = []
        if acwr_risk >= 15:
            recommendations.append("Reduce training volume — ACWR is elevated.")
        if readiness_risk >= 15:
            recommendations.append(
                "Readiness trending down — prioritize sleep and recovery."
            )
        if hotspot_risk >= 15:
            recommendations.append(
                "Multiple injury hotspots noted — consider rest days."
            )
        if intensity_risk >= 15:
            recommendations.append("Intensity creeping up — mix in lighter sessions.")
        if not recommendations:
            recommendations.append("Training load looks healthy. Keep it up!")

        return {
            "risk_score": total_risk,
            "level": level,
            "factors": {
                "acwr_spike": {"score": acwr_risk, "max": 25},
                "readiness_decline": {"score": readiness_risk, "max": 25},
                "hotspot_mentions": {"score": hotspot_risk, "max": 25},
                "intensity_creep": {"score": intensity_risk, "max": 25},
            },
            "recommendations": recommendations,
        }

    # ------------------------------------------------------------------
    # 7. Recovery insights
    # ------------------------------------------------------------------

    def get_recovery_insights(
        self,
        user_id: int,
        days: int = 90,
    ) -> dict[str, Any]:
        """Sleep → next-day performance, optimal rest days analysis."""
        end = date.today()
        start = end - timedelta(days=days)

        readiness = self.readiness_repo.get_by_date_range(user_id, start, end)
        sessions = self.session_repo.get_by_date_range(user_id, start, end)

        # Sleep → next-day performance Pearson r
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

    # ------------------------------------------------------------------
    # 8. Summary digest
    # ------------------------------------------------------------------

    def get_insights_summary(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """Lightweight dashboard digest."""
        load = self.get_training_load_management(user_id, days=90)
        risk = self.get_overtraining_risk(user_id)
        technique = self.get_technique_effectiveness(user_id)
        quality = self.get_session_quality_scores(user_id)

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

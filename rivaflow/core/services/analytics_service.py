"""Analytics service for dashboard data calculations."""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict, Counter
import statistics

from rivaflow.db.repositories import (
    SessionRepository,
    ReadinessRepository,
    SessionRollRepository,
    FriendRepository,
    GradingRepository,
    GlossaryRepository,
)


class AnalyticsService:
    """Business logic for analytics and dashboard data."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.readiness_repo = ReadinessRepository()
        self.roll_repo = SessionRollRepository()
        self.friend_repo = FriendRepository()
        self.grading_repo = GradingRepository()
        self.glossary_repo = GlossaryRepository()

    # ============================================================================
    # PERFORMANCE OVERVIEW DASHBOARD
    # ============================================================================

    def get_performance_overview(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get performance overview metrics.

        Returns:
            - submission_success_over_time: Monthly breakdown of subs for/against
            - training_volume_calendar: Daily session data for heatmap
            - top_submissions: Top 5 subs given and received
            - performance_by_belt: Metrics grouped by belt rank periods
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

        # Submission success over time (monthly)
        monthly_stats = defaultdict(lambda: {"for": 0, "against": 0, "ratio": 0})
        for session in sessions:
            month_key = session["session_date"].strftime("%Y-%m")
            monthly_stats[month_key]["for"] += session["submissions_for"]
            monthly_stats[month_key]["against"] += session["submissions_against"]

        for month in monthly_stats:
            for_count = monthly_stats[month]["for"]
            against_count = monthly_stats[month]["against"]
            if against_count > 0:
                monthly_stats[month]["ratio"] = round(for_count / against_count, 2)
            else:
                monthly_stats[month]["ratio"] = for_count if for_count > 0 else 0

        # Training volume calendar (daily)
        volume_calendar = []
        for session in sessions:
            volume_calendar.append({
                "date": session["session_date"].isoformat(),
                "intensity": session["intensity"],
                "duration": session["duration_mins"],
                "class_type": session["class_type"],
                "sessions": 1,
            })

        # Top submissions (requires roll data with movement IDs)
        top_subs_for = Counter()
        top_subs_against = Counter()

        # Get detailed rolls in bulk to avoid N+1 queries
        session_ids = [session["id"] for session in sessions]
        rolls_by_session = self.roll_repo.get_by_session_ids(user_id, session_ids)

        for session in sessions:
            rolls = rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    for movement_id in roll["submissions_for"]:
                        top_subs_for[movement_id] += 1
                if roll.get("submissions_against"):
                    for movement_id in roll["submissions_against"]:
                        top_subs_against[movement_id] += 1

        # Convert movement IDs to names
        top_subs_for_list = []
        for movement_id, count in top_subs_for.most_common(5):
            movement = self.glossary_repo.get_by_id(user_id, movement_id)
            if movement:
                top_subs_for_list.append({
                    "name": movement["name"],
                    "count": count,
                    "id": movement_id,
                })

        top_subs_against_list = []
        for movement_id, count in top_subs_against.most_common(5):
            movement = self.glossary_repo.get_by_id(user_id, movement_id)
            if movement:
                top_subs_against_list.append({
                    "name": movement["name"],
                    "count": count,
                    "id": movement_id,
                })

        # Performance by belt rank
        gradings = self.grading_repo.list_all(user_id)
        belt_performance = self._calculate_performance_by_belt(sessions, gradings)

        return {
            "submission_success_over_time": [
                {"month": k, **v} for k, v in sorted(monthly_stats.items())
            ],
            "training_volume_calendar": volume_calendar,
            "top_submissions_for": top_subs_for_list,
            "top_submissions_against": top_subs_against_list,
            "performance_by_belt": belt_performance,
            "summary": {
                "total_sessions": len(sessions),
                "total_submissions_for": sum(s["submissions_for"] for s in sessions),
                "total_submissions_against": sum(s["submissions_against"] for s in sessions),
                "avg_intensity": round(
                    statistics.mean([s["intensity"] for s in sessions]) if sessions else 0, 1
                ),
            },
        }

    def _calculate_performance_by_belt(
        self, sessions: List[Dict], gradings: List[Dict]
    ) -> List[Dict]:
        """Calculate metrics for each belt rank period."""
        if not gradings:
            # No belt data, return overall stats
            return [{
                "belt": "unranked",
                "sessions": len(sessions),
                "subs_for": sum(s["submissions_for"] for s in sessions),
                "subs_against": sum(s["submissions_against"] for s in sessions),
            }]

        # Sort gradings by date
        sorted_gradings = sorted(gradings, key=lambda g: g["date_graded"])

        belt_periods = []
        for i, grading in enumerate(sorted_gradings):
            start = grading["date_graded"]
            if isinstance(start, str):
                start = date.fromisoformat(start)

            if i + 1 < len(sorted_gradings):
                end = sorted_gradings[i + 1]["date_graded"]
                if isinstance(end, str):
                    end = date.fromisoformat(end)
            else:
                end = date.today()

            period_sessions = [
                s for s in sessions
                if start <= s["session_date"] < end
            ]

            belt_periods.append({
                "belt": grading["grade"],
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "sessions": len(period_sessions),
                "subs_for": sum(s["submissions_for"] for s in period_sessions),
                "subs_against": sum(s["submissions_against"] for s in period_sessions),
            })

        return belt_periods

    # ============================================================================
    # PARTNER ANALYTICS DASHBOARD
    # ============================================================================

    def get_partner_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get partner analytics data.

        Returns:
            - partner_matrix: Table of all partners with stats
            - partner_diversity: Unique partners, new vs recurring
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

        # Get all partners from contacts
        partners = self.friend_repo.list_by_type(user_id, "training-partner")

        partner_matrix = []
        for partner in partners:
            stats = self.roll_repo.get_partner_stats(user_id, partner["id"])

            # Filter by date range
            rolls_in_range = self.roll_repo.get_by_partner_id(user_id, partner["id"])
            rolls_in_range = [
                r for r in rolls_in_range
                if start_date <= self._get_session_date(user_id, r["session_id"]) <= end_date
            ]

            partner_matrix.append({
                "id": partner["id"],
                "name": partner["name"],
                "belt_rank": partner.get("belt_rank"),
                "belt_stripes": partner.get("belt_stripes", 0),
                "total_rolls": len(rolls_in_range),
                "submissions_for": stats.get("total_submissions_for", 0),
                "submissions_against": stats.get("total_submissions_against", 0),
                "sub_ratio": stats.get("sub_ratio", 0),
                "subs_per_roll_for": stats.get("subs_per_roll_for", 0),
                "subs_per_roll_against": stats.get("subs_per_roll_against", 0),
            })

        # Sort by total rolls
        partner_matrix.sort(key=lambda p: p["total_rolls"], reverse=True)

        # Partner diversity metrics
        unique_partners = len([p for p in partner_matrix if p["total_rolls"] > 0])
        new_partners = len([p for p in partner_matrix if p["total_rolls"] <= 3])
        recurring_partners = len([p for p in partner_matrix if p["total_rolls"] > 3])

        return {
            "partner_matrix": partner_matrix,
            "diversity_metrics": {
                "unique_partners": unique_partners,
                "new_partners": new_partners,
                "recurring_partners": recurring_partners,
            },
        }

    def get_head_to_head(
        self, user_id: int, partner1_id: int, partner2_id: int
    ) -> Dict[str, Any]:
        """Get head-to-head comparison between two partners."""
        partner1 = self.friend_repo.get_by_id(user_id, partner1_id)
        partner2 = self.friend_repo.get_by_id(user_id, partner2_id)

        if not partner1 or not partner2:
            return {}

        stats1 = self.roll_repo.get_partner_stats(user_id, partner1_id)
        stats2 = self.roll_repo.get_partner_stats(user_id, partner2_id)

        return {
            "partner1": {
                "name": partner1["name"],
                "belt": partner1.get("belt_rank"),
                **stats1,
            },
            "partner2": {
                "name": partner2["name"],
                "belt": partner2.get("belt_rank"),
                **stats2,
            },
        }

    def _get_session_date(self, user_id: int, session_id: int) -> date:
        """Helper to get session date."""
        session = self.session_repo.get_by_id(user_id, session_id)
        return session["session_date"] if session else date.today()

    # ============================================================================
    # READINESS & RECOVERY DASHBOARD
    # ============================================================================

    def get_readiness_trends(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get readiness and recovery analytics.

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

        readiness_records = self.readiness_repo.get_by_date_range(user_id, start_date, end_date)
        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

        # Readiness over time
        readiness_over_time = []
        for record in readiness_records:
            readiness_over_time.append({
                "date": record["check_date"].isoformat(),
                "composite_score": record["composite_score"],
                "sleep": record["sleep"],
                "stress": record["stress"],
                "soreness": record["soreness"],
                "energy": record["energy"],
            })

        # Training load vs readiness (combine sessions with readiness on same day)
        load_vs_readiness = []
        for session in sessions:
            # Find readiness for same day
            matching_readiness = next(
                (r for r in readiness_records if r["check_date"] == session["session_date"]),
                None
            )
            if matching_readiness:
                load_vs_readiness.append({
                    "date": session["session_date"].isoformat(),
                    "readiness": matching_readiness["composite_score"],
                    "intensity": session["intensity"],
                    "duration": session["duration_mins"],
                    "class_type": session["class_type"],
                })

        # Recovery patterns by day of week
        day_of_week_readiness = defaultdict(list)
        for record in readiness_records:
            day_name = record["check_date"].strftime("%A")
            day_of_week_readiness[day_name].append(record["composite_score"])

        recovery_patterns = []
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            scores = day_of_week_readiness[day]
            recovery_patterns.append({
                "day": day,
                "avg_readiness": round(statistics.mean(scores), 1) if scores else 0,
                "count": len(scores),
            })

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
        weight_records = [r for r in readiness_records if r.get("weight_kg") is not None]
        weight_over_time = []
        for record in weight_records:
            weight_over_time.append({
                "date": record["check_date"].isoformat(),
                "weight_kg": round(record["weight_kg"], 1),
            })

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

        return {
            "readiness_over_time": readiness_over_time,
            "training_load_vs_readiness": load_vs_readiness,
            "recovery_patterns": recovery_patterns,
            "injury_timeline": injury_timeline,
            "weight_over_time": weight_over_time,
            "weight_stats": weight_stats,
        }

    # ============================================================================
    # WHOOP INTEGRATION DASHBOARD
    # ============================================================================

    def get_whoop_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get Whoop fitness tracker analytics.

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

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)
        whoop_sessions = [s for s in sessions if s.get("whoop_strain") is not None]

        # Strain vs performance
        strain_vs_performance = []
        for session in whoop_sessions:
            sub_ratio = 0
            if session["submissions_against"] > 0:
                sub_ratio = round(
                    session["submissions_for"] / session["submissions_against"], 2
                )

            strain_vs_performance.append({
                "date": session["session_date"].isoformat(),
                "strain": session.get("whoop_strain"),
                "submissions_for": session["submissions_for"],
                "submissions_against": session["submissions_against"],
                "sub_ratio": sub_ratio,
            })

        # Heart rate zones by class type
        hr_by_class = defaultdict(lambda: {"avg_hr": [], "max_hr": []})
        for session in whoop_sessions:
            if session.get("whoop_avg_hr"):
                hr_by_class[session["class_type"]]["avg_hr"].append(session["whoop_avg_hr"])
            if session.get("whoop_max_hr"):
                hr_by_class[session["class_type"]]["max_hr"].append(session["whoop_max_hr"])

        heart_rate_zones = []
        for class_type, hrs in hr_by_class.items():
            heart_rate_zones.append({
                "class_type": class_type,
                "avg_hr": round(statistics.mean(hrs["avg_hr"])) if hrs["avg_hr"] else 0,
                "max_hr": round(statistics.mean(hrs["max_hr"])) if hrs["max_hr"] else 0,
                "sessions": len(hrs["avg_hr"]),
            })

        # Calorie burn analysis
        calorie_analysis = defaultdict(lambda: {"calories": [], "duration": []})
        for session in whoop_sessions:
            if session.get("whoop_calories"):
                calorie_analysis[session["class_type"]]["calories"].append(session["whoop_calories"])
                calorie_analysis[session["class_type"]]["duration"].append(session["duration_mins"])

        calorie_burn = []
        for class_type, data in calorie_analysis.items():
            total_cals = sum(data["calories"])
            total_mins = sum(data["duration"])
            calorie_burn.append({
                "class_type": class_type,
                "total_calories": total_cals,
                "avg_calories": round(statistics.mean(data["calories"])) if data["calories"] else 0,
                "calories_per_min": round(total_cals / total_mins, 1) if total_mins > 0 else 0,
                "sessions": len(data["calories"]),
            })

        # Recovery correlation (Whoop strain vs next day readiness)
        readiness_records = self.readiness_repo.get_by_date_range(user_id, start_date, end_date)
        recovery_correlation = []

        for session in whoop_sessions:
            if session.get("whoop_strain"):
                next_day = session["session_date"] + timedelta(days=1)
                next_readiness = next(
                    (r for r in readiness_records if r["check_date"] == next_day),
                    None
                )
                if next_readiness:
                    recovery_correlation.append({
                        "date": session["session_date"].isoformat(),
                        "strain": session["whoop_strain"],
                        "next_day_readiness": next_readiness["composite_score"],
                    })

        return {
            "strain_vs_performance": strain_vs_performance,
            "heart_rate_zones": heart_rate_zones,
            "calorie_burn": calorie_burn,
            "recovery_correlation": recovery_correlation,
            "summary": {
                "total_whoop_sessions": len(whoop_sessions),
                "avg_strain": round(statistics.mean([s["whoop_strain"] for s in whoop_sessions if s.get("whoop_strain")]), 1) if whoop_sessions else 0,
                "total_calories": sum(s.get("whoop_calories", 0) for s in whoop_sessions),
            },
        }

    # ============================================================================
    # TECHNIQUE MASTERY DASHBOARD
    # ============================================================================

    def get_technique_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get technique mastery analytics.

        Returns:
            - category_breakdown: Time spent on each technique category
            - stale_techniques: Techniques not trained recently
            - success_heatmap: Technique success rates over time
            - gi_vs_nogi: Technique applicability comparison
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)
        movements = self.glossary_repo.list_all(user_id)

        # Category breakdown (count submissions by category)
        category_counts = Counter()

        # Get rolls in bulk to avoid N+1 queries
        session_ids = [session["id"] for session in sessions]
        rolls_by_session = self.roll_repo.get_by_session_ids(user_id, session_ids)

        for session in sessions:
            rolls = rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    for movement_id in roll["submissions_for"]:
                        movement = self.glossary_repo.get_by_id(user_id, movement_id)
                        if movement:
                            category_counts[movement["category"]] += 1

        category_breakdown = [
            {"category": cat, "count": count}
            for cat, count in category_counts.items()
        ]

        # Stale techniques (movements from glossary not used in X days)
        stale_threshold_days = 30
        stale_date = date.today() - timedelta(days=stale_threshold_days)

        all_movement_ids = {m["id"] for m in movements}
        used_movement_ids = set()

        recent_sessions = self.session_repo.get_by_date_range(user_id, stale_date, date.today())

        # Get rolls in bulk to avoid N+1 queries
        recent_session_ids = [session["id"] for session in recent_sessions]
        recent_rolls_by_session = self.roll_repo.get_by_session_ids(user_id, recent_session_ids)

        for session in recent_sessions:
            rolls = recent_rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    used_movement_ids.update(roll["submissions_for"])
                if roll.get("submissions_against"):
                    used_movement_ids.update(roll["submissions_against"])

        stale_movement_ids = all_movement_ids - used_movement_ids
        stale_techniques = [
            {
                "id": m["id"],
                "name": m["name"],
                "category": m["category"],
            }
            for m in movements
            if m["id"] in stale_movement_ids
        ]

        # Gi vs No-Gi comparison
        gi_sessions = [s for s in sessions if s["class_type"] == "gi"]
        nogi_sessions = [s for s in sessions if s["class_type"] == "no-gi"]

        gi_techniques = Counter()
        nogi_techniques = Counter()

        # Use already-loaded rolls from bulk query above
        for session in gi_sessions:
            rolls = rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    gi_techniques.update(roll["submissions_for"])

        for session in nogi_sessions:
            rolls = rolls_by_session.get(session["id"], [])
            for roll in rolls:
                if roll.get("submissions_for"):
                    nogi_techniques.update(roll["submissions_for"])

        # Get top 10 from each
        gi_top = []
        for movement_id, count in gi_techniques.most_common(10):
            movement = self.glossary_repo.get_by_id(user_id, movement_id)
            if movement:
                gi_top.append({"name": movement["name"], "count": count})

        nogi_top = []
        for movement_id, count in nogi_techniques.most_common(10):
            movement = self.glossary_repo.get_by_id(user_id, movement_id)
            if movement:
                nogi_top.append({"name": movement["name"], "count": count})

        return {
            "category_breakdown": category_breakdown,
            "stale_techniques": stale_techniques,
            "gi_top_techniques": gi_top,
            "nogi_top_techniques": nogi_top,
            "summary": {
                "total_unique_techniques_used": len(used_movement_ids),
                "stale_count": len(stale_techniques),
            },
        }

    # ============================================================================
    # TRAINING CONSISTENCY DASHBOARD
    # ============================================================================

    def get_consistency_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get training consistency analytics.

        Returns:
            - weekly_volume: Sessions/hours by week
            - class_type_distribution: Breakdown by class type
            - gym_breakdown: Training by location
            - streaks: Current and longest streaks
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

        # Weekly volume
        weekly_stats = defaultdict(lambda: {"sessions": 0, "hours": 0, "rolls": 0})
        for session in sessions:
            week_key = session["session_date"].strftime("%Y-W%U")
            weekly_stats[week_key]["sessions"] += 1
            weekly_stats[week_key]["hours"] += session["duration_mins"] / 60
            weekly_stats[week_key]["rolls"] += session["rolls"]

        weekly_volume = [
            {"week": k, **v} for k, v in sorted(weekly_stats.items())
        ]

        # Class type distribution
        class_type_counts = Counter(s["class_type"] for s in sessions)
        class_type_distribution = [
            {"class_type": ct, "count": count}
            for ct, count in class_type_counts.items()
        ]

        # Gym breakdown
        gym_counts = Counter(s["gym_name"] for s in sessions)
        gym_breakdown = [
            {"gym": gym, "sessions": count}
            for gym, count in gym_counts.most_common()
        ]

        # Calculate streaks
        all_sessions = self.session_repo.get_recent(user_id, 1000)  # Get more for streak calc
        current_streak, longest_streak = self._calculate_streaks(all_sessions)

        return {
            "weekly_volume": weekly_volume,
            "class_type_distribution": class_type_distribution,
            "gym_breakdown": gym_breakdown,
            "streaks": {
                "current": current_streak,
                "longest": longest_streak,
            },
        }

    def _calculate_streaks(self, sessions: List[Dict]) -> tuple:
        """Calculate current and longest training streaks."""
        if not sessions:
            return 0, 0

        # Sort by date descending
        sorted_sessions = sorted(sessions, key=lambda s: s["session_date"], reverse=True)

        # Get unique dates
        session_dates = sorted(list(set(s["session_date"] for s in sorted_sessions)), reverse=True)

        current_streak = 0
        longest_streak = 0
        temp_streak = 1

        # Calculate current streak from today
        today = date.today()
        if session_dates and session_dates[0] >= today - timedelta(days=1):
            current_streak = 1
            for i in range(1, len(session_dates)):
                if session_dates[i] == session_dates[i-1] - timedelta(days=1):
                    current_streak += 1
                else:
                    break

        # Calculate longest streak
        for i in range(1, len(session_dates)):
            if session_dates[i] == session_dates[i-1] - timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1

        longest_streak = max(longest_streak, temp_streak)

        return current_streak, longest_streak

    # ============================================================================
    # PROGRESSION & MILESTONES DASHBOARD
    # ============================================================================

    def get_milestones(self, user_id: int) -> Dict[str, Any]:
        """
        Get progression and milestone data.

        Returns:
            - belt_progression: Timeline of belt promotions
            - personal_records: Best performances
            - rolling_totals: Lifetime and current belt stats
        """
        all_sessions = self.session_repo.get_recent(user_id, 10000)  # Get all
        gradings = self.grading_repo.list_all(user_id)

        # Belt progression timeline
        belt_progression = []
        sorted_gradings = sorted(gradings, key=lambda g: g["date_graded"])

        for i, grading in enumerate(sorted_gradings):
            start = grading["date_graded"]
            if isinstance(start, str):
                start = date.fromisoformat(start)

            if i + 1 < len(sorted_gradings):
                end = sorted_gradings[i + 1]["date_graded"]
                if isinstance(end, str):
                    end = date.fromisoformat(end)
            else:
                end = date.today()

            period_sessions = [
                s for s in all_sessions
                if start <= s["session_date"] < end
            ]

            belt_progression.append({
                "belt": grading["grade"],
                "date": start.isoformat(),
                "professor": grading.get("professor"),
                "sessions_at_belt": len(period_sessions),
                "hours_at_belt": sum(s["duration_mins"] for s in period_sessions) / 60,
            })

        # Personal records
        personal_records = {
            "most_rolls_session": max(all_sessions, key=lambda s: s["rolls"])["rolls"] if all_sessions else 0,
            "longest_session": max(all_sessions, key=lambda s: s["duration_mins"])["duration_mins"] if all_sessions else 0,
            "best_sub_ratio_day": 0,
            "most_partners_session": 0,
        }

        # Best submission ratio
        for session in all_sessions:
            if session["submissions_against"] > 0:
                ratio = session["submissions_for"] / session["submissions_against"]
                personal_records["best_sub_ratio_day"] = max(
                    personal_records["best_sub_ratio_day"], ratio
                )

        # Rolling totals
        total_sessions = len(all_sessions)
        total_hours = sum(s["duration_mins"] for s in all_sessions) / 60
        total_rolls = sum(s["rolls"] for s in all_sessions)
        total_subs = sum(s["submissions_for"] for s in all_sessions)

        # Current belt stats (if gradings exist)
        current_belt_sessions = 0
        current_belt_hours = 0
        if gradings:
            latest_grading = max(gradings, key=lambda g: g["date_graded"] if isinstance(g["date_graded"], date) else date.fromisoformat(g["date_graded"]))
            latest_date = latest_grading["date_graded"]
            if isinstance(latest_date, str):
                latest_date = date.fromisoformat(latest_date)

            current_belt_sessions_list = [
                s for s in all_sessions
                if s["session_date"] >= latest_date
            ]
            current_belt_sessions = len(current_belt_sessions_list)
            current_belt_hours = sum(s["duration_mins"] for s in current_belt_sessions_list) / 60

        # This year stats
        year_start = date(date.today().year, 1, 1)
        year_sessions = [s for s in all_sessions if s["session_date"] >= year_start]
        year_stats = {
            "sessions": len(year_sessions),
            "hours": sum(s["duration_mins"] for s in year_sessions) / 60,
            "rolls": sum(s["rolls"] for s in year_sessions),
        }

        return {
            "belt_progression": belt_progression,
            "personal_records": personal_records,
            "rolling_totals": {
                "lifetime": {
                    "sessions": total_sessions,
                    "hours": round(total_hours, 1),
                    "rolls": total_rolls,
                    "submissions": total_subs,
                },
                "current_belt": {
                    "sessions": current_belt_sessions,
                    "hours": round(current_belt_hours, 1),
                },
                "this_year": year_stats,
            },
        }

    # ============================================================================
    # INSTRUCTOR INSIGHTS DASHBOARD
    # ============================================================================

    def get_instructor_analytics(
        self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get instructor insights.

        Returns:
            - performance_by_instructor: Metrics for each instructor
            - instructor_styles: Teaching style analysis
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)
        instructors = self.friend_repo.list_by_type(user_id, "instructor")

        performance_by_instructor = []
        for instructor in instructors:
            instructor_sessions = [
                s for s in sessions
                if s.get("instructor_id") == instructor["id"]
            ]

            if not instructor_sessions:
                continue

            # Calculate metrics
            total_sessions = len(instructor_sessions)
            avg_intensity = statistics.mean([s["intensity"] for s in instructor_sessions])
            total_subs_for = sum(s["submissions_for"] for s in instructor_sessions)
            total_subs_against = sum(s["submissions_against"] for s in instructor_sessions)

            # Analyze techniques taught
            techniques_taught = Counter()
            for session in instructor_sessions:
                if session.get("techniques"):
                    techniques_taught.update(session["techniques"])

            performance_by_instructor.append({
                "instructor_id": instructor["id"],
                "instructor_name": instructor["name"],
                "belt_rank": instructor.get("belt_rank"),
                "certification": instructor.get("instructor_certification"),
                "total_sessions": total_sessions,
                "avg_intensity": round(avg_intensity, 1),
                "submissions_for": total_subs_for,
                "submissions_against": total_subs_against,
                "top_techniques": [
                    {"name": tech, "count": count}
                    for tech, count in techniques_taught.most_common(5)
                ],
            })

        return {
            "performance_by_instructor": performance_by_instructor,
        }

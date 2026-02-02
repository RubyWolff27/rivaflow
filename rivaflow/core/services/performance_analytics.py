"""Performance analytics service for training sessions."""
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict, Counter
import statistics

from rivaflow.db.repositories import (
    SessionRepository,
    SessionRollRepository,
    FriendRepository,
    GradingRepository,
    GlossaryRepository,
)


class PerformanceAnalyticsService:
    """Business logic for performance and partner analytics."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.roll_repo = SessionRollRepository()
        self.friend_repo = FriendRepository()
        self.grading_repo = GradingRepository()
        self.glossary_repo = GlossaryRepository()

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

        # Calculate ratios with division by zero protection
        for month in monthly_stats:
            for_count = monthly_stats[month]["for"]
            against_count = monthly_stats[month]["against"]
            if against_count > 0:
                monthly_stats[month]["ratio"] = round(for_count / against_count, 2)
            elif for_count > 0:
                monthly_stats[month]["ratio"] = float(for_count)
            else:
                monthly_stats[month]["ratio"] = 0.0

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
            movement = self.glossary_repo.get_by_id(movement_id)
            if movement:
                top_subs_for_list.append({
                    "name": movement["name"],
                    "count": count,
                    "id": movement_id,
                })

        top_subs_against_list = []
        for movement_id, count in top_subs_against.most_common(5):
            movement = self.glossary_repo.get_by_id(movement_id)
            if movement:
                top_subs_against_list.append({
                    "name": movement["name"],
                    "count": count,
                    "id": movement_id,
                })

        # Performance by belt rank
        gradings = self.grading_repo.list_all(user_id)
        belt_performance = self._calculate_performance_by_belt(sessions, gradings)

        # Daily time series for sparklines
        daily_timeseries = self._calculate_daily_timeseries(sessions, start_date, end_date)

        # Previous period comparison for deltas
        period_length = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_length)
        prev_end = start_date - timedelta(days=1)
        prev_sessions = self.session_repo.get_by_date_range(user_id, prev_start, prev_end)
        prev_summary = self._calculate_period_summary(prev_sessions)
        current_summary = self._calculate_period_summary(sessions)

        # Calculate deltas
        deltas = {
            "sessions": current_summary["total_sessions"] - prev_summary["total_sessions"],
            "intensity": round(current_summary["avg_intensity"] - prev_summary["avg_intensity"], 1),
            "rolls": current_summary["total_rolls"] - prev_summary["total_rolls"],
            "submissions": current_summary["total_submissions_for"] - prev_summary["total_submissions_for"],
        }

        return {
            "submission_success_over_time": [
                {"month": k, **v} for k, v in sorted(monthly_stats.items())
            ],
            "training_volume_calendar": volume_calendar,
            "daily_timeseries": daily_timeseries,
            "top_submissions_for": top_subs_for_list,
            "top_submissions_against": top_subs_against_list,
            "performance_by_belt": belt_performance,
            "summary": current_summary,
            "deltas": deltas,
        }

    def _calculate_period_summary(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Calculate summary metrics for a period with safe null handling."""
        if not sessions:
            return {
                "total_sessions": 0,
                "total_submissions_for": 0,
                "total_submissions_against": 0,
                "total_rolls": 0,
                "avg_intensity": 0.0,
            }

        return {
            "total_sessions": len(sessions),
            "total_submissions_for": sum(s.get("submissions_for", 0) or 0 for s in sessions),
            "total_submissions_against": sum(s.get("submissions_against", 0) or 0 for s in sessions),
            "total_rolls": sum(s.get("rolls", 0) or 0 for s in sessions),
            "avg_intensity": round(
                statistics.mean([s.get("intensity", 0) or 0 for s in sessions]) if sessions else 0, 1
            ),
        }

    def _calculate_daily_timeseries(
        self, sessions: List[Dict], start_date: date, end_date: date
    ) -> Dict[str, List[float]]:
        """Calculate daily aggregated time series data for sparklines."""
        # Create a dict for each day in the range
        daily_data = defaultdict(lambda: {
            "sessions": 0,
            "total_intensity": 0,
            "rolls": 0,
            "submissions": 0,
        })

        # Aggregate sessions by day
        for session in sessions:
            day_key = session["session_date"].isoformat()
            daily_data[day_key]["sessions"] += 1
            daily_data[day_key]["total_intensity"] += session["intensity"]
            daily_data[day_key]["rolls"] += session.get("rolls", 0)
            daily_data[day_key]["submissions"] += session["submissions_for"]

        # Build ordered time series arrays
        current_day = start_date
        sessions_series = []
        intensity_series = []
        rolls_series = []
        submissions_series = []

        while current_day <= end_date:
            day_key = current_day.isoformat()
            data = daily_data[day_key]

            sessions_series.append(data["sessions"])

            # Avg intensity for the day (if any sessions)
            if data["sessions"] > 0:
                intensity_series.append(round(data["total_intensity"] / data["sessions"], 1))
            else:
                intensity_series.append(0)

            rolls_series.append(data["rolls"])
            submissions_series.append(data["submissions"])

            current_day += timedelta(days=1)

        return {
            "sessions": sessions_series,
            "intensity": intensity_series,
            "rolls": rolls_series,
            "submissions": submissions_series,
        }

    def _calculate_partner_session_distribution(
        self, user_id: int, sessions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Calculate which partners appear in which sessions."""
        # Get all session IDs
        session_ids = [s["id"] for s in sessions]

        # Get rolls for these sessions
        rolls_by_session = self.roll_repo.get_by_session_ids(user_id, session_ids)

        # Count sessions per partner
        partner_session_count = defaultdict(int)
        partner_names = {}

        for session in sessions:
            rolls = rolls_by_session.get(session["id"], [])
            partners_in_session = set()

            for roll in rolls:
                if roll.get("partner_id"):
                    partners_in_session.add(roll["partner_id"])

            for partner_id in partners_in_session:
                partner_session_count[partner_id] += 1
                if partner_id not in partner_names:
                    partner = self.friend_repo.get_by_id(user_id, partner_id)
                    if partner:
                        partner_names[partner_id] = partner["name"]

        # Build distribution list
        distribution = []
        for partner_id, session_count in partner_session_count.items():
            distribution.append({
                "partner_id": partner_id,
                "partner_name": partner_names.get(partner_id, "Unknown"),
                "session_count": session_count,
            })

        # Sort by session count
        distribution.sort(key=lambda x: x["session_count"], reverse=True)
        return distribution

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
        active_partners = [p for p in partner_matrix if p["total_rolls"] > 0]
        unique_partners = len(active_partners)
        new_partners = len([p for p in active_partners if p["total_rolls"] <= 3])
        recurring_partners = len([p for p in active_partners if p["total_rolls"] > 3])

        # Top partners summary (top 5)
        top_partners = partner_matrix[:5] if len(partner_matrix) >= 5 else partner_matrix

        # Calculate session distribution by partner
        session_distribution = self._calculate_partner_session_distribution(user_id, sessions)

        # Overall partner stats
        total_rolls_all_partners = sum(p["total_rolls"] for p in partner_matrix)
        total_subs_for = sum(p["submissions_for"] for p in partner_matrix)
        total_subs_against = sum(p["submissions_against"] for p in partner_matrix)

        return {
            "partner_matrix": partner_matrix,
            "top_partners": top_partners,
            "session_distribution": session_distribution,
            "diversity_metrics": {
                "unique_partners": unique_partners,
                "new_partners": new_partners,
                "recurring_partners": recurring_partners,
            },
            "summary": {
                "total_partners": len(partners),
                "active_partners": unique_partners,
                "total_rolls": total_rolls_all_partners,
                "total_submissions_for": total_subs_for,
                "total_submissions_against": total_subs_against,
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

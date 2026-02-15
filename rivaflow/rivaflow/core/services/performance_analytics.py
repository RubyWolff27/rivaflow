"""Performance analytics service for training sessions."""

import json
import statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from rivaflow.db.repositories import (
    FriendRepository,
    GlossaryRepository,
    GradingRepository,
    SessionRepository,
    SessionRollRepository,
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
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get performance overview metrics.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

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

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )

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
            volume_calendar.append(
                {
                    "date": session["session_date"].isoformat(),
                    "intensity": session["intensity"],
                    "duration": session["duration_mins"],
                    "class_type": session["class_type"],
                    "sessions": 1,
                }
            )

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
                top_subs_for_list.append(
                    {
                        "name": movement["name"],
                        "count": count,
                        "id": movement_id,
                    }
                )

        top_subs_against_list = []
        for movement_id, count in top_subs_against.most_common(5):
            movement = self.glossary_repo.get_by_id(movement_id)
            if movement:
                top_subs_against_list.append(
                    {
                        "name": movement["name"],
                        "count": count,
                        "id": movement_id,
                    }
                )

        # Performance by belt rank
        gradings = self.grading_repo.list_all(user_id)
        belt_performance = self._calculate_performance_by_belt(sessions, gradings)

        # Daily time series for sparklines
        daily_timeseries = self._calculate_daily_timeseries(
            sessions, start_date, end_date
        )

        # Previous period comparison for deltas
        period_length = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_length)
        prev_end = start_date - timedelta(days=1)
        prev_sessions = self.session_repo.get_by_date_range(
            user_id, prev_start, prev_end
        )
        prev_summary = self._calculate_period_summary(prev_sessions)
        current_summary = self._calculate_period_summary(sessions)

        # Calculate deltas
        deltas = {
            "sessions": current_summary["total_sessions"]
            - prev_summary["total_sessions"],
            "intensity": round(
                current_summary["avg_intensity"] - prev_summary["avg_intensity"], 1
            ),
            "rolls": current_summary["total_rolls"] - prev_summary["total_rolls"],
            "submissions": current_summary["total_submissions_for"]
            - prev_summary["total_submissions_for"],
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

    def _calculate_period_summary(self, sessions: list[dict]) -> dict[str, Any]:
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
            "total_submissions_for": sum(
                s.get("submissions_for", 0) or 0 for s in sessions
            ),
            "total_submissions_against": sum(
                s.get("submissions_against", 0) or 0 for s in sessions
            ),
            "total_rolls": sum(s.get("rolls", 0) or 0 for s in sessions),
            "avg_intensity": round(
                (
                    statistics.mean([s.get("intensity", 0) or 0 for s in sessions])
                    if sessions
                    else 0
                ),
                1,
            ),
        }

    def _calculate_daily_timeseries(
        self, sessions: list[dict], start_date: date, end_date: date
    ) -> dict[str, list[float]]:
        """Calculate daily aggregated time series data for sparklines."""
        # Create a dict for each day in the range
        daily_data = defaultdict(
            lambda: {
                "sessions": 0,
                "total_intensity": 0,
                "rolls": 0,
                "submissions": 0,
            }
        )

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
                intensity_series.append(
                    round(data["total_intensity"] / data["sessions"], 1)
                )
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
        self, user_id: int, sessions: list[dict]
    ) -> list[dict[str, Any]]:
        """Calculate which partners appear in which sessions."""
        # Get all session IDs
        session_ids = [s["id"] for s in sessions]

        # Get rolls for these sessions
        rolls_by_session = self.roll_repo.get_by_session_ids(user_id, session_ids)

        # Count sessions per partner
        partner_session_count = defaultdict(int)
        partner_names = {}

        # Build name→id lookup from friends for matching simple partners
        all_partners = self.friend_repo.list_by_type(user_id, "training-partner")
        name_to_id: dict[str, int] = {}
        for p in all_partners:
            name_to_id[p["name"].strip().lower()] = p["id"]
            partner_names[p["id"]] = p["name"]

        for session in sessions:
            rolls = rolls_by_session.get(session["id"], [])
            partners_in_session: set[int] = set()

            # Detailed rolls
            for roll in rolls:
                if roll.get("partner_id"):
                    partners_in_session.add(roll["partner_id"])

            # Simple-mode partners from sessions.partners JSON
            import json

            raw = session.get("partners")
            if raw:
                try:
                    plist = json.loads(raw) if isinstance(raw, str) else raw
                    if isinstance(plist, list):
                        for name in plist:
                            pid = name_to_id.get(name.strip().lower())
                            if pid:
                                partners_in_session.add(pid)
                except (json.JSONDecodeError, TypeError):
                    pass

            for partner_id in partners_in_session:
                partner_session_count[partner_id] += 1

        # Build distribution list
        distribution = []
        for partner_id, session_count in partner_session_count.items():
            distribution.append(
                {
                    "partner_id": partner_id,
                    "partner_name": partner_names.get(partner_id, "Unknown"),
                    "session_count": session_count,
                }
            )

        # Sort by session count
        distribution.sort(key=lambda x: x["session_count"], reverse=True)
        return distribution

    def _calculate_performance_by_belt(
        self, sessions: list[dict], gradings: list[dict]
    ) -> list[dict]:
        """Calculate metrics for each belt rank period."""
        if not gradings:
            # No belt data, return overall stats
            return [
                {
                    "belt": "unranked",
                    "sessions": len(sessions),
                    "subs_for": sum(s["submissions_for"] for s in sessions),
                    "subs_against": sum(s["submissions_against"] for s in sessions),
                }
            ]

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

            period_sessions = [s for s in sessions if start <= s["session_date"] < end]

            belt_periods.append(
                {
                    "belt": grading["grade"],
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "sessions": len(period_sessions),
                    "subs_for": sum(s["submissions_for"] for s in period_sessions),
                    "subs_against": sum(
                        s["submissions_against"] for s in period_sessions
                    ),
                }
            )

        return belt_periods

    def get_partner_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get partner analytics data.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - partner_matrix: Table of all partners with stats
            - partner_diversity: Unique partners, new vs recurring
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )

        # Get all partners from contacts (including 'other' type)
        partners = self.friend_repo.list_by_type(user_id, "training-partner")
        other = self.friend_repo.list_by_type(user_id, "other")
        seen_ids = {p["id"] for p in partners}
        for o in other:
            if o["id"] not in seen_ids:
                partners.append(o)

        # Count simple-mode partner mentions from sessions.partners JSON
        simple_partner_counts: dict[str, int] = {}
        for s in sessions:
            raw = s.get("partners")
            if not raw:
                continue
            try:
                plist = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(plist, list):
                    for name in plist:
                        name_lower = name.strip().lower()
                        simple_partner_counts[name_lower] = (
                            simple_partner_counts.get(name_lower, 0) + 1
                        )
            except (json.JSONDecodeError, TypeError):
                pass

        partner_matrix = []
        for partner in partners:
            stats = self.roll_repo.get_partner_stats(user_id, partner["id"])

            # Count detailed rolls in date range (linked by partner_id)
            rolls_in_range = self.roll_repo.get_by_partner_id(user_id, partner["id"])
            rolls_in_range = [
                r
                for r in rolls_in_range
                if start_date
                <= self._get_session_date(user_id, r["session_id"])
                <= end_date
            ]
            detailed_count = len(rolls_in_range)

            # Also count unlinked rolls (partner_id IS NULL, matched by name)
            unlinked_rolls = self.roll_repo.list_by_partner_name(
                user_id, partner["name"]
            )
            unlinked_in_range = [
                r
                for r in unlinked_rolls
                if start_date
                <= self._get_session_date(user_id, r["session_id"])
                <= end_date
            ]
            detailed_count += len(unlinked_in_range)

            # Count simple-mode mentions by partner name
            simple_count = simple_partner_counts.get(partner["name"].strip().lower(), 0)

            total_rolls = detailed_count + simple_count

            # Aggregate session-level submissions for this partner.
            # Check both sessions.partners JSON (simple mode) AND
            # session_rolls (detailed mode) to find sessions involving
            # this partner.
            all_rolls = rolls_in_range + unlinked_in_range
            roll_session_ids = {r["session_id"] for r in all_rolls}
            sess_subs_for, sess_subs_against = (
                self._get_session_submissions_for_partner(
                    partner["name"], sessions, roll_session_ids
                )
            )
            roll_subs_for = stats.get("total_submissions_for", 0)
            roll_subs_against = stats.get("total_submissions_against", 0)
            final_subs_for = max(roll_subs_for, sess_subs_for)
            final_subs_against = max(roll_subs_against, sess_subs_against)

            partner_matrix.append(
                {
                    "id": partner["id"],
                    "name": partner["name"],
                    "belt_rank": partner.get("belt_rank"),
                    "belt_stripes": partner.get("belt_stripes", 0),
                    "total_rolls": total_rolls,
                    "submissions_for": final_subs_for,
                    "submissions_against": final_subs_against,
                    "sub_ratio": stats.get("sub_ratio", 0),
                    "subs_per_roll_for": stats.get("subs_per_roll", 0),
                    "subs_per_roll_against": stats.get("taps_per_roll", 0),
                }
            )

        # Sort by total rolls
        partner_matrix.sort(key=lambda p: p["total_rolls"], reverse=True)

        # Partner diversity metrics
        active_partners = [p for p in partner_matrix if p["total_rolls"] > 0]
        unique_partners = len(active_partners)
        new_partners = len([p for p in active_partners if p["total_rolls"] <= 3])
        recurring_partners = len([p for p in active_partners if p["total_rolls"] > 3])

        # Top partners summary (top 5)
        top_partners = (
            partner_matrix[:5] if len(partner_matrix) >= 5 else partner_matrix
        )

        # Calculate session distribution by partner
        session_distribution = self._calculate_partner_session_distribution(
            user_id, sessions
        )

        # Overall partner stats
        total_rolls_all_partners = sum(p["total_rolls"] for p in partner_matrix)
        total_subs_for = sum(p["submissions_for"] for p in partner_matrix)
        total_subs_against = sum(p["submissions_against"] for p in partner_matrix)

        return {
            "partner_matrix": partner_matrix,
            "top_partners": top_partners,
            "session_distribution": session_distribution,
            "diversity_metrics": {
                "active_partners": unique_partners,
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
    ) -> dict[str, Any]:
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

    @staticmethod
    def _get_session_submissions_for_partner(
        partner_name: str,
        sessions: list[dict],
        roll_session_ids: set | None = None,
    ) -> tuple[int, int]:
        """Sum session-level submissions for sessions involving a partner.

        Checks two sources to determine if a partner was in a session:
        1. sessions.partners JSON (simple mode)
        2. roll_session_ids from session_rolls table (detailed mode)
        """
        total_for = 0
        total_against = 0
        name_lower = partner_name.strip().lower()
        if roll_session_ids is None:
            roll_session_ids = set()

        for s in sessions:
            subs_for = s.get("submissions_for", 0) or 0
            subs_against = s.get("submissions_against", 0) or 0
            if subs_for == 0 and subs_against == 0:
                continue

            # Check if partner was in this session via partners JSON
            in_session_json = False
            n_partners_json = 0
            partners_raw = s.get("partners")
            if partners_raw:
                try:
                    plist = (
                        json.loads(partners_raw)
                        if isinstance(partners_raw, str)
                        else partners_raw
                    )
                    if isinstance(plist, list):
                        names = [n.strip().lower() for n in plist]
                        n_partners_json = len(names)
                        in_session_json = name_lower in names
                except (json.JSONDecodeError, TypeError):
                    pass

            # Check if partner was in this session via detailed rolls
            in_session_rolls = s.get("id") in roll_session_ids

            if not in_session_json and not in_session_rolls:
                continue

            # Estimate partner count for proportional distribution
            n_partners = max(n_partners_json, 1)
            total_for += subs_for // n_partners
            total_against += subs_against // n_partners
        return total_for, total_against

    def _get_session_date(self, user_id: int, session_id: int) -> date:
        """Helper to get session date."""
        session = self.session_repo.get_by_id(user_id, session_id)
        return session["session_date"] if session else date.today()

    def get_duration_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Average duration trends, duration by class type & gym."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )
        if not sessions:
            return {
                "weekly_avg_duration": [],
                "by_class_type": [],
                "by_gym": [],
                "overall_avg": 0,
            }

        # Weekly average duration
        weekly = defaultdict(list)
        for s in sessions:
            week_key = s["session_date"].strftime("%Y-W%U")
            weekly[week_key].append(s["duration_mins"])

        weekly_avg = [
            {
                "week": k,
                "avg_duration": round(statistics.mean(v), 1),
                "sessions": len(v),
            }
            for k, v in sorted(weekly.items())
        ]

        # Duration by class type
        by_class = defaultdict(list)
        for s in sessions:
            by_class[s["class_type"]].append(s["duration_mins"])

        by_class_type = [
            {
                "class_type": ct,
                "avg_duration": round(statistics.mean(ds), 1),
                "min_duration": min(ds),
                "max_duration": max(ds),
                "sessions": len(ds),
            }
            for ct, ds in by_class.items()
        ]

        # Duration by gym
        by_gym = defaultdict(list)
        for s in sessions:
            by_gym[s["gym_name"]].append(s["duration_mins"])

        by_gym_list = [
            {
                "gym": gym,
                "avg_duration": round(statistics.mean(ds), 1),
                "sessions": len(ds),
            }
            for gym, ds in by_gym.items()
        ]

        overall_avg = round(statistics.mean([s["duration_mins"] for s in sessions]), 1)

        return {
            "weekly_avg_duration": weekly_avg,
            "by_class_type": by_class_type,
            "by_gym": by_gym_list,
            "overall_avg": overall_avg,
        }

    def get_time_of_day_patterns(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Bucket class_time into morning/afternoon/evening with performance."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )

        buckets: dict[str, list[dict]] = {
            "morning": [],
            "afternoon": [],
            "evening": [],
        }

        for s in sessions:
            ct = s.get("class_time") or ""
            if not ct:
                continue
            try:
                hour = int(ct.split(":")[0])
            except (ValueError, IndexError):
                continue

            if hour < 12:
                buckets["morning"].append(s)
            elif hour < 17:
                buckets["afternoon"].append(s)
            else:
                buckets["evening"].append(s)

        patterns = []
        for slot, slot_sessions in buckets.items():
            if not slot_sessions:
                patterns.append(
                    {
                        "time_slot": slot,
                        "sessions": 0,
                        "avg_intensity": 0,
                        "sub_rate": 0,
                        "avg_rolls": 0,
                    }
                )
                continue

            total_for = sum(ss.get("submissions_for", 0) or 0 for ss in slot_sessions)
            total_against = sum(
                ss.get("submissions_against", 0) or 0 for ss in slot_sessions
            )
            sub_rate = (
                round(total_for / total_against, 2)
                if total_against > 0
                else float(total_for)
            )

            patterns.append(
                {
                    "time_slot": slot,
                    "sessions": len(slot_sessions),
                    "avg_intensity": round(
                        statistics.mean(
                            [ss.get("intensity", 0) or 0 for ss in slot_sessions]
                        ),
                        1,
                    ),
                    "sub_rate": sub_rate,
                    "avg_rolls": round(
                        statistics.mean(
                            [ss.get("rolls", 0) or 0 for ss in slot_sessions]
                        ),
                        1,
                    ),
                }
            )

        return {"patterns": patterns}

    def get_gym_comparison(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Sessions, avg intensity, sub rate per gym."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )

        gyms: dict[str, list[dict]] = defaultdict(list)
        for s in sessions:
            gyms[s["gym_name"]].append(s)

        comparison = []
        for gym, gym_sessions in gyms.items():
            total_for = sum(s.get("submissions_for", 0) or 0 for s in gym_sessions)
            total_against = sum(
                s.get("submissions_against", 0) or 0 for s in gym_sessions
            )
            sub_rate = (
                round(total_for / total_against, 2)
                if total_against > 0
                else float(total_for)
            )

            comparison.append(
                {
                    "gym": gym,
                    "sessions": len(gym_sessions),
                    "avg_intensity": round(
                        statistics.mean(
                            [s.get("intensity", 0) or 0 for s in gym_sessions]
                        ),
                        1,
                    ),
                    "sub_rate": sub_rate,
                    "total_rolls": sum(s.get("rolls", 0) or 0 for s in gym_sessions),
                    "avg_duration": round(
                        statistics.mean([s["duration_mins"] for s in gym_sessions]),
                        1,
                    ),
                }
            )

        comparison.sort(key=lambda x: x["sessions"], reverse=True)
        return {"gyms": comparison}

    def get_class_type_effectiveness(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """Sub rate, avg rolls, intensity per class type."""
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(user_id, start_date, end_date)

        by_type: dict[str, list[dict]] = defaultdict(list)
        for s in sessions:
            by_type[s["class_type"]].append(s)

        effectiveness = []
        for ct, ct_sessions in by_type.items():
            total_for = sum(s.get("submissions_for", 0) or 0 for s in ct_sessions)
            total_against = sum(
                s.get("submissions_against", 0) or 0 for s in ct_sessions
            )
            sub_rate = (
                round(total_for / total_against, 2)
                if total_against > 0
                else float(total_for)
            )

            effectiveness.append(
                {
                    "class_type": ct,
                    "sessions": len(ct_sessions),
                    "sub_rate": sub_rate,
                    "avg_rolls": round(
                        statistics.mean([s.get("rolls", 0) or 0 for s in ct_sessions]),
                        1,
                    ),
                    "avg_intensity": round(
                        statistics.mean(
                            [s.get("intensity", 0) or 0 for s in ct_sessions]
                        ),
                        1,
                    ),
                    "total_subs_for": total_for,
                    "total_subs_against": total_against,
                }
            )

        effectiveness.sort(key=lambda x: x["sessions"], reverse=True)
        return {"class_types": effectiveness}

    def get_partner_belt_distribution(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """Partner count by belt rank from friends table."""
        partners = self.friend_repo.list_by_type(user_id, "training-partner")

        belt_counts: Counter = Counter()
        for p in partners:
            belt = p.get("belt_rank") or "unranked"
            belt_counts[belt] += 1

        # Standard belt order
        belt_order = [
            "white",
            "blue",
            "purple",
            "brown",
            "black",
            "unranked",
        ]
        distribution = []
        for belt in belt_order:
            if belt_counts[belt] > 0:
                distribution.append({"belt": belt, "count": belt_counts[belt]})

        # Include any non-standard belts
        for belt, count in belt_counts.items():
            if belt not in belt_order:
                distribution.append({"belt": belt, "count": count})

        return {
            "distribution": distribution,
            "total_partners": len(partners),
        }

    def get_instructor_analytics(
        self,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get instructor insights.

        Args:
            user_id: User ID
            start_date: Start date for filtering (default: 90 days ago)
            end_date: End date for filtering (default: today)
            types: Optional list of class types to filter by (e.g., ["gi", "no-gi"])

        Returns:
            - performance_by_instructor: Metrics for each instructor
            - instructor_styles: Teaching style analysis
        """
        if not start_date:
            start_date = date.today() - timedelta(days=90)
        if not end_date:
            end_date = date.today()

        sessions = self.session_repo.get_by_date_range(
            user_id, start_date, end_date, types=types
        )
        instructors = self.friend_repo.list_by_type(user_id, "instructor")

        performance_by_instructor = []
        for instructor in instructors:
            instructor_sessions = [
                s for s in sessions if s.get("instructor_id") == instructor["id"]
            ]

            if not instructor_sessions:
                continue

            # Calculate metrics
            total_sessions = len(instructor_sessions)
            avg_intensity = statistics.mean(
                [s["intensity"] for s in instructor_sessions]
            )
            total_subs_for = sum(s["submissions_for"] for s in instructor_sessions)
            total_subs_against = sum(
                s["submissions_against"] for s in instructor_sessions
            )

            # Analyze techniques taught
            techniques_taught = Counter()
            for session in instructor_sessions:
                if session.get("techniques"):
                    techniques_taught.update(session["techniques"])

            performance_by_instructor.append(
                {
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
                }
            )

        return {
            "performance_by_instructor": performance_by_instructor,
        }

"""Core performance calculations and partner analytics.

Performance overview, partner analytics, head-to-head, and related helpers.
"""

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


def calculate_period_summary(sessions: list[dict]) -> dict[str, Any]:
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


def calculate_daily_timeseries(
    sessions: list[dict], start_date: date, end_date: date
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


def calculate_partner_session_distribution(
    roll_repo: SessionRollRepository,
    friend_repo: FriendRepository,
    user_id: int,
    sessions: list[dict],
) -> list[dict[str, Any]]:
    """Calculate which partners appear in which sessions."""
    # Get all session IDs
    session_ids = [s["id"] for s in sessions]

    # Get rolls for these sessions
    rolls_by_session = roll_repo.get_by_session_ids(user_id, session_ids)

    # Count sessions per partner
    partner_session_count = defaultdict(int)
    partner_names = {}

    # Build name->id lookup from friends for matching simple partners
    all_partners = friend_repo.list_by_type(user_id, "training-partner")
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


def calculate_performance_by_belt(
    sessions: list[dict], gradings: list[dict]
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
                "subs_against": sum(s["submissions_against"] for s in period_sessions),
            }
        )

    return belt_periods


def get_session_date(
    session_repo: SessionRepository, user_id: int, session_id: int
) -> date:
    """Helper to get session date."""
    session = session_repo.get_by_id(user_id, session_id)
    return session["session_date"] if session else date.today()


def compute_performance_overview(
    session_repo: SessionRepository,
    roll_repo: SessionRollRepository,
    glossary_repo: GlossaryRepository,
    grading_repo: GradingRepository,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
) -> dict[str, Any]:
    """Get performance overview metrics."""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    sessions = session_repo.get_by_date_range(
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
    rolls_by_session = roll_repo.get_by_session_ids(user_id, session_ids)

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
        movement = glossary_repo.get_by_id(movement_id)
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
        movement = glossary_repo.get_by_id(movement_id)
        if movement:
            top_subs_against_list.append(
                {
                    "name": movement["name"],
                    "count": count,
                    "id": movement_id,
                }
            )

    # Performance by belt rank
    gradings = grading_repo.list_all(user_id)
    belt_performance = calculate_performance_by_belt(sessions, gradings)

    # Daily time series for sparklines
    daily_timeseries = calculate_daily_timeseries(sessions, start_date, end_date)

    # Previous period comparison for deltas
    period_length = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date - timedelta(days=1)
    prev_sessions = session_repo.get_by_date_range(user_id, prev_start, prev_end)
    prev_summary = calculate_period_summary(prev_sessions)
    current_summary = calculate_period_summary(sessions)

    # Calculate deltas
    deltas = {
        "sessions": current_summary["total_sessions"] - prev_summary["total_sessions"],
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


def compute_partner_analytics(
    session_repo: SessionRepository,
    roll_repo: SessionRollRepository,
    friend_repo: FriendRepository,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
) -> dict[str, Any]:
    """Get partner analytics data."""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    sessions = session_repo.get_by_date_range(
        user_id, start_date, end_date, types=types
    )

    # Get all partners from contacts (including 'other' type)
    partners = friend_repo.list_by_type(user_id, "training-partner")
    other = friend_repo.list_by_type(user_id, "other")
    seen_ids = {p["id"] for p in partners}
    for o in other:
        if o["id"] not in seen_ids:
            partners.append(o)

    # Pre-compute per-session partner names from JSON
    session_partners_json: dict[int, set[str]] = {}
    for s in sessions:
        names: set[str] = set()
        raw = s.get("partners")
        if raw:
            try:
                plist = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(plist, list):
                    for name in plist:
                        names.add(name.strip().lower())
            except (json.JSONDecodeError, TypeError):
                pass
        session_partners_json[s["id"]] = names

    partner_matrix = []
    for partner in partners:
        stats = roll_repo.get_partner_stats(user_id, partner["id"])
        name_lower = partner["name"].strip().lower()

        # Count detailed rolls in date range (linked by partner_id)
        rolls_in_range = roll_repo.get_by_partner_id(user_id, partner["id"])
        rolls_in_range = [
            r
            for r in rolls_in_range
            if start_date
            <= get_session_date(session_repo, user_id, r["session_id"])
            <= end_date
        ]

        # Also count unlinked rolls (partner_id IS NULL, matched by name)
        unlinked_rolls = roll_repo.list_by_partner_name(user_id, partner["name"])
        unlinked_in_range = [
            r
            for r in unlinked_rolls
            if start_date
            <= get_session_date(session_repo, user_id, r["session_id"])
            <= end_date
        ]

        all_partner_rolls = rolls_in_range + unlinked_in_range
        detailed_count = len(all_partner_rolls)
        detailed_session_ids = {r["session_id"] for r in all_partner_rolls}

        # Simple mode: count sessions with this partner in JSON,
        # EXCLUDING sessions already counted via detailed rolls
        simple_count = 0
        for s in sessions:
            if s["id"] in detailed_session_ids:
                continue  # already counted via session_rolls
            if name_lower in session_partners_json.get(s["id"], set()):
                simple_count += 1

        total_rolls = detailed_count + simple_count

        # Per-partner submissions: count from date-range-filtered rolls only.
        # stats.get("total_submissions_for") is all-time and must NOT be used
        # here — it causes subs from outside the selected period to bleed in.
        roll_subs_for = sum(
            len(r.get("submissions_for") or []) for r in all_partner_rolls
        )
        roll_subs_against = sum(
            len(r.get("submissions_against") or []) for r in all_partner_rolls
        )

        if roll_subs_for > 0 or roll_subs_against > 0:
            subs_for = roll_subs_for
            subs_against = roll_subs_against
        else:
            subs_for = 0
            subs_against = 0
            for s in sessions:
                sid = s["id"]
                in_rolls = sid in detailed_session_ids
                in_json = name_lower in session_partners_json.get(sid, set())
                if not (in_rolls or in_json):
                    continue
                # Count total unique partners in this session
                json_partners = session_partners_json.get(sid, set())
                total_partners_in_session = len(json_partners)
                # If this session only has 1 partner, attribute subs
                if total_partners_in_session <= 1:
                    subs_for += s.get("submissions_for", 0) or 0
                    subs_against += s.get("submissions_against", 0) or 0

        # Compute ratio
        if subs_against > 0:
            ratio = round(subs_for / subs_against, 2)
        elif subs_for > 0:
            ratio = float(subs_for)
        else:
            ratio = 0.0

        partner_matrix.append(
            {
                "id": partner["id"],
                "name": partner["name"],
                "belt_rank": partner.get("belt_rank"),
                "belt_stripes": partner.get("belt_stripes", 0),
                "total_rolls": total_rolls,
                "submissions_for": subs_for,
                "submissions_against": subs_against,
                "sub_ratio": ratio,
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
    top_partners = partner_matrix[:5] if len(partner_matrix) >= 5 else partner_matrix

    # Calculate session distribution by partner
    session_distribution = calculate_partner_session_distribution(
        roll_repo, friend_repo, user_id, sessions
    )

    # Overall stats: rolls from partner matrix, subs from session totals
    total_rolls_all_partners = sum(p["total_rolls"] for p in partner_matrix)
    total_subs_for = sum(s.get("submissions_for", 0) or 0 for s in sessions)
    total_subs_against = sum(s.get("submissions_against", 0) or 0 for s in sessions)

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


def compute_head_to_head(
    roll_repo: SessionRollRepository,
    friend_repo: FriendRepository,
    user_id: int,
    partner1_id: int,
    partner2_id: int,
) -> dict[str, Any]:
    """Get head-to-head comparison between two partners."""
    partner1 = friend_repo.get_by_id(user_id, partner1_id)
    partner2 = friend_repo.get_by_id(user_id, partner2_id)

    if not partner1 or not partner2:
        return {}

    stats1 = roll_repo.get_partner_stats(user_id, partner1_id)
    stats2 = roll_repo.get_partner_stats(user_id, partner2_id)

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

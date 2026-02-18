"""Trend, comparison, and pattern analytics for performance.

Duration analytics, time-of-day patterns, gym comparison,
class type effectiveness, belt distribution, and instructor analytics.
"""

import statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from rivaflow.db.repositories import (
    FriendRepository,
    SessionRepository,
)


def compute_duration_analytics(
    session_repo: SessionRepository,
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

    sessions = session_repo.get_by_date_range(
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


def compute_time_of_day_patterns(
    session_repo: SessionRepository,
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

    sessions = session_repo.get_by_date_range(
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
                    statistics.mean([ss.get("rolls", 0) or 0 for ss in slot_sessions]),
                    1,
                ),
            }
        )

    return {"patterns": patterns}


def compute_gym_comparison(
    session_repo: SessionRepository,
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

    sessions = session_repo.get_by_date_range(
        user_id, start_date, end_date, types=types
    )

    gyms: dict[str, list[dict]] = defaultdict(list)
    for s in sessions:
        gyms[s["gym_name"]].append(s)

    comparison = []
    for gym, gym_sessions in gyms.items():
        total_for = sum(s.get("submissions_for", 0) or 0 for s in gym_sessions)
        total_against = sum(s.get("submissions_against", 0) or 0 for s in gym_sessions)
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
                    statistics.mean([s.get("intensity", 0) or 0 for s in gym_sessions]),
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


def compute_class_type_effectiveness(
    session_repo: SessionRepository,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """Sub rate, avg rolls, intensity per class type."""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    sessions = session_repo.get_by_date_range(user_id, start_date, end_date)

    by_type: dict[str, list[dict]] = defaultdict(list)
    for s in sessions:
        by_type[s["class_type"]].append(s)

    effectiveness = []
    for ct, ct_sessions in by_type.items():
        total_for = sum(s.get("submissions_for", 0) or 0 for s in ct_sessions)
        total_against = sum(s.get("submissions_against", 0) or 0 for s in ct_sessions)
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
                    statistics.mean([s.get("intensity", 0) or 0 for s in ct_sessions]),
                    1,
                ),
                "total_subs_for": total_for,
                "total_subs_against": total_against,
            }
        )

    effectiveness.sort(key=lambda x: x["sessions"], reverse=True)
    return {"class_types": effectiveness}


def compute_partner_belt_distribution(
    friend_repo: FriendRepository,
    user_id: int,
) -> dict[str, Any]:
    """Partner count by belt rank from friends table."""
    partners = friend_repo.list_by_type(user_id, "training-partner")

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


def compute_instructor_analytics(
    session_repo: SessionRepository,
    friend_repo: FriendRepository,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    types: list[str] | None = None,
) -> dict[str, Any]:
    """Get instructor insights."""
    if not start_date:
        start_date = date.today() - timedelta(days=90)
    if not end_date:
        end_date = date.today()

    sessions = session_repo.get_by_date_range(
        user_id, start_date, end_date, types=types
    )
    instructors = friend_repo.list_by_type(user_id, "instructor")

    performance_by_instructor = []
    for instructor in instructors:
        instructor_sessions = [
            s for s in sessions if s.get("instructor_id") == instructor["id"]
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

"""Game Distribution analytics — the 6-axis radar over glossary categories.

Axes mirror movements_glossary categories 1:1 (takedown/pass/sweep/submission/
escape/defense). Three metrics over a window:

- coverage:  distinct movements touched per axis
- frequency: technique touches per axis (per-10-mat-hour rate supplied alongside)
- load:      TRIMP-share attribution — each session's garmin_training_load is
             split across axes by that session's technique-touch shares; sessions
             with HR but no logged techniques stay unattributed and are reported
             as a gap, never guessed.

Radial semantics are DISTRIBUTION (Bevel-style): axis_max is the max across the
six axes for the selected metric (shared with the previous window when present),
so the shape reads "where is my game concentrated", with raw values printed by
the frontend. Touches counted from session_techniques plus roll submissions_for.
"""

import json
from collections import Counter
from datetime import date, timedelta
from typing import Any

from rivaflow.db.repositories import (
    GlossaryRepository,
    SessionRepository,
)
from rivaflow.db.repositories.session_roll_repo import SessionRollRepository
from rivaflow.db.repositories.session_technique_repo import SessionTechniqueRepository

AXES: list[tuple[str, str]] = [
    ("takedown", "Takedowns"),
    ("pass", "Passing"),
    ("sweep", "Sweeps"),
    ("submission", "Submissions"),
    ("escape", "Escapes"),
    ("defense", "Defence"),
]
AXIS_KEYS = {key for key, _ in AXES}
WINDOW_WEEKS = {"8w": 8, "12w": 12}
# Mat exposure counts BJJ time only — S&C/cardio/mobility have no game axes.
BJJ_TYPES = ["gi", "no-gi", "open-mat", "drilling", "competition"]
ALL_TIME_START = date(2000, 1, 1)


class GameDistributionService:
    """Business logic for the Game Distribution radar."""

    def __init__(self):
        self.session_repo = SessionRepository()
        self.glossary_repo = GlossaryRepository()
        self.technique_repo = SessionTechniqueRepository()
        self.roll_repo = SessionRollRepository()

    def get_game_distribution(
        self, user_id: int, window: str = "all"
    ) -> dict[str, Any]:
        end = date.today()
        weeks = WINDOW_WEEKS.get(window)
        if weeks:
            start = end - timedelta(weeks=weeks)
            prev_start = start - timedelta(weeks=weeks)
            prev_end = start - timedelta(days=1)
        else:
            window = "all"
            start, prev_start, prev_end = ALL_TIME_START, None, None

        movement_map = {m["id"]: m for m in self.glossary_repo.list_all()}
        current = self._window_stats(user_id, start, end, movement_map)
        prev = (
            self._window_stats(user_id, prev_start, prev_end, movement_map)
            if prev_start is not None and prev_end is not None
            else None
        )

        axes = []
        axis_max = {
            metric: max(
                [current[metric][key] for key in AXIS_KEYS]
                + ([prev[metric][key] for key in AXIS_KEYS] if prev else [0])
            )
            for metric in ("coverage", "frequency", "load")
        }

        mat_hours = current["mat_hours"]
        for key, label in AXES:
            freq = current["frequency"][key]
            axes.append(
                {
                    "key": key,
                    "label": label,
                    "coverage": {
                        "value": current["coverage"][key],
                        "prev": prev["coverage"][key] if prev else None,
                        "axis_max": axis_max["coverage"],
                    },
                    "frequency": {
                        "value": freq,
                        "per_10h": (
                            round(freq / mat_hours * 10, 1) if mat_hours else 0.0
                        ),
                        "prev": prev["frequency"][key] if prev else None,
                        "axis_max": axis_max["frequency"],
                    },
                    "load": {
                        "value": round(current["load"][key], 1),
                        "prev": round(prev["load"][key], 1) if prev else None,
                        "axis_max": round(axis_max["load"], 1),
                    },
                }
            )

        total_trimp = current["total_trimp"]
        attributed_trimp = sum(current["load"].values())
        return {
            "window": {
                "mode": window,
                "start": start.isoformat() if weeks else None,
                "end": end.isoformat(),
                "prev_start": prev_start.isoformat() if prev_start else None,
                "prev_end": prev_end.isoformat() if prev_end else None,
            },
            "axes": axes,
            "gaps": {
                "sessions_in_window": current["sessions_in_window"],
                "sessions_with_techniques": current["sessions_with_techniques"],
                "load_sessions_with_hr": current["load_sessions_with_hr"],
                "load_unattributed_pct": (
                    round((1 - attributed_trimp / total_trimp) * 100, 1)
                    if total_trimp > 0
                    else None
                ),
                "other_category_touches": current["other_touches"],
            },
            "totals": {
                "mat_hours": round(mat_hours, 1),
                "touches": current["total_touches"],
                "distinct_movements": current["distinct_movements"],
            },
        }

    def _window_stats(
        self,
        user_id: int,
        start: date,
        end: date,
        movement_map: dict[int, dict],
    ) -> dict[str, Any]:
        sessions = self.session_repo.get_by_date_range(
            user_id, start, end, types=BJJ_TYPES
        )
        session_ids = [s["id"] for s in sessions]
        techs_by_session = (
            self.technique_repo.batch_get_by_session_ids(session_ids)
            if session_ids
            else {}
        )
        rolls_by_session = (
            self.roll_repo.get_by_session_ids(user_id, session_ids)
            if session_ids
            else {}
        )

        coverage_sets: dict[str, set[int]] = {key: set() for key in AXIS_KEYS}
        frequency: Counter = Counter({key: 0 for key in AXIS_KEYS})
        load: dict[str, float] = {key: 0.0 for key in AXIS_KEYS}
        other_touches = 0
        total_touches = 0
        distinct_movements: set[int] = set()
        sessions_with_techniques = 0
        load_sessions_with_hr = 0
        total_trimp = 0.0

        for session in sessions:
            per_axis: Counter = Counter()

            for mid in _session_movement_ids(
                techs_by_session.get(session["id"], []),
                rolls_by_session.get(session["id"], []),
            ):
                movement = movement_map.get(mid) if mid else None
                if not movement:
                    continue
                total_touches += 1
                distinct_movements.add(movement["id"])
                category = movement.get("category")
                if category in AXIS_KEYS:
                    per_axis[category] += 1
                    coverage_sets[category].add(movement["id"])
                else:
                    other_touches += 1

            if per_axis:
                sessions_with_techniques += 1
                for category, count in per_axis.items():
                    frequency[category] += count

            trimp = session.get("garmin_training_load")
            if trimp is not None:
                load_sessions_with_hr += 1
                total_trimp += float(trimp)
                axis_total = sum(per_axis.values())
                if axis_total > 0:
                    for category, count in per_axis.items():
                        load[category] += float(trimp) * (count / axis_total)

        return {
            "coverage": {key: len(ids) for key, ids in coverage_sets.items()},
            "frequency": dict(frequency),
            "load": load,
            "mat_hours": sum((s.get("duration_mins") or 0) for s in sessions) / 60.0,
            "sessions_in_window": len(sessions),
            "sessions_with_techniques": sessions_with_techniques,
            "load_sessions_with_hr": load_sessions_with_hr,
            "total_trimp": total_trimp,
            "other_touches": other_touches,
            "total_touches": total_touches,
            "distinct_movements": len(distinct_movements),
        }


def _session_movement_ids(techs: list[dict], rolls: list[dict]) -> list[int]:
    """All movement ids a session touched: logged techniques + roll subs-for."""
    mids = [mid for tech in techs if isinstance(mid := tech.get("movement_id"), int)]
    for roll in rolls:
        mids.extend(_parse_movement_ids(roll.get("submissions_for")))
    return mids


def _parse_movement_ids(raw: Any) -> list[int]:
    """submissions_for/against arrive as JSON arrays of movement ids (TEXT)."""
    if not raw:
        return []
    if isinstance(raw, list):
        return [int(x) for x in raw if isinstance(x, (int, str)) and str(x).isdigit()]
    try:
        parsed = json.loads(raw)
        return [
            int(x) for x in parsed if isinstance(x, (int, str)) and str(x).isdigit()
        ]
    except (ValueError, TypeError):
        return []

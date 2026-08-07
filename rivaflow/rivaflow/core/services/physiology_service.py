"""Physiology analytics — wires the B-series pure cores to live Air data (Wave 2, F13).

The fusion/prescription/load cores (readiness.py, strain_target.py, training_load.py,
sleep_metrics.py) were built unit-tested but unreachable — everything downstream of the dead
whoop_rr feed. This service feeds them from the data RivaFlow actually holds today:
garmin_daily (hub-pushed Air daily biometrics) and sessions.garmin_training_load (per-session
Edwards TRIMP from the Wahoo→GoogleHealth forward link). All the cores' honest availability
gates pass through untouched: no baseline → Building, short load history → ACWR unavailable,
Sunday → Rest.

Scale note: sessions carry EDWARDS TRIMP while cardio_load.scale_to_21's constants were fit on
raw Banister units. Same order of magnitude, and the 0-21 mapping is display-feel rather than
physiology; revisit if the hub ever pushes intraday samples for a true Banister path.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from math import log
from typing import Any
from zoneinfo import ZoneInfo

from rivaflow.core.cardio_load import scale_to_21
from rivaflow.core.readiness import blend_readiness, zscore
from rivaflow.core.sleep_metrics import sleep_debt
from rivaflow.core.strain_target import prescribe_strain
from rivaflow.core.training_load import acwr
from rivaflow.db.repositories import SessionRepository
from rivaflow.db.repositories.garmin_daily_repo import GarminDailyRepository

TZ = ZoneInfo("Australia/Melbourne")
BASELINE_FETCH_DAYS = 45  # daily-biometrics window pulled for baselines
LOAD_WINDOW_DAYS = 28  # chronic-load calendar window (Gabbett)
MIN_CHRONIC_DAYS = 14  # days of load history before we trust a chronic estimate
STALE_SIGNAL_DAYS = (
    2  # a signal whose last reading is older than this is treated as absent
)


class PhysiologyService:
    """Compose readiness, strain target, ACWR and sleep debt from live data."""

    def __init__(
        self,
        garmin_repo: type[GarminDailyRepository] = GarminDailyRepository,
        session_repo: SessionRepository | None = None,
    ):
        self.garmin_repo = garmin_repo
        self.session_repo = session_repo or SessionRepository()

    def get_physiology(self, user_id: int, today: date | None = None) -> dict[str, Any]:
        # The server runs UTC; "today" (and therefore Sunday) is Ruby's Melbourne day.
        today = today or datetime.now(TZ).date()
        is_sabbath = today.weekday() == 6  # Sunday, Ruby's rest day

        rows = self.garmin_repo.get_range(user_id, days=BASELINE_FETCH_DAYS)
        readiness = self._readiness(rows, today, is_sabbath)

        daily_raw = self._daily_load_series(user_id, today)
        acwr_result = (
            acwr(daily_raw)
            if daily_raw
            else {
                "available": False,
                "reason": "No HR-tracked sessions yet — load history starts with the first tracked session.",
            }
        )

        chronic, acute = self._strain_inputs(daily_raw)
        strain = prescribe_strain(readiness.get("state"), chronic, acute)

        sleep_hours = [
            float(r["sleep_hours"]) for r in rows if r.get("sleep_hours") is not None
        ]
        debt = sleep_debt(sleep_hours)

        return {
            "date": today.isoformat(),
            "readiness": readiness,
            "strain_target": strain,
            "acwr": acwr_result,
            "sleep_debt": debt,
        }

    def _readiness(
        self, rows: list[dict], today: date, is_sabbath: bool
    ) -> dict[str, Any]:
        signal_z = {
            # HRV must enter as lnRMSSD — raw RMSSD is right-skewed (Plews/Buchheit).
            "hrv": self._signal_z(rows, "hrv_ms", today, transform=log),
            "rhr": self._signal_z(rows, "rhr", today),
            "sleep": self._signal_z(rows, "sleep_hours", today),
            "resp": self._signal_z(rows, "respiration_rate", today),
        }
        verdict = blend_readiness(signal_z, today_is_sabbath=is_sabbath)
        verdict["source"] = "garmin_daily (Fitbit Air via Google Health)"
        return verdict

    def _signal_z(
        self, rows: list[dict], field: str, today: date, transform=None
    ) -> float | None:
        """z of the latest reading vs its own baseline; None if absent or stale."""
        series: list[tuple[date, float]] = []
        for r in rows:
            value = r.get(field)
            if value is None:
                continue
            raw = float(value)
            if raw <= 0:
                continue
            series.append(
                (_as_date(r["metric_date"]), transform(raw) if transform else raw)
            )
        if not series:
            return None
        last_date = series[-1][0]
        if (today - last_date).days > STALE_SIGNAL_DAYS:
            return None  # honest: a weeks-old reading is not "today"
        result = zscore([v for _, v in series])
        return result["z"] if result else None

    def _daily_load_series(self, user_id: int, today: date) -> list[float]:
        """Calendar daily TRIMP from the first HR-tracked session: rest days are real zeros, not gaps."""
        start = today - timedelta(days=LOAD_WINDOW_DAYS * 2)
        sessions = self.session_repo.get_by_date_range(user_id, start, today)
        by_day: dict[date, float] = {}
        for s in sessions:
            trimp = s.get("garmin_training_load")
            if trimp is None:
                continue
            day = _as_date(s["session_date"])
            by_day[day] = by_day.get(day, 0.0) + float(trimp)
        if not by_day:
            return []
        first = min(by_day)
        return [
            by_day.get(first + timedelta(days=i), 0.0)
            for i in range((today - first).days + 1)
        ]

    def _strain_inputs(
        self, daily_raw: list[float]
    ) -> tuple[float | None, float | None]:
        """(chronic, acute) on the 0-21 scale, or (None, None) while history is too short —
        prescribe_strain then falls back to its neutral DEFAULT_CHRONIC honestly."""
        if len(daily_raw) < MIN_CHRONIC_DAYS:
            return None, None
        window = daily_raw[-LOAD_WINDOW_DAYS:]
        chronic = sum(scale_to_21(raw) for raw in window) / len(window)
        acute = scale_to_21(daily_raw[-1])
        return chronic, acute


def _as_date(value: Any) -> date:
    """metric_date/session_date arrive as date (Postgres) or ISO string (SQLite)."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])

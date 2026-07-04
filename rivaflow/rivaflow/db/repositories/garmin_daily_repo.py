"""Repository for Garmin daily key metrics (one row per user per day).

Populated by the Mac Garmin push job (RivaFlowGarminPush) which reads the
already-synced health.db. Read by the Health-tab daily trend charts.
"""

from __future__ import annotations

from datetime import date, timedelta

from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

# Columns returned to the API (no internal id / user_id / synced_at).
_DAILY_COLS = (
    "metric_date, rhr, hrv_ms, hrv_status, body_battery_high, body_battery_low, "
    "stress_avg, max_stress, sleep_hours, sleep_score, sleep_deep_hours, "
    "sleep_rem_hours, sleep_light_hours, sleep_awake_hours, steps, respiration_rate, "
    "spo2_pct, training_readiness_score, training_readiness_level, training_status, "
    "vo2max, active_calories, intensity_min_moderate, intensity_min_vigorous"
)

# Upsertable metric fields (everything except the keys).
_UPSERT_FIELDS = [
    "rhr",
    "hrv_ms",
    "hrv_status",
    "body_battery_high",
    "body_battery_low",
    "stress_avg",
    "max_stress",
    "sleep_hours",
    "sleep_score",
    "sleep_deep_hours",
    "sleep_rem_hours",
    "sleep_light_hours",
    "sleep_awake_hours",
    "steps",
    "respiration_rate",
    "spo2_pct",
    "training_readiness_score",
    "training_readiness_level",
    "training_status",
    "vo2max",
    "active_calories",
    "intensity_min_moderate",
    "intensity_min_vigorous",
]


class GarminDailyRepository(BaseRepository):
    """Data access for the garmin_daily table."""

    @staticmethod
    def upsert(user_id: int, metric_date: str, **fields) -> None:
        """Insert or update one day's metrics. COALESCE keeps prior non-null
        values when a later payload omits a field."""
        cols = ["user_id", "metric_date"] + _UPSERT_FIELDS
        placeholders = ", ".join(["?"] * len(cols))
        values = [user_id, metric_date] + [fields.get(f) for f in _UPSERT_FIELDS]
        set_clause = ", ".join(
            f"{f} = COALESCE(excluded.{f}, garmin_daily.{f})" for f in _UPSERT_FIELDS
        )
        query = convert_query(
            f"INSERT INTO garmin_daily ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT(user_id, metric_date) DO UPDATE SET {set_clause}"
        )
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))

    @staticmethod
    def get_range(user_id: int, days: int = 30) -> list[dict]:
        """Return daily metrics for the last `days`, oldest first (for trends)."""
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        return BaseRepository._fetchall(
            convert_query(
                f"SELECT {_DAILY_COLS} FROM garmin_daily "
                "WHERE user_id = ? AND metric_date >= ? ORDER BY metric_date ASC"
            ),
            (user_id, cutoff),
        )

    @staticmethod
    def get_latest(user_id: int) -> dict | None:
        """Most recent day of metrics (for the summary cards)."""
        return BaseRepository._fetchone(
            convert_query(
                f"SELECT {_DAILY_COLS} FROM garmin_daily WHERE user_id = ? "
                "ORDER BY metric_date DESC LIMIT 1"
            ),
            (user_id,),
        )

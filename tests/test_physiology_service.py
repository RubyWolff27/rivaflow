"""Unit tests for PhysiologyService — the F13 wiring of the B-series cores to live data.

The pure cores (readiness/strain_target/training_load/sleep_metrics) have their own unit
suites; these tests pin the WIRING: signal extraction, lnRMSSD transform, staleness, the
calendar load series, honest gates, and Sabbath.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

from rivaflow.core.services.physiology_service import PhysiologyService

TODAY = date(2026, 8, 7)  # a Friday
SUNDAY = date(2026, 8, 9)


def _daily_rows(days: int, end: date = TODAY, hrv: float = 40.0, **overrides):
    """Contiguous garmin_daily rows ending at `end`, oldest first (repo contract)."""
    rows = []
    for i in range(days - 1, -1, -1):
        row = {
            "metric_date": (end - timedelta(days=i)).isoformat(),
            "hrv_ms": hrv,
            "rhr": 65,
            "sleep_hours": 7.5,
            "respiration_rate": 14.0,
        }
        row.update(overrides)
        rows.append(row)
    return rows


def _service(rows, sessions):
    garmin_repo = MagicMock()
    garmin_repo.get_range.return_value = rows
    session_repo = MagicMock()
    session_repo.get_by_date_range.return_value = sessions
    return PhysiologyService(garmin_repo=garmin_repo, session_repo=session_repo)


def _sessions_with_load(days: int, end: date = TODAY, trimp: float = 150.0):
    return [
        {
            "session_date": (end - timedelta(days=i)).isoformat(),
            "garmin_training_load": trimp,
        }
        for i in range(days)
    ]


class TestReadinessWiring:
    def test_full_signals_produce_a_verdict(self):
        svc = _service(_daily_rows(14), [])
        result = svc.get_physiology(user_id=4, today=TODAY)

        assert result["readiness"]["state"] in {
            "Prime",
            "Balanced",
            "Strained",
            "Rundown",
        }
        assert "garmin_daily" in result["readiness"]["source"]

    def test_no_hrv_baseline_is_building_not_a_number(self):
        svc = _service(_daily_rows(3), [])  # < MIN_BASELINE_DAYS+1
        result = svc.get_physiology(user_id=4, today=TODAY)

        assert result["readiness"]["state"] == "Building"
        assert result["readiness"]["score"] is None

    def test_hrv_enters_as_ln_rmssd(self):
        """A doubled RMSSD must move z by log-scale, not linear, distance."""
        rows = _daily_rows(14)
        rows[-1]["hrv_ms"] = 80.0  # today doubles vs the flat 40 baseline
        svc = _service(rows, [])
        result = svc.get_physiology(user_id=4, today=TODAY)

        hrv_contrib = next(
            c
            for c in result["readiness"]["basis"]["contributors"]
            if c["signal"] == "hrv"
        )
        # ln(80)-ln(40)=ln(2)≈0.693; the flat baseline makes sd fall back to 1.0,
        # so z should be ~0.69 — a linear implementation would put z on the raw
        # +40ms jump instead and this pin would break.
        assert 0.5 < hrv_contrib["z"] < 0.9

    def test_stale_signal_is_dropped_not_reported_as_today(self):
        rows = _daily_rows(14)
        for r in rows[-5:]:
            r["respiration_rate"] = None  # resp went dark 5 days ago
        svc = _service(rows, [])
        result = svc.get_physiology(user_id=4, today=TODAY)

        signals = {c["signal"] for c in result["readiness"]["basis"]["contributors"]}
        assert "resp" not in signals
        assert "hrv" in signals

    def test_sunday_is_sabbath_rest(self):
        svc = _service(_daily_rows(14, end=SUNDAY), [])
        result = svc.get_physiology(user_id=4, today=SUNDAY)

        assert result["readiness"]["state"] == "Rest"
        assert result["strain_target"]["available"] is False
        assert "Sabbath" in result["strain_target"]["reason"]


class TestLoadWiring:
    def test_daily_series_zero_fills_rest_days(self):
        sessions = [
            {
                "session_date": (TODAY - timedelta(days=4)).isoformat(),
                "garmin_training_load": 100.0,
            },
            {"session_date": TODAY.isoformat(), "garmin_training_load": 200.0},
        ]
        svc = _service(_daily_rows(14), sessions)
        series = svc._daily_load_series(4, TODAY)

        assert series == [100.0, 0.0, 0.0, 0.0, 200.0]

    def test_same_day_sessions_sum(self):
        sessions = [
            {"session_date": TODAY.isoformat(), "garmin_training_load": 100.0},
            {"session_date": TODAY.isoformat(), "garmin_training_load": 50.0},
        ]
        svc = _service(_daily_rows(14), sessions)
        assert svc._daily_load_series(4, TODAY) == [150.0]

    def test_sessions_without_trimp_are_ignored(self):
        sessions = [{"session_date": TODAY.isoformat(), "garmin_training_load": None}]
        svc = _service(_daily_rows(14), sessions)
        assert svc._daily_load_series(4, TODAY) == []

    def test_short_history_gates_acwr_with_reason(self):
        svc = _service(_daily_rows(14), _sessions_with_load(10))
        result = svc.get_physiology(user_id=4, today=TODAY)

        assert result["acwr"]["available"] is False
        assert "reason" in result["acwr"]

    def test_full_history_yields_acwr_ratio(self):
        svc = _service(_daily_rows(14), _sessions_with_load(30))
        result = svc.get_physiology(user_id=4, today=TODAY)

        assert result["acwr"]["available"] is True
        assert result["acwr"]["zone"] == "sweet-spot"  # flat load → ratio 1.0

    def test_no_load_history_at_all(self):
        svc = _service(_daily_rows(14), [])
        result = svc.get_physiology(user_id=4, today=TODAY)

        assert result["acwr"]["available"] is False


class TestStrainWiring:
    def test_short_history_falls_back_to_default_chronic(self):
        svc = _service(_daily_rows(14), _sessions_with_load(5))
        result = svc.get_physiology(user_id=4, today=TODAY)

        st = result["strain_target"]
        if st["available"]:  # state-dependent, but chronic must be the neutral default
            assert st["chronic_load"] == 10.0

    def test_long_history_uses_measured_chronic(self):
        svc = _service(_daily_rows(14), _sessions_with_load(30, trimp=150.0))
        result = svc.get_physiology(user_id=4, today=TODAY)

        st = result["strain_target"]
        assert st["available"] is True
        assert st["chronic_load"] != 10.0
        assert "acute_load" in st


class TestSleepDebtWiring:
    def test_sleep_debt_from_daily_rows(self):
        svc = _service(_daily_rows(14, sleep_hours=7.0), [])
        result = svc.get_physiology(user_id=4, today=TODAY)

        debt = result["sleep_debt"]
        assert debt["available"] is True
        assert debt["need_hours"] == 9.0
        assert debt["debt_hours"] == 14.0  # 7 nights x 2h shortfall

    def test_no_sleep_rows_is_unavailable(self):
        svc = _service(_daily_rows(14, sleep_hours=None), [])
        result = svc.get_physiology(user_id=4, today=TODAY)

        assert result["sleep_debt"]["available"] is False


class TestSpine1HubCanonical:
    """Spine-1: the hub verdict is the ONE readiness number; the blend is basis."""

    def _rows_with_hub(self, score, days=14):
        rows = _daily_rows(days)
        for r in rows:
            r["training_readiness_score"] = score
        return rows

    def test_hub_score_is_canonical(self):
        svc = _service(self._rows_with_hub(70), [])
        r = svc.get_physiology(user_id=4, today=TODAY)["readiness"]

        assert r["score"] == 70
        assert r["band"] == "green"
        assert r["state"] == "Prime"

    def test_hub_band_mapping(self):
        for score, band, state in [
            (66, "green", "Prime"),
            (55, "yellow", "Balanced"),
            (48, "yellow", "Strained"),
            (33, "red", "Rundown"),
        ]:
            svc = _service(self._rows_with_hub(score), [])
            r = svc.get_physiology(user_id=4, today=TODAY)["readiness"]
            assert (r["score"], r["band"], r["state"]) == (score, band, state)

    def test_no_second_composite_score_in_response(self):
        """The blend's 0-100 score must NOT appear — one number only (Spine-1)."""
        svc = _service(self._rows_with_hub(70), [])
        r = svc.get_physiology(user_id=4, today=TODAY)["readiness"]

        assert "score" not in r["basis"]
        assert set(r["basis"].keys()) == {
            "driver",
            "composite_z",
            "contributors",
            "signals_used",
            "caveat",
        }

    def test_stale_hub_score_falls_back_to_blend(self):
        rows = _daily_rows(14)
        for r in rows[:-5]:
            r["training_readiness_score"] = 70  # hub verdict went dark 5 days ago
        svc = _service(rows, [])
        r = svc.get_physiology(user_id=4, today=TODAY)["readiness"]

        assert r["score"] is None
        assert r["band"] is None
        assert r["state"] in {"Prime", "Balanced", "Strained", "Rundown"}

    def test_strain_prescription_follows_hub_state(self):
        svc = _service(self._rows_with_hub(30), _sessions_with_load(30))
        result = svc.get_physiology(user_id=4, today=TODAY)

        assert result["readiness"]["state"] == "Rundown"
        assert result["strain_target"]["available"] is True
        assert result["strain_target"]["capped"] is True

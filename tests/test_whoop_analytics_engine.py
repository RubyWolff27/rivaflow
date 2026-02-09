"""Tests for WhoopAnalyticsEngine sport science analytics."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch


def _make_recovery(
    day_offset=0,
    recovery_score=72,
    hrv_ms=45,
    resting_hr=52,
    sleep_duration_ms=25_920_000,
    rem_sleep_ms=5_961_600,
    slow_wave_ms=4_924_800,
):
    d = date.today() - timedelta(days=day_offset)
    return {
        "recovery_score": recovery_score,
        "hrv_ms": hrv_ms,
        "resting_hr": resting_hr,
        "spo2": 97,
        "sleep_performance": 85,
        "sleep_duration_ms": sleep_duration_ms,
        "rem_sleep_ms": rem_sleep_ms,
        "slow_wave_ms": slow_wave_ms,
        "cycle_start": d.isoformat(),
    }


def _make_session(day_offset=0, subs_for=2, subs_against=1, intensity=3):
    d = date.today() - timedelta(days=day_offset)
    return {
        "id": 100 + day_offset,
        "session_date": d,
        "class_type": "gi",
        "gym_name": "TestGym",
        "duration_mins": 60,
        "intensity": intensity,
        "rolls": 5,
        "submissions_for": subs_for,
        "submissions_against": subs_against,
    }


class TestRecoveryPerformanceCorrelation:
    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_sufficient_data(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        engine.session_repo = MagicMock()

        # Create matching recovery and sessions
        recs = [
            _make_recovery(day_offset=i, recovery_score=70 + i)
            for i in range(10, 0, -1)
        ]
        sessions = [
            _make_session(day_offset=i - 1, subs_for=i) for i in range(10, 0, -1)
        ]

        mock_rec.get_by_date_range.return_value = recs
        engine.session_repo.get_by_date_range.return_value = sessions

        result = engine.get_recovery_performance_correlation(1, days=30)
        assert "r_value" in result
        assert "zones" in result
        assert "scatter" in result

    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_no_data(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        engine.session_repo = MagicMock()

        mock_rec.get_by_date_range.return_value = []
        engine.session_repo.get_by_date_range.return_value = []

        result = engine.get_recovery_performance_correlation(1)
        assert result["r_value"] == 0.0
        assert result["scatter"] == []

    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_zone_bucketing(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        engine.session_repo = MagicMock()

        # Mix of red/yellow/green recoveries
        recs = [
            _make_recovery(day_offset=3, recovery_score=20),
            _make_recovery(day_offset=2, recovery_score=50),
            _make_recovery(day_offset=1, recovery_score=80),
        ]
        sessions = [
            _make_session(day_offset=2, subs_for=1),
            _make_session(day_offset=1, subs_for=2),
            _make_session(day_offset=0, subs_for=4),
        ]

        mock_rec.get_by_date_range.return_value = recs
        engine.session_repo.get_by_date_range.return_value = sessions

        result = engine.get_recovery_performance_correlation(1, days=7)
        assert "red" in result["zones"]
        assert "yellow" in result["zones"]
        assert "green" in result["zones"]


class TestStrainEfficiency:
    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopWorkoutCacheRepository"
    )
    def test_by_class_type(self, mock_wo):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        engine.session_repo = MagicMock()

        sessions = [
            _make_session(day_offset=1, subs_for=3),
            _make_session(day_offset=0, subs_for=1),
        ]
        engine.session_repo.get_by_date_range.return_value = sessions

        mock_wo.get_by_session_id.side_effect = [
            {"strain": 12.0},
            {"strain": 8.0},
        ]

        result = engine.get_strain_efficiency(1, days=7)
        assert result["overall_efficiency"] > 0
        assert "gi" in result["by_class_type"]

    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopWorkoutCacheRepository"
    )
    def test_zero_strain_guard(self, mock_wo):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        engine.session_repo = MagicMock()
        engine.session_repo.get_by_date_range.return_value = [_make_session()]

        mock_wo.get_by_session_id.return_value = {"strain": 0}

        result = engine.get_strain_efficiency(1)
        assert result["overall_efficiency"] == 0


class TestHRVPredictor:
    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_threshold_calculation(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        engine.session_repo = MagicMock()

        recs = [
            _make_recovery(day_offset=i, hrv_ms=30 + i * 5) for i in range(10, 0, -1)
        ]
        sessions = [
            _make_session(day_offset=i, subs_for=i, intensity=3)
            for i in range(10, 0, -1)
        ]

        mock_rec.get_by_date_range.return_value = recs
        engine.session_repo.get_by_date_range.return_value = sessions

        result = engine.get_hrv_performance_predictor(1, days=30)
        assert "hrv_threshold" in result
        assert result["hrv_threshold"] > 0


class TestSleepAnalysis:
    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_rem_correlation(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        engine.session_repo = MagicMock()

        recs = [_make_recovery(day_offset=i) for i in range(10, 0, -1)]
        sessions = [
            _make_session(day_offset=i - 1, subs_for=i) for i in range(10, 0, -1)
        ]

        mock_rec.get_by_date_range.return_value = recs
        engine.session_repo.get_by_date_range.return_value = sessions

        result = engine.get_sleep_performance_analysis(1, days=30)
        assert "rem_r" in result
        assert "sws_r" in result
        assert "total_sleep_r" in result


class TestCardiovascularDrift:
    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_declining_rhr(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()

        # RHR declining over 4 weeks = improving
        recs = []
        for week in range(4):
            for day in range(7):
                offset = (3 - week) * 7 + (6 - day)
                recs.append(
                    _make_recovery(
                        day_offset=offset,
                        resting_hr=60 - week * 3,
                    )
                )

        mock_rec.get_by_date_range.return_value = recs

        result = engine.get_cardiovascular_drift(1, days=30)
        assert result["trend"] == "improving"
        assert result["slope"] < 0

    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_rising_rhr(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()

        # RHR rising over 4 weeks = fatigue
        recs = []
        for week in range(4):
            for day in range(7):
                offset = (3 - week) * 7 + (6 - day)
                recs.append(
                    _make_recovery(
                        day_offset=offset,
                        resting_hr=50 + week * 3,
                    )
                )

        mock_rec.get_by_date_range.return_value = recs

        result = engine.get_cardiovascular_drift(1, days=30)
        assert result["trend"] == "rising"
        assert result["slope"] > 0

    @patch(
        "rivaflow.core.services.whoop_analytics_engine" ".WhoopRecoveryCacheRepository"
    )
    def test_insufficient_data(self, mock_rec):
        from rivaflow.core.services.whoop_analytics_engine import (
            WhoopAnalyticsEngine,
        )

        engine = WhoopAnalyticsEngine()
        mock_rec.get_by_date_range.return_value = []

        result = engine.get_cardiovascular_drift(1)
        assert result["trend"] == "insufficient_data"

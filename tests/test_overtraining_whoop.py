"""Tests for enhanced 6-factor overtraining risk with WHOOP biometrics."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch


def _make_readiness(day_offset=0, composite_score=14, hotspot_note=None):
    return {
        "check_date": date.today() - timedelta(days=day_offset),
        "composite_score": composite_score,
        "hotspot_note": hotspot_note,
    }


def _make_session(day_offset=0, intensity=3):
    return {
        "id": 100 + day_offset,
        "session_date": date.today() - timedelta(days=day_offset),
        "intensity": intensity,
        "duration_mins": 60,
        "rolls": 5,
        "submissions_for": 1,
        "submissions_against": 1,
        "class_type": "gi",
        "gym_name": "TestGym",
    }


def _make_recovery(day_offset=0, recovery_score=72, hrv_ms=45):
    return {
        "recovery_score": recovery_score,
        "hrv_ms": hrv_ms,
        "cycle_start": (date.today() - timedelta(days=day_offset)).isoformat(),
    }


@patch(
    "rivaflow.db.repositories.whoop_recovery_cache_repo" ".WhoopRecoveryCacheRepository"
)
@patch("rivaflow.db.repositories.whoop_connection_repo" ".WhoopConnectionRepository")
def test_hrv_decline_factor_max(mock_conn, mock_rec):
    """Declining HRV over 14 days yields max 15 points."""
    from rivaflow.core.services.insights_analytics import (
        InsightsAnalyticsService,
    )

    svc = InsightsAnalyticsService()
    svc.readiness_repo = MagicMock()
    svc.readiness_repo.get_by_date_range.return_value = [
        _make_readiness(i) for i in range(14)
    ]
    svc.session_repo = MagicMock()
    svc.session_repo.get_by_date_range.return_value = [
        _make_session(i) for i in range(10)
    ]

    mock_conn.get_by_user_id.return_value = {"is_active": True}
    # HRV steeply declining: 60, 57, 54, ... (slope ~ -2.1)
    declining_hrv = [
        _make_recovery(day_offset=13 - i, hrv_ms=60 - i * 3) for i in range(14)
    ]
    mock_rec.get_by_date_range.return_value = declining_hrv

    # Mock training load to avoid DB calls
    svc.get_training_load_management = MagicMock(
        return_value={"current_acwr": 1.0, "current_zone": "sweet_spot"}
    )

    result = svc.get_overtraining_risk(1)
    assert result["factors"]["hrv_decline"]["score"] == 15
    assert result["factors"]["hrv_decline"]["max"] == 15


@patch("rivaflow.db.repositories.whoop_connection_repo" ".WhoopConnectionRepository")
def test_hrv_decline_no_whoop(mock_conn):
    """No WHOOP data → hrv_decline and recovery_decline both 0."""
    from rivaflow.core.services.insights_analytics import (
        InsightsAnalyticsService,
    )

    svc = InsightsAnalyticsService()
    svc.readiness_repo = MagicMock()
    svc.readiness_repo.get_by_date_range.return_value = [
        _make_readiness(i) for i in range(14)
    ]
    svc.session_repo = MagicMock()
    svc.session_repo.get_by_date_range.return_value = [
        _make_session(i) for i in range(10)
    ]

    mock_conn.get_by_user_id.return_value = None

    svc.get_training_load_management = MagicMock(
        return_value={"current_acwr": 1.0, "current_zone": "sweet_spot"}
    )

    result = svc.get_overtraining_risk(1)
    assert result["factors"]["hrv_decline"]["score"] == 0
    assert result["factors"]["recovery_decline"]["score"] == 0


@patch(
    "rivaflow.db.repositories.whoop_recovery_cache_repo" ".WhoopRecoveryCacheRepository"
)
@patch("rivaflow.db.repositories.whoop_connection_repo" ".WhoopConnectionRepository")
def test_recovery_decline_consecutive_red(mock_conn, mock_rec):
    """3+ consecutive red recovery days → 15 points."""
    from rivaflow.core.services.insights_analytics import (
        InsightsAnalyticsService,
    )

    svc = InsightsAnalyticsService()
    svc.readiness_repo = MagicMock()
    svc.readiness_repo.get_by_date_range.return_value = [
        _make_readiness(i) for i in range(14)
    ]
    svc.session_repo = MagicMock()
    svc.session_repo.get_by_date_range.return_value = [
        _make_session(i) for i in range(10)
    ]

    mock_conn.get_by_user_id.return_value = {"is_active": True}
    # 3 consecutive red days (<34%), rest normal
    recs = [
        _make_recovery(day_offset=13 - i, recovery_score=70, hrv_ms=50)
        for i in range(11)
    ] + [
        _make_recovery(day_offset=2, recovery_score=25, hrv_ms=50),
        _make_recovery(day_offset=1, recovery_score=20, hrv_ms=50),
        _make_recovery(day_offset=0, recovery_score=30, hrv_ms=50),
    ]
    mock_rec.get_by_date_range.return_value = recs

    svc.get_training_load_management = MagicMock(
        return_value={"current_acwr": 1.0, "current_zone": "sweet_spot"}
    )

    result = svc.get_overtraining_risk(1)
    assert result["factors"]["recovery_decline"]["score"] == 15


@patch("rivaflow.db.repositories.whoop_connection_repo" ".WhoopConnectionRepository")
def test_six_factors_returned(mock_conn):
    """Verify 6 factor keys are present in response."""
    from rivaflow.core.services.insights_analytics import (
        InsightsAnalyticsService,
    )

    svc = InsightsAnalyticsService()
    svc.readiness_repo = MagicMock()
    svc.readiness_repo.get_by_date_range.return_value = []
    svc.session_repo = MagicMock()
    svc.session_repo.get_by_date_range.return_value = []

    mock_conn.get_by_user_id.return_value = None

    svc.get_training_load_management = MagicMock(
        return_value={"current_acwr": 1.0, "current_zone": "sweet_spot"}
    )

    result = svc.get_overtraining_risk(1)
    expected_keys = {
        "acwr_spike",
        "readiness_decline",
        "hotspot_mentions",
        "intensity_creep",
        "hrv_decline",
        "recovery_decline",
    }
    assert set(result["factors"].keys()) == expected_keys


@patch("rivaflow.db.repositories.whoop_connection_repo" ".WhoopConnectionRepository")
def test_all_factors_sum_to_100(mock_conn):
    """Max scores across all 6 factors total 100."""
    from rivaflow.core.services.insights_analytics import (
        InsightsAnalyticsService,
    )

    svc = InsightsAnalyticsService()
    svc.readiness_repo = MagicMock()
    svc.readiness_repo.get_by_date_range.return_value = []
    svc.session_repo = MagicMock()
    svc.session_repo.get_by_date_range.return_value = []

    mock_conn.get_by_user_id.return_value = None

    svc.get_training_load_management = MagicMock(
        return_value={"current_acwr": 1.0, "current_zone": "sweet_spot"}
    )

    result = svc.get_overtraining_risk(1)
    total_max = sum(f["max"] for f in result["factors"].values())
    assert total_max == 100

"""Tests for FightDynamicsService — attack/defence heatmap and insights."""

from datetime import date, timedelta

from rivaflow.core.services.fight_dynamics_service import (
    FightDynamicsService,
)
from rivaflow.db.repositories.session_repo import SessionRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_fight_session(
    user_id,
    session_date,
    attacks_attempted=0,
    attacks_successful=0,
    defenses_attempted=0,
    defenses_successful=0,
):
    """Create a session with fight dynamics data."""
    return SessionRepository.create(
        user_id=user_id,
        session_date=session_date,
        class_type="gi",
        gym_name="Test Gym",
        attacks_attempted=attacks_attempted,
        attacks_successful=attacks_successful,
        defenses_attempted=defenses_attempted,
        defenses_successful=defenses_successful,
    )


# ---------------------------------------------------------------------------
# _calc_rate
# ---------------------------------------------------------------------------


def test_calc_rate_normal():
    """_calc_rate calculates percentage correctly."""
    assert FightDynamicsService._calc_rate(3, 10) == 30.0


def test_calc_rate_zero_attempted():
    """_calc_rate returns 0.0 when attempted is zero."""
    assert FightDynamicsService._calc_rate(0, 0) == 0.0


def test_calc_rate_perfect():
    """_calc_rate returns 100.0 when all attempts succeed."""
    assert FightDynamicsService._calc_rate(5, 5) == 100.0


# ---------------------------------------------------------------------------
# _detect_imbalance
# ---------------------------------------------------------------------------


def test_detect_imbalance_balanced():
    """Balanced training is detected correctly."""
    result = FightDynamicsService._detect_imbalance(
        attacks_attempted=10,
        defenses_attempted=10,
        attack_rate=50.0,
        defense_rate=50.0,
    )
    assert result["detected"] is False
    assert result["type"] == "balanced"


def test_detect_imbalance_attack_heavy():
    """Attack-heavy imbalance is detected (>70% attacks)."""
    result = FightDynamicsService._detect_imbalance(
        attacks_attempted=80,
        defenses_attempted=20,
        attack_rate=50.0,
        defense_rate=50.0,
    )
    assert result["detected"] is True
    assert result["type"] == "attack_heavy"


def test_detect_imbalance_defense_heavy():
    """Defense-heavy imbalance is detected (>70% defenses)."""
    result = FightDynamicsService._detect_imbalance(
        attacks_attempted=20,
        defenses_attempted=80,
        attack_rate=50.0,
        defense_rate=50.0,
    )
    assert result["detected"] is True
    assert result["type"] == "defense_heavy"


def test_detect_imbalance_rate_difference():
    """Rate imbalance is detected when success rates differ by >25%."""
    result = FightDynamicsService._detect_imbalance(
        attacks_attempted=50,
        defenses_attempted=50,
        attack_rate=30.0,
        defense_rate=70.0,
    )
    assert result["detected"] is True
    assert "rate_imbalance" in result["type"]


def test_detect_imbalance_no_data():
    """No data returns not detected with type 'none'."""
    result = FightDynamicsService._detect_imbalance(
        attacks_attempted=0,
        defenses_attempted=0,
        attack_rate=0.0,
        defense_rate=0.0,
    )
    assert result["detected"] is False
    assert result["type"] == "none"


# ---------------------------------------------------------------------------
# _determine_trend
# ---------------------------------------------------------------------------


def test_determine_trend_increasing():
    """Volume increasing >10% is labelled 'increasing'."""
    result = FightDynamicsService._determine_trend(
        recent_attempted=20,
        previous_attempted=10,
        recent_rate=60.0,
        previous_rate=55.0,
    )
    assert result["volume_change"] == "increasing"


def test_determine_trend_decreasing():
    """Volume decreasing >10% is labelled 'decreasing'."""
    result = FightDynamicsService._determine_trend(
        recent_attempted=5,
        previous_attempted=15,
        recent_rate=50.0,
        previous_rate=50.0,
    )
    assert result["volume_change"] == "decreasing"


def test_determine_trend_stable():
    """Volume within 10% is labelled 'stable'."""
    result = FightDynamicsService._determine_trend(
        recent_attempted=10,
        previous_attempted=10,
        recent_rate=50.0,
        previous_rate=50.0,
    )
    assert result["volume_change"] == "stable"
    assert result["rate_direction"] == "stable"


def test_determine_trend_rate_improving():
    """Rate improving >5% is labelled 'improving'."""
    result = FightDynamicsService._determine_trend(
        recent_attempted=10,
        previous_attempted=10,
        recent_rate=60.0,
        previous_rate=40.0,
    )
    assert result["rate_direction"] == "improving"


def test_determine_trend_rate_declining():
    """Rate declining >5% is labelled 'declining'."""
    result = FightDynamicsService._determine_trend(
        recent_attempted=10,
        previous_attempted=10,
        recent_rate=40.0,
        previous_rate=60.0,
    )
    assert result["rate_direction"] == "declining"


def test_determine_trend_from_zero():
    """Going from zero to non-zero is 'increasing' at 100%."""
    result = FightDynamicsService._determine_trend(
        recent_attempted=5,
        previous_attempted=0,
        recent_rate=50.0,
        previous_rate=0.0,
    )
    assert result["volume_change"] == "increasing"
    assert result["volume_change_pct"] == 100.0


# ---------------------------------------------------------------------------
# _suggest_focus
# ---------------------------------------------------------------------------


def test_suggest_focus_low_attack_rate():
    """Low attack success rate triggers high-priority suggestion."""
    off_trend = {
        "volume_change": "stable",
        "rate_direction": "stable",
    }
    def_trend = {
        "volume_change": "stable",
        "rate_direction": "stable",
    }
    result = FightDynamicsService._suggest_focus(
        attack_rate=30.0,
        defense_rate=60.0,
        attacks_attempted=10,
        defenses_attempted=10,
        offensive_trend=off_trend,
        defensive_trend=def_trend,
    )
    areas = [s["area"] for s in result["all_suggestions"]]
    assert "attack_accuracy" in areas
    assert result["primary_focus"]["priority"] == "high"


def test_suggest_focus_balanced():
    """Balanced metrics produce a 'maintain' suggestion."""
    off_trend = {
        "volume_change": "stable",
        "rate_direction": "stable",
    }
    def_trend = {
        "volume_change": "stable",
        "rate_direction": "stable",
    }
    result = FightDynamicsService._suggest_focus(
        attack_rate=60.0,
        defense_rate=60.0,
        attacks_attempted=10,
        defenses_attempted=10,
        offensive_trend=off_trend,
        defensive_trend=def_trend,
    )
    assert result["primary_focus"]["area"] == "maintain"


# ---------------------------------------------------------------------------
# get_heatmap_data (weekly)
# ---------------------------------------------------------------------------


def test_heatmap_weekly_empty(temp_db, test_user):
    """Weekly heatmap with no sessions returns empty buckets."""
    svc = FightDynamicsService()
    data = svc.get_heatmap_data(test_user["id"], view="weekly", weeks=4)

    assert isinstance(data, list)
    assert len(data) == 4
    for bucket in data:
        assert bucket["session_count"] == 0
        assert bucket["attacks_attempted"] == 0


def test_heatmap_weekly_with_sessions(temp_db, test_user):
    """Weekly heatmap aggregates session data into correct buckets."""
    svc = FightDynamicsService()
    today = date.today()

    # Create sessions in the current week
    _create_fight_session(
        user_id=test_user["id"],
        session_date=today,
        attacks_attempted=5,
        attacks_successful=3,
        defenses_attempted=4,
        defenses_successful=2,
    )
    _create_fight_session(
        user_id=test_user["id"],
        session_date=today,
        attacks_attempted=3,
        attacks_successful=1,
        defenses_attempted=6,
        defenses_successful=4,
    )

    data = svc.get_heatmap_data(test_user["id"], view="weekly", weeks=4)

    # Find the bucket that has data
    filled = [b for b in data if b["session_count"] > 0]
    assert len(filled) >= 1
    bucket = filled[0]
    assert bucket["attacks_attempted"] == 8
    assert bucket["attacks_successful"] == 4
    assert bucket["defenses_attempted"] == 10
    assert bucket["defenses_successful"] == 6
    assert bucket["session_count"] == 2


# ---------------------------------------------------------------------------
# get_heatmap_data (monthly)
# ---------------------------------------------------------------------------


def test_heatmap_monthly_empty(temp_db, test_user):
    """Monthly heatmap with no sessions returns empty buckets."""
    svc = FightDynamicsService()
    data = svc.get_heatmap_data(test_user["id"], view="monthly", months=3)

    assert isinstance(data, list)
    assert len(data) == 3
    for bucket in data:
        assert bucket["session_count"] == 0


def test_heatmap_monthly_with_sessions(temp_db, test_user):
    """Monthly heatmap aggregates session data correctly."""
    svc = FightDynamicsService()
    today = date.today()

    _create_fight_session(
        user_id=test_user["id"],
        session_date=today,
        attacks_attempted=10,
        attacks_successful=7,
        defenses_attempted=8,
        defenses_successful=5,
    )

    data = svc.get_heatmap_data(test_user["id"], view="monthly", months=3)

    filled = [b for b in data if b["session_count"] > 0]
    assert len(filled) == 1
    assert filled[0]["attacks_attempted"] == 10


# ---------------------------------------------------------------------------
# get_insights
# ---------------------------------------------------------------------------


def test_insights_insufficient_data(temp_db, test_user):
    """Insights with fewer than 3 sessions reports insufficient data."""
    svc = FightDynamicsService()
    result = svc.get_insights(test_user["id"])

    assert result["has_sufficient_data"] is False
    assert result["sessions_needed"] == 3


def test_insights_with_sufficient_data(temp_db, test_user):
    """Insights with enough sessions generates analysis."""
    svc = FightDynamicsService()
    today = date.today()

    # Create 4 sessions in the recent period (last 4 weeks)
    for i in range(4):
        _create_fight_session(
            user_id=test_user["id"],
            session_date=today - timedelta(days=i * 5),
            attacks_attempted=10,
            attacks_successful=6,
            defenses_attempted=8,
            defenses_successful=5,
        )

    result = svc.get_insights(test_user["id"])

    assert result["has_sufficient_data"] is True
    assert result["sessions_with_data"] >= 3
    assert "offensive_trend" in result
    assert "defensive_trend" in result
    assert "attack_success_rate" in result
    assert "defense_success_rate" in result
    assert "imbalance_detection" in result
    assert "suggested_focus" in result
    assert "recent_period" in result
    assert "previous_period" in result


def test_insights_attack_heavy(temp_db, test_user):
    """Insights detects attack-heavy imbalance."""
    svc = FightDynamicsService()
    today = date.today()

    # Create sessions with heavy attack bias
    for i in range(4):
        _create_fight_session(
            user_id=test_user["id"],
            session_date=today - timedelta(days=i * 3),
            attacks_attempted=20,
            attacks_successful=10,
            defenses_attempted=2,
            defenses_successful=1,
        )

    result = svc.get_insights(test_user["id"])

    assert result["has_sufficient_data"] is True
    imbalance = result["imbalance_detection"]
    assert imbalance["detected"] is True
    assert imbalance["type"] == "attack_heavy"

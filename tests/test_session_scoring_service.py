"""Tests for SessionScoringService -- session performance scoring."""

from datetime import date, timedelta

from rivaflow.core.services.session_scoring_service import (
    SCORE_VERSION,
    SessionScoringService,
    _tier_label,
)
from rivaflow.db.repositories.readiness_repo import ReadinessRepository
from rivaflow.db.repositories.session_repo import SessionRepository

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #


def _create_session(user_id, **kwargs):
    """Create a session and return its ID."""
    defaults = {
        "user_id": user_id,
        "session_date": date(2025, 1, 20),
        "class_type": "gi",
        "gym_name": "Test Gym",
        "duration_mins": 60,
        "intensity": 4,
        "rolls": 5,
        "submissions_for": 2,
        "submissions_against": 1,
    }
    defaults.update(kwargs)
    return SessionRepository().create(**defaults)


def _create_readiness(user_id, check_date, **kwargs):
    """Create a readiness entry for scoring alignment tests."""
    defaults = {
        "user_id": user_id,
        "check_date": check_date,
        "sleep": 4,
        "stress": 3,
        "soreness": 3,
        "energy": 4,
    }
    defaults.update(kwargs)
    return ReadinessRepository().upsert(**defaults)


# ------------------------------------------------------------------ #
# Basic scoring
# ------------------------------------------------------------------ #


def test_score_session_basic(temp_db, test_user):
    """score_session returns a score between 0 and 100."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"])

    result = svc.score_session(test_user["id"], sid)

    assert result is not None
    assert 0 <= result["total"] <= 100
    assert result["version"] == SCORE_VERSION


def test_score_session_returns_none_for_missing(temp_db, test_user):
    """score_session returns None for a non-existent session."""
    svc = SessionScoringService()
    result = svc.score_session(test_user["id"], 999999)
    assert result is None


def test_score_session_breakdown_keys(temp_db, test_user):
    """Score breakdown contains expected top-level keys."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"])

    result = svc.score_session(test_user["id"], sid)

    assert "total" in result
    assert "label" in result
    assert "pillars" in result
    assert "rubric" in result
    assert "data_completeness" in result
    assert "version" in result


def test_score_session_bjj_pillars(temp_db, test_user):
    """BJJ session score has effort, engagement, effectiveness pillars."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"], class_type="gi", rolls=5)

    result = svc.score_session(test_user["id"], sid)
    assert result["rubric"] == "bjj"

    pillars = result["pillars"]
    assert "effort" in pillars
    assert "engagement" in pillars
    assert "effectiveness" in pillars

    # Each pillar has score, max, pct
    for name, pillar in pillars.items():
        assert "score" in pillar
        assert "max" in pillar
        assert "pct" in pillar
        assert pillar["score"] <= pillar["max"]


def test_score_session_nogi(temp_db, test_user):
    """No-gi sessions also use the BJJ rubric."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"], class_type="no-gi")

    result = svc.score_session(test_user["id"], sid)
    assert result["rubric"] == "bjj"


def test_score_session_competition(temp_db, test_user):
    """Competition sessions use the competition rubric."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"], class_type="competition")

    result = svc.score_session(test_user["id"], sid)
    assert result["rubric"] == "competition"


def test_score_session_supplementary(temp_db, test_user):
    """S&C sessions use the supplementary rubric."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"], class_type="strength_conditioning")

    result = svc.score_session(test_user["id"], sid)
    assert result["rubric"] == "supplementary"

    pillars = result["pillars"]
    assert "effort" in pillars
    assert "consistency" in pillars


# ------------------------------------------------------------------ #
# Scoring respects inputs
# ------------------------------------------------------------------ #


def test_higher_intensity_higher_effort(temp_db, test_user):
    """Higher intensity should produce a higher effort pillar score."""
    svc = SessionScoringService()

    low_sid = _create_session(
        test_user["id"],
        intensity=1,
        duration_mins=60,
        session_date=date(2025, 1, 20),
    )
    high_sid = _create_session(
        test_user["id"],
        intensity=5,
        duration_mins=60,
        session_date=date(2025, 1, 21),
    )

    low_result = svc.score_session(test_user["id"], low_sid)
    high_result = svc.score_session(test_user["id"], high_sid)

    low_effort = low_result["pillars"]["effort"]["score"]
    high_effort = high_result["pillars"]["effort"]["score"]
    assert high_effort > low_effort


def test_more_rolls_higher_engagement(temp_db, test_user):
    """More rolls should increase the engagement pillar score."""
    svc = SessionScoringService()

    few_sid = _create_session(
        test_user["id"],
        rolls=1,
        session_date=date(2025, 1, 20),
    )
    many_sid = _create_session(
        test_user["id"],
        rolls=10,
        session_date=date(2025, 1, 21),
    )

    few_result = svc.score_session(test_user["id"], few_sid)
    many_result = svc.score_session(test_user["id"], many_sid)

    few_eng = few_result["pillars"]["engagement"]["score"]
    many_eng = many_result["pillars"]["engagement"]["score"]
    assert many_eng > few_eng


def test_submissions_affect_effectiveness(temp_db, test_user):
    """Better sub ratio yields higher effectiveness pillar score."""
    svc = SessionScoringService()

    # Session with poor sub ratio
    poor_sid = _create_session(
        test_user["id"],
        submissions_for=0,
        submissions_against=5,
        session_date=date(2025, 1, 20),
    )
    # Session with great sub ratio
    great_sid = _create_session(
        test_user["id"],
        submissions_for=5,
        submissions_against=0,
        session_date=date(2025, 1, 21),
    )

    poor = svc.score_session(test_user["id"], poor_sid)
    great = svc.score_session(test_user["id"], great_sid)

    poor_eff = poor["pillars"]["effectiveness"]["score"]
    great_eff = great["pillars"]["effectiveness"]["score"]
    assert great_eff > poor_eff


def test_longer_duration_higher_effort(temp_db, test_user):
    """Longer sessions contribute more to the effort score."""
    svc = SessionScoringService()

    short_sid = _create_session(
        test_user["id"],
        duration_mins=30,
        intensity=3,
        session_date=date(2025, 1, 20),
    )
    long_sid = _create_session(
        test_user["id"],
        duration_mins=120,
        intensity=3,
        session_date=date(2025, 1, 21),
    )

    short_result = svc.score_session(test_user["id"], short_sid)
    long_result = svc.score_session(test_user["id"], long_sid)

    short_effort = short_result["pillars"]["effort"]["score"]
    long_effort = long_result["pillars"]["effort"]["score"]
    assert long_effort > short_effort


# ------------------------------------------------------------------ #
# Readiness alignment
# ------------------------------------------------------------------ #


def test_readiness_alignment_included(temp_db, test_user):
    """Readiness alignment pillar appears when readiness data exists."""
    svc = SessionScoringService()

    session_date = date(2025, 1, 20)
    _create_readiness(test_user["id"], session_date)
    sid = _create_session(test_user["id"], session_date=session_date)

    result = svc.score_session(test_user["id"], sid)
    assert "readiness_alignment" in result["pillars"]


def test_readiness_alignment_absent_without_data(temp_db, test_user):
    """Readiness alignment pillar absent without readiness entry."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"])

    result = svc.score_session(test_user["id"], sid)
    assert "readiness_alignment" not in result["pillars"]


def test_readiness_alignment_smart_training(temp_db, test_user):
    """High recovery + high intensity = high alignment score."""
    svc = SessionScoringService()

    session_date = date(2025, 1, 20)
    # High recovery readiness (sleep=5, stress=1, soreness=1, energy=5)
    # composite = 5 + (6-1) + (6-1) + 5 = 20
    _create_readiness(
        test_user["id"],
        session_date,
        sleep=5,
        stress=1,
        soreness=1,
        energy=5,
    )
    sid = _create_session(
        test_user["id"],
        session_date=session_date,
        intensity=5,
    )

    result = svc.score_session(test_user["id"], sid)
    alignment = result["pillars"]["readiness_alignment"]
    # green zone + high effort = 100% alignment
    assert alignment["pct"] == 100


# ------------------------------------------------------------------ #
# Score persistence
# ------------------------------------------------------------------ #


def test_score_is_persisted(temp_db, test_user):
    """score_session writes score, breakdown, and version to the session."""
    svc = SessionScoringService()
    repo = SessionRepository()

    sid = _create_session(test_user["id"])
    result = svc.score_session(test_user["id"], sid)

    # Re-fetch the session to verify persistence
    session = repo.get_by_id(test_user["id"], sid)
    assert session is not None
    assert float(session["session_score"]) == result["total"]
    assert session["score_version"] == SCORE_VERSION


def test_recalculate_session(temp_db, test_user):
    """recalculate_session recomputes and updates the score."""
    svc = SessionScoringService()
    repo = SessionRepository()

    sid = _create_session(test_user["id"], intensity=2, rolls=2)
    svc.score_session(test_user["id"], sid)

    # Update the session to be higher intensity
    repo.update(
        user_id=test_user["id"],
        session_id=sid,
        intensity=5,
        rolls=10,
    )

    result2 = svc.recalculate_session(test_user["id"], sid)
    assert result2 is not None

    session = repo.get_by_id(test_user["id"], sid)
    assert float(session["session_score"]) == result2["total"]


# ------------------------------------------------------------------ #
# backfill_user_scores
# ------------------------------------------------------------------ #


def test_backfill_user_scores(temp_db, test_user):
    """backfill_user_scores scores all unscored sessions."""
    svc = SessionScoringService()

    # Create 3 sessions (all unscored)
    for i in range(3):
        _create_session(
            test_user["id"],
            session_date=date(2025, 1, 20) + timedelta(days=i),
        )

    summary = svc.backfill_user_scores(test_user["id"])
    assert summary["scored"] == 3
    assert summary["skipped"] == 0
    assert summary["total"] == 3


def test_backfill_skips_already_scored(temp_db, test_user):
    """backfill_user_scores skips sessions that already have scores."""
    svc = SessionScoringService()

    sid1 = _create_session(test_user["id"], session_date=date(2025, 1, 20))
    _create_session(test_user["id"], session_date=date(2025, 1, 21))

    # Score the first session
    svc.score_session(test_user["id"], sid1)

    summary = svc.backfill_user_scores(test_user["id"])
    assert summary["scored"] == 1
    assert summary["skipped"] == 1
    assert summary["total"] == 2


# ------------------------------------------------------------------ #
# Tier labels
# ------------------------------------------------------------------ #


def test_tier_label_peak():
    """Score >= 85 is labeled Peak."""
    assert _tier_label(90) == "Peak"
    assert _tier_label(85) == "Peak"


def test_tier_label_excellent():
    """Score 70-84 is labeled Excellent."""
    assert _tier_label(75) == "Excellent"
    assert _tier_label(70) == "Excellent"


def test_tier_label_strong():
    """Score 50-69 is labeled Strong."""
    assert _tier_label(60) == "Strong"
    assert _tier_label(50) == "Strong"


def test_tier_label_solid():
    """Score 30-49 is labeled Solid."""
    assert _tier_label(40) == "Solid"
    assert _tier_label(30) == "Solid"


def test_tier_label_light():
    """Score < 30 is labeled Light."""
    assert _tier_label(20) == "Light"
    assert _tier_label(0) == "Light"


# ------------------------------------------------------------------ #
# Data completeness
# ------------------------------------------------------------------ #


def test_data_completeness_without_optional(temp_db, test_user):
    """Data completeness < 1.0 when readiness and WHOOP are missing."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"])

    result = svc.score_session(test_user["id"], sid)
    # Without readiness or WHOOP, only 3/5 pillars for BJJ
    assert result["data_completeness"] < 1.0


def test_data_completeness_with_readiness(temp_db, test_user):
    """Data completeness increases when readiness data is present."""
    svc = SessionScoringService()

    session_date = date(2025, 1, 20)
    _create_readiness(test_user["id"], session_date)

    sid = _create_session(test_user["id"], session_date=session_date)

    result = svc.score_session(test_user["id"], sid)
    # With readiness: 4/5 pillars
    assert result["data_completeness"] > 0.6


# ------------------------------------------------------------------ #
# Biometric validation (WHOOP data)
# ------------------------------------------------------------------ #


def test_biometric_pillar_with_whoop_data(temp_db, test_user):
    """Biometric pillar appears when WHOOP strain data exists."""
    svc = SessionScoringService()

    sid = _create_session(
        test_user["id"],
        whoop_strain=12.5,
        whoop_avg_hr=155,
        whoop_max_hr=185,
    )

    result = svc.score_session(test_user["id"], sid)
    assert "biometric_validation" in result["pillars"]


def test_biometric_pillar_absent_without_whoop(temp_db, test_user):
    """Biometric pillar absent when no WHOOP data on session."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"])

    result = svc.score_session(test_user["id"], sid)
    assert "biometric_validation" not in result["pillars"]


# ------------------------------------------------------------------ #
# Edge cases
# ------------------------------------------------------------------ #


def test_zero_rolls_gets_minimum_credit(temp_db, test_user):
    """Session with 0 rolls still gets engagement minimum credit."""
    svc = SessionScoringService()
    sid = _create_session(test_user["id"], rolls=0)

    result = svc.score_session(test_user["id"], sid)
    engagement = result["pillars"]["engagement"]
    assert engagement["score"] > 0


def test_no_submissions_neutral_effectiveness(temp_db, test_user):
    """Session with no submissions gets neutral effectiveness."""
    svc = SessionScoringService()
    sid = _create_session(
        test_user["id"],
        submissions_for=0,
        submissions_against=0,
    )

    result = svc.score_session(test_user["id"], sid)
    effectiveness = result["pillars"]["effectiveness"]
    # Neutral = 50% pct when no sub data
    assert effectiveness["pct"] == 50

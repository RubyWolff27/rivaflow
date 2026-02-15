"""Tests for SessionScoringService (Wave 4 coverage).

Covers:
- BJJ session scoring (gi/no-gi)
- Supplementary session scoring (s&c)
- Score tier boundary labels
- Backfill of unscored sessions
- Graceful degradation with missing data
"""

from datetime import date, timedelta

from rivaflow.core.services.session_scoring_service import (
    SCORE_VERSION,
    SessionScoringService,
    _tier_label,
)
from rivaflow.db.repositories.session_repo import SessionRepository

# ── Tier label tests ───────────────────────────────────────────


class TestTierLabels:
    """Verify score-to-tier boundary mapping."""

    def test_light_tier_zero(self):
        assert _tier_label(0) == "Light"

    def test_light_tier_upper(self):
        assert _tier_label(29) == "Light"

    def test_solid_tier_lower(self):
        assert _tier_label(30) == "Solid"

    def test_solid_tier_upper(self):
        assert _tier_label(49) == "Solid"

    def test_strong_tier_lower(self):
        assert _tier_label(50) == "Strong"

    def test_strong_tier_upper(self):
        assert _tier_label(69) == "Strong"

    def test_excellent_tier_lower(self):
        assert _tier_label(70) == "Excellent"

    def test_excellent_tier_upper(self):
        assert _tier_label(84) == "Excellent"

    def test_peak_tier_lower(self):
        assert _tier_label(85) == "Peak"

    def test_peak_tier_upper(self):
        assert _tier_label(100) == "Peak"

    def test_negative_score_returns_light(self):
        assert _tier_label(-5) == "Light"


# ── BJJ session scoring ───────────────────────────────────────


class TestScoreBJJSession:
    """Score a BJJ (gi / no-gi) session end-to-end."""

    def test_score_gi_session(self, temp_db, test_user, session_factory):
        """A gi session should produce a valid breakdown."""
        sid = session_factory(
            class_type="gi",
            duration_mins=60,
            intensity=4,
            rolls=6,
            submissions_for=3,
            submissions_against=1,
            partners=["Alice", "Bob", "Charlie"],
            techniques=["armbar", "triangle", "kimura"],
        )

        svc = SessionScoringService()
        breakdown = svc.score_session(test_user["id"], sid)

        assert breakdown is not None
        assert breakdown["rubric"] == "bjj"
        assert breakdown["version"] == SCORE_VERSION
        assert 0 <= breakdown["total"] <= 100
        assert breakdown["label"] in {
            "Light",
            "Solid",
            "Strong",
            "Excellent",
            "Peak",
        }
        assert isinstance(breakdown["pillars"], dict)
        assert "effort" in breakdown["pillars"]
        assert "engagement" in breakdown["pillars"]
        assert "effectiveness" in breakdown["pillars"]
        # Without readiness / WHOOP, those pillars absent
        assert "readiness_alignment" not in breakdown["pillars"]
        assert "biometric_validation" not in breakdown["pillars"]
        assert 0 < breakdown["data_completeness"] <= 1.0

    def test_score_nogi_session(self, temp_db, test_user, session_factory):
        """no-gi should also use the bjj rubric."""
        sid = session_factory(
            class_type="no-gi",
            intensity=3,
            rolls=4,
        )

        svc = SessionScoringService()
        bd = svc.score_session(test_user["id"], sid)

        assert bd is not None
        assert bd["rubric"] == "bjj"

    def test_score_persisted_to_db(self, temp_db, test_user, session_factory):
        """After scoring, the session row has the score."""
        sid = session_factory(class_type="gi", rolls=3)

        svc = SessionScoringService()
        bd = svc.score_session(test_user["id"], sid)

        repo = SessionRepository()
        session = repo.get_by_id(test_user["id"], sid)
        assert session is not None
        assert session["session_score"] == bd["total"]
        assert session["score_version"] == SCORE_VERSION
        assert isinstance(session["score_breakdown"], dict)


# ── Supplementary session scoring ──────────────────────────────


class TestScoreSupplementarySession:
    """Score a supplementary (s&c / cardio) session."""

    def test_score_sc_session(self, temp_db, test_user, session_factory):
        sid = session_factory(
            class_type="s&c",
            duration_mins=45,
            intensity=3,
            rolls=0,
        )

        svc = SessionScoringService()
        bd = svc.score_session(test_user["id"], sid)

        assert bd is not None
        assert bd["rubric"] == "supplementary"
        assert 0 <= bd["total"] <= 100
        assert "effort" in bd["pillars"]
        assert "consistency" in bd["pillars"]
        # BJJ-specific pillars should be absent
        assert "engagement" not in bd["pillars"]
        assert "effectiveness" not in bd["pillars"]

    def test_score_cardio_session(self, temp_db, test_user, session_factory):
        sid = session_factory(
            class_type="cardio",
            duration_mins=30,
            intensity=5,
        )
        svc = SessionScoringService()
        bd = svc.score_session(test_user["id"], sid)

        assert bd["rubric"] == "supplementary"
        assert bd["total"] > 0


# ── Competition scoring ────────────────────────────────────────


class TestScoreCompetitionSession:
    """Score a competition session."""

    def test_score_competition(self, temp_db, test_user, session_factory):
        sid = session_factory(
            class_type="competition",
            duration_mins=90,
            intensity=5,
            rolls=8,
            submissions_for=4,
            submissions_against=0,
            attacks_attempted=10,
            attacks_successful=6,
            defenses_attempted=5,
            defenses_successful=4,
        )
        svc = SessionScoringService()
        bd = svc.score_session(test_user["id"], sid)

        assert bd is not None
        assert bd["rubric"] == "competition"
        assert 0 <= bd["total"] <= 100
        assert "effectiveness" in bd["pillars"]


# ── Graceful degradation ───────────────────────────────────────


class TestGracefulDegradation:
    """Scoring with minimal / missing data."""

    def test_no_rolls_no_subs_no_notes(self, temp_db, test_user, session_factory):
        """Session with bare minimum data still scores."""
        sid = session_factory(
            class_type="gi",
            duration_mins=60,
            intensity=3,
            rolls=0,
            submissions_for=0,
            submissions_against=0,
            partners=None,
            techniques=None,
            notes=None,
        )
        svc = SessionScoringService()
        bd = svc.score_session(test_user["id"], sid)

        assert bd is not None
        assert 0 <= bd["total"] <= 100
        assert bd["rubric"] == "bjj"
        # Engagement should still give minimum credit
        eng = bd["pillars"]["engagement"]
        assert eng["score"] > 0

    def test_nonexistent_session_returns_none(self, temp_db, test_user):
        svc = SessionScoringService()
        result = svc.score_session(test_user["id"], 99999)
        assert result is None


# ── Backfill ───────────────────────────────────────────────────


class TestBackfillUserScores:
    """backfill_user_scores scores all unscored sessions."""

    def test_backfill_scores_all(self, temp_db, test_user, session_factory):
        """Create several unscored sessions and backfill."""
        ids = []
        for i in range(3):
            sid = session_factory(
                session_date=date.today() - timedelta(days=i),
                class_type="gi",
                rolls=3 + i,
            )
            ids.append(sid)

        svc = SessionScoringService()
        result = svc.backfill_user_scores(test_user["id"])

        assert result["scored"] == 3
        assert result["skipped"] == 0
        assert result["total"] == 3

        # Verify all sessions now have scores
        repo = SessionRepository()
        for sid in ids:
            s = repo.get_by_id(test_user["id"], sid)
            assert s["session_score"] is not None
            assert s["score_version"] == SCORE_VERSION

    def test_backfill_skips_already_scored(self, temp_db, test_user, session_factory):
        """Already-scored sessions are skipped."""
        sid = session_factory(class_type="gi", rolls=4)

        svc = SessionScoringService()
        # Score once
        svc.score_session(test_user["id"], sid)
        # Backfill should skip
        result = svc.backfill_user_scores(test_user["id"])

        assert result["scored"] == 0
        assert result["skipped"] == 1
        assert result["total"] == 1


# ── Recalculate ────────────────────────────────────────────────


class TestRecalculate:
    """recalculate_session re-computes an existing score."""

    def test_recalculate_updates_score(self, temp_db, test_user, session_factory):
        sid = session_factory(
            class_type="gi",
            intensity=2,
            rolls=2,
        )
        svc = SessionScoringService()
        bd1 = svc.score_session(test_user["id"], sid)
        assert bd1 is not None

        # Update the session to higher effort
        repo = SessionRepository()
        repo.update(
            user_id=test_user["id"],
            session_id=sid,
            intensity=5,
            rolls=10,
            submissions_for=5,
        )

        bd2 = svc.recalculate_session(test_user["id"], sid)
        assert bd2 is not None
        # Score should change (likely higher)
        assert bd2["total"] != bd1["total"]

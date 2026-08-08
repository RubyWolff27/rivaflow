"""Tests for the Grapple coach's context blocks (Wave 3, MA-F2/MA-F3).

Replaces test_grapple_context_whoop.py: the WHOOP block read an honest-empty
seam and never spoke. The coach now reads real check-in columns (1-5 scales),
the physiology composition (canonical readiness + strain + sleep debt), the
purple-belt curriculum summary, and Air biometrics through redact_for_llm.
"""

from unittest.mock import MagicMock, patch

from rivaflow.core.services.grapple.context_builder import GrappleContextBuilder
from rivaflow.core.services.privacy_service import PrivacyService

_PHYSIO = "rivaflow.core.services.physiology_service.PhysiologyService"
_CURRIC = "rivaflow.core.services.curriculum_service.CurriculumService"


def _bare_builder():
    builder = GrappleContextBuilder.__new__(GrappleContextBuilder)
    builder.user_id = 4
    return builder


class TestPhysiologyContext:
    @patch(_PHYSIO)
    def test_full_body_state_block(self, mock_svc):
        mock_svc.return_value.get_physiology.return_value = {
            "readiness": {
                "score": 48,
                "band": "yellow",
                "state": "Strained",
                "headline": "Below baseline — technical/skills over hard rolls today.",
            },
            "strain_target": {
                "available": True,
                "target_load": 3.4,
                "band": [1.4, 5.4],
                "chronic_load": 5.3,
                "acute_load": 3.6,
            },
            "sleep_debt": {"available": True, "debt_hours": 13.0, "nights": 7},
        }
        result = _bare_builder()._build_physiology_context()

        assert "BODY STATE" in result
        assert "48/100 (yellow) — Strained" in result
        assert "strain target: 3.4" in result
        assert "Load so far today: 3.6" in result
        assert "Sleep debt: 13.0h over 7 nights" in result

    @patch(_PHYSIO)
    def test_missing_data_omits_lines_never_zeros(self, mock_svc):
        mock_svc.return_value.get_physiology.return_value = {
            "readiness": {"score": None, "state": "Building", "headline": ""},
            "strain_target": {"available": False},
            "sleep_debt": {"available": False},
        }
        result = _bare_builder()._build_physiology_context()

        assert "Building" in result
        assert "strain target" not in result
        assert "Sleep debt" not in result
        assert "0" not in result.replace("/100", "")

    @patch(_PHYSIO)
    def test_empty_physiology_returns_empty(self, mock_svc):
        mock_svc.return_value.get_physiology.return_value = {
            "readiness": {},
            "strain_target": {},
            "sleep_debt": {},
        }
        assert _bare_builder()._build_physiology_context() == ""


class TestCurriculumContext:
    @patch(_CURRIC)
    def test_status_counts_per_block(self, mock_svc):
        mock_svc.return_value.get_summary.return_value = {
            "blocks": [
                {
                    "block": "guard",
                    "label": "Guard",
                    "status_counts": {"drilled": 3, "grooved": 1, "live": 0},
                    "weak_evidence": 2,
                },
                {
                    "block": "passing",
                    "label": "Passing",
                    "status_counts": {},
                    "weak_evidence": 0,
                },
            ]
        }
        result = _bare_builder()._build_curriculum_context()

        assert "PURPLE-BELT CURRICULUM" in result
        assert "Guard: drilled 3, grooved 1 (2 weak-evidence)" in result
        assert "Passing" not in result  # empty block omitted, not zeroed

    @patch(_CURRIC)
    def test_no_slots_returns_empty(self, mock_svc):
        mock_svc.return_value.get_summary.return_value = {"blocks": []}
        assert _bare_builder()._build_curriculum_context() == ""


class TestReadinessCheckinContext:
    def test_real_row_shape_real_scales(self):
        """MA-F2: the coach must read check_date/energy/soreness/sleep/stress
        on 1-5 — the old keys fabricated 'Energy 0/10' every day."""
        builder = _bare_builder()
        builder.session_repo = MagicMock()
        builder.readiness_repo = MagicMock()
        builder.user_repo = MagicMock()
        builder.profile_repo = MagicMock()
        builder.grading_repo = MagicMock()
        builder.insights = MagicMock()

        builder.session_repo.get_recent.return_value = [
            {
                "session_date": "2026-08-07",
                "gym_name": "Academy",
                "duration_mins": 60,
                "intensity": 3,
                "rolls": 4,
            }
        ]
        builder.readiness_repo.get_by_date_range.return_value = [
            {
                "check_date": "2026-08-07",
                "energy": 4,
                "soreness": 2,
                "sleep": 3,
                "stress": 2,
                "composite_score": 15,
            }
        ]
        builder.insights.get_training_load_management.return_value = {
            "available": False
        }
        builder.insights.get_overtraining_risk.side_effect = Exception("skip")

        with patch(_PHYSIO) as physio, patch(_CURRIC) as curric:
            physio.return_value.get_physiology.side_effect = Exception("skip")
            curric.return_value.get_summary.side_effect = Exception("skip")
            context = builder._build_user_context()

        assert "Energy 4/5" in context
        assert "Soreness 2/5" in context
        assert "Sleep 3/5" in context
        assert "Stress 2/5" in context
        assert "composite 15/20" in context
        assert "0/10" not in context
        assert "Energy 0" not in context


class TestRedactionBiometrics:
    def test_garmin_and_partners_pass_through(self):
        session = {
            "session_date": "2026-08-07",
            "gym_name": "Academy",
            "duration_mins": 60,
            "intensity": 3,
            "rolls": 4,
            "garmin_training_load": 141.2,
            "garmin_avg_hr": 148,
            "garmin_max_hr": 176,
            "partners": ["Tato Silva", "Vincenzo Marino"],
        }
        redacted = PrivacyService.redact_for_llm(session)

        assert redacted["trimp"] == 141.2
        assert redacted["avg_hr"] == 148
        assert redacted["max_hr"] == 176
        assert redacted["partners"] == ["Tato", "Vincenzo"]

    def test_absent_biometrics_stay_absent(self):
        redacted = PrivacyService.redact_for_llm(
            {"session_date": "2026-08-07", "gym_name": "A", "duration_mins": 60}
        )
        assert "trimp" not in redacted
        assert "partners" not in redacted

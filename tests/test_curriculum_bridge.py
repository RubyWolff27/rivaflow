"""Tests for the session↔curriculum evidence bridge (Wave 3, MA-F1 — the P0).

A logged session's techniques and roll submissions match against the slate's
seq_finish text (folded, glossary-alias-aware) to produce one-tap evidence
candidates. Candidates only: evidence stays human-confirmed.
"""

from unittest.mock import MagicMock, patch

from rivaflow.core.services.curriculum_service import CurriculumService

_TECH = "rivaflow.db.repositories.session_technique_repo.SessionTechniqueRepository"
_ROLL = "rivaflow.db.repositories.session_roll_repo.SessionRollRepository"
_GLOSS = "rivaflow.db.repositories.GlossaryRepository"

_MOVEMENTS = [
    {"id": 34, "name": "Armbar", "aliases": '["Juji Gatame"]'},
    {"id": 20, "name": "Triangle Choke", "aliases": '["Triangle"]'},
    {"id": 53, "name": "Berimbolo", "aliases": "[]"},
]

_SLOTS = [
    {
        "id": 501,
        "block": "guard",
        "requirement_label": "Submission of choice",
        "seq_entry": "Closed guard",
        "seq_position": "High guard",
        "seq_finish": "Armbar",
    },
    {
        "id": 502,
        "block": "guard",
        "requirement_label": "Submission of choice",
        "seq_entry": "Open guard",
        "seq_position": "Diamond",
        "seq_finish": "Triangle",  # alias of Triangle Choke
    },
    {
        "id": 503,
        "block": "back",
        "requirement_label": "Finish of choice",
        "seq_entry": "Back take",
        "seq_position": "Body triangle",
        "seq_finish": "Rear naked choke",
    },
]


def _service(slots=None, evidence=None):
    svc = CurriculumService()
    svc.repo = MagicMock()
    svc.repo.list_slots.return_value = slots if slots is not None else _SLOTS
    svc.repo.list_evidence.return_value = evidence or []
    return svc


def _derive(svc, techniques, rolls):
    with patch(_TECH) as tech, patch(_ROLL) as roll, patch(_GLOSS) as gloss:
        tech.get_by_session_id.return_value = techniques
        roll.get_by_session_id.return_value = rolls
        gloss.list_all.return_value = _MOVEMENTS
        return svc.derive_evidence_candidates(user_id=4, session_id=99)


class TestEvidenceBridge:
    def test_drilled_technique_matches_slot_finish(self):
        result = _derive(_service(), [{"movement_id": 34}], [])

        assert len(result["candidates"]) == 1
        c = result["candidates"][0]
        assert c["slot_id"] == 501
        assert c["kind"] == "drilled"
        assert c["matched_movement"] == "Armbar"
        assert c["session_id"] == 99
        assert c["sequence"] == "Closed guard → High guard → Armbar"

    def test_roll_submission_becomes_live_with_partner(self):
        rolls = [{"partner_name": "Tato", "submissions_for": [20]}]
        result = _derive(_service(), [], rolls)

        c = result["candidates"][0]
        assert c["slot_id"] == 502  # matched via the "Triangle" alias
        assert c["kind"] == "live"
        assert c["partner_ref"] == "Tato"

    def test_live_outranks_drilled_for_same_movement(self):
        result = _derive(
            _service(),
            [{"movement_id": 34}],
            [{"partner_name": "Vin", "submissions_for": [34]}],
        )

        c = result["candidates"][0]
        assert c["kind"] == "live"
        assert c["partner_ref"] == "Vin"

    def test_already_evidenced_slot_excluded(self):
        evidence = [{"slot_id": 501, "session_id": 99}]
        result = _derive(_service(evidence=evidence), [{"movement_id": 34}], [])

        assert result["candidates"] == []

    def test_same_slot_different_session_still_offered(self):
        evidence = [{"slot_id": 501, "session_id": 42}]
        result = _derive(_service(evidence=evidence), [{"movement_id": 34}], [])

        assert [c["slot_id"] for c in result["candidates"]] == [501]

    def test_no_matches_returns_empty(self):
        result = _derive(_service(), [{"movement_id": 53}], [])  # Berimbolo ∉ slate
        assert result["candidates"] == []

    def test_empty_session_short_circuits(self):
        svc = _service()
        with patch(_TECH) as tech, patch(_ROLL) as roll:
            tech.get_by_session_id.return_value = []
            roll.get_by_session_id.return_value = []
            result = svc.derive_evidence_candidates(user_id=4, session_id=99)

        assert result == {"session_id": 99, "candidates": []}
        svc.repo.list_slots.assert_not_called()

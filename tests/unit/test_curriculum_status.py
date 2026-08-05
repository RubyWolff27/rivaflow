"""Unit tests for the curriculum status engine and the gap-first coach export.

Every test here is DB-free: ``compute_slot_state`` is a pure function, and the
service tests swap ``service.repo`` for a mock. The point of the module is the
integrity core — that a status can only ever come from logged evidence and coach
sign-offs — so the tests sit on both sides of each ladder boundary.
"""

import re
from datetime import date, timedelta
from pathlib import Path

import pytest

from rivaflow.core.exceptions import ValidationError
from rivaflow.core.services.curriculum_service import (
    GROOVED_MIN_SESSIONS,
    GROOVED_MIN_SPAN_DAYS,
    LIVE_MIN_OCCASIONS,
    LIVE_MIN_PARTNERS,
    STATUS_COACH_VERIFIED,
    STATUS_DRILLED,
    STATUS_GROOVED,
    STATUS_LIVE,
    STATUS_NOT_STARTED,
    CurriculumService,
    compute_slot_state,
)


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """Override any DB init — nothing in this module touches a database."""
    yield


TODAY = date(2026, 8, 5)


def _ev(day_offset, kind="drilled", session_id=None, band=None, size=None, ref=None):
    """One evidence row, `day_offset` days before TODAY."""
    return {
        "kind": kind,
        "session_id": session_id,
        "partner_rank_band": band,
        "partner_size": size,
        "partner_ref": ref,
        "logged_at": (TODAY - timedelta(days=day_offset)).isoformat(),
    }


def _signoff(verdict, created, signoff_id=1, coach="Prof. Anthony"):
    return {
        "id": signoff_id,
        "verdict": verdict,
        "coach_name": coach,
        "created_at": created.isoformat(),
    }


# --------------------------------------------------------------- ladder rungs


def test_no_evidence_is_not_started():
    state = compute_slot_state([], [], today=TODAY)
    assert state["status"] == STATUS_NOT_STARTED
    assert state["staleness_days"] is None
    assert state["weak_evidence"] is False


def test_one_session_is_drilled():
    state = compute_slot_state([_ev(3, session_id=1)], [], today=TODAY)
    assert state["status"] == STATUS_DRILLED
    assert state["sessions"] == 1


def test_two_sessions_over_a_long_span_is_still_drilled():
    """Boundary: session count, not elapsed time, is what blocks grooved here."""
    evidence = [_ev(40, session_id=1), _ev(0, session_id=2)]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["sessions"] == GROOVED_MIN_SESSIONS - 1
    assert state["span_days"] == 40
    assert state["status"] == STATUS_DRILLED


def test_three_sessions_spanning_exactly_twenty_one_days_is_grooved():
    evidence = [
        _ev(21, session_id=1),
        _ev(10, session_id=2),
        _ev(0, session_id=3),
    ]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["sessions"] == GROOVED_MIN_SESSIONS
    assert state["span_days"] == GROOVED_MIN_SPAN_DAYS
    assert state["status"] == STATUS_GROOVED


def test_three_sessions_spanning_twenty_days_is_not_grooved():
    """One day short of three weeks — the rung is not awarded."""
    evidence = [
        _ev(20, session_id=1),
        _ev(10, session_id=2),
        _ev(0, session_id=3),
    ]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["span_days"] == GROOVED_MIN_SPAN_DAYS - 1
    assert state["status"] == STATUS_DRILLED


def test_same_day_entries_without_a_session_collapse_to_one_session():
    """Two notebook entries on one day must not fake a second session."""
    evidence = [_ev(5), _ev(5), _ev(5)]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["sessions"] == 1
    assert state["status"] == STATUS_DRILLED


def test_two_live_occasions_against_two_partners_is_live():
    evidence = [
        _ev(9, kind="live", session_id=1, band="same", size="similar"),
        _ev(2, kind="live", session_id=2, band="higher", size="bigger"),
    ]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["live_occasions"] == LIVE_MIN_OCCASIONS
    assert state["live_partners"] == LIVE_MIN_PARTNERS
    assert state["status"] == STATUS_LIVE


def test_two_live_occasions_against_one_partner_is_not_live():
    """Same rank+size pair twice is one partner identity, so the rung is denied."""
    evidence = [
        _ev(9, kind="live", session_id=1, band="same", size="similar"),
        _ev(2, kind="live", session_id=2, band="same", size="similar"),
    ]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["live_occasions"] == 2
    assert state["live_partners"] == 1
    assert state["status"] == STATUS_DRILLED


def test_one_live_occasion_is_not_live():
    evidence = [_ev(2, kind="live", session_id=1, band="higher", size="bigger")]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["live_occasions"] == LIVE_MIN_OCCASIONS - 1
    assert state["status"] == STATUS_DRILLED


# ------------------------------------------------------------- coach sign-off


def test_coach_verified_requires_a_signoff_never_evidence():
    """A slot drowning in live evidence still is not coach-verified."""
    evidence = [
        _ev(30, kind="live", session_id=1, band="higher", size="bigger"),
        _ev(15, kind="live", session_id=2, band="same", size="similar"),
        _ev(0, kind="live", session_id=3, band="lower", size="smaller"),
    ]
    assert compute_slot_state(evidence, [], today=TODAY)["status"] == STATUS_LIVE

    verified = compute_slot_state(
        evidence, [_signoff("verified", date(2026, 8, 1))], today=TODAY
    )
    assert verified["status"] == STATUS_COACH_VERIFIED


def test_non_verified_verdicts_do_not_promote():
    evidence = [_ev(3, session_id=1)]
    for verdict in ("not-yet", "show-me"):
        state = compute_slot_state(
            evidence, [_signoff(verdict, date(2026, 8, 1))], today=TODAY
        )
        assert state["status"] == STATUS_DRILLED
        assert state["signoff_verdict"] == verdict


def test_latest_signoff_supersedes_an_earlier_verified():
    """The coach changed their mind; both rows survive, the newest one rules."""
    signoffs = [
        _signoff("verified", date(2026, 6, 1), signoff_id=1),
        _signoff("not-yet", date(2026, 7, 20), signoff_id=2),
    ]
    state = compute_slot_state([_ev(3, session_id=1)], signoffs, today=TODAY)
    assert state["status"] == STATUS_DRILLED
    assert state["signoff_verdict"] == "not-yet"
    assert state["signoff_count"] == 2


# ---------------------------------------------------- staleness + weak evidence


def test_staleness_counts_days_since_the_most_recent_evidence():
    evidence = [_ev(90, session_id=1), _ev(34, session_id=2)]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["staleness_days"] == 34
    assert state["last_evidence_at"] == (TODAY - timedelta(days=34)).isoformat()
    # Staleness never demotes: the rung is unchanged by age.
    assert state["status"] == STATUS_DRILLED


def test_weak_evidence_when_every_live_rep_is_smaller_and_lower():
    evidence = [
        _ev(9, kind="live", session_id=1, band="lower", size="smaller", ref="p1"),
        _ev(2, kind="live", session_id=2, band="lower", size="smaller", ref="p2"),
    ]
    state = compute_slot_state(evidence, [], today=TODAY)
    assert state["status"] == STATUS_LIVE
    assert state["weak_evidence"] is True


def test_weak_evidence_clears_when_one_rep_is_against_a_bigger_partner():
    evidence = [
        _ev(9, kind="live", session_id=1, band="lower", size="smaller", ref="p1"),
        _ev(2, kind="live", session_id=2, band="lower", size="bigger", ref="p2"),
    ]
    assert compute_slot_state(evidence, [], today=TODAY)["weak_evidence"] is False


def test_weak_evidence_is_false_without_live_evidence():
    """Drilled-only slots are not "weak" — they simply have no live claim."""
    evidence = [_ev(5, session_id=1), _ev(1, session_id=2)]
    assert compute_slot_state(evidence, [], today=TODAY)["weak_evidence"] is False


# ---------------------------------------------------------------- coach export


def _slot(slot_id, block, req, index, **overrides):
    row = {
        "id": slot_id,
        "user_id": 1,
        "belt": "purple",
        "block": block,
        "requirement_key": req,
        "requirement_label": req,
        "slot_index": index,
        "of_choice": 1,
        "is_draft": 0,
        "seq_entry": "entry",
        "seq_position": "position",
        "seq_finish": "finish",
        "game_tag": "a-game",
        "movement_ids": None,
        "tension_note": None,
        "blocker_note": None,
        "declared_at": None,
    }
    row.update(overrides)
    return row


def _service(slots, evidence, signoffs, meta=None):
    from unittest.mock import MagicMock

    service = CurriculumService()
    service.repo = MagicMock()
    service.repo.list_slots.return_value = slots
    service.repo.list_evidence.return_value = evidence
    service.repo.list_signoffs.return_value = signoffs
    service.repo.get_meta.return_value = meta
    return service


def _export_fixture():
    slots = [
        _slot(1, "guard", "guard-subs", 1),  # verified
        _slot(2, "guard", "guard-subs", 2),  # in progress
        _slot(3, "guard", "guard-subs", 3, seq_finish=None),  # never started
        _slot(4, "standup", "td-strikes", 1),  # coach said not yet
    ]
    evidence = [
        {"slot_id": 1, **_ev(5, session_id=1)},
        {"slot_id": 2, **_ev(5, session_id=1)},
        {"slot_id": 4, **_ev(5, session_id=1)},
    ]
    signoffs = [
        {"slot_id": 1, **_signoff("verified", date(2026, 8, 1), signoff_id=1)},
        {"slot_id": 4, **_signoff("not-yet", date(2026, 8, 1), signoff_id=2)},
    ]
    return _service(slots, evidence, signoffs, meta={"competition_date": "2026-09-12"})


def test_export_carries_no_percentage_field_anywhere():
    """Binding council rule: no percentage goes near the coach view."""
    export = _export_fixture().get_export(user_id=1, today=TODAY)
    banned = re.compile(r"percent|pct", re.IGNORECASE)

    def walk(node, path="root"):
        if isinstance(node, dict):
            for key, value in node.items():
                assert not banned.search(str(key)), f"percentage key at {path}.{key}"
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")

    walk(export)


def test_export_orders_gaps_first_and_hard_gates_above_everything():
    export = _export_fixture().get_export(user_id=1, today=TODAY)

    keys = list(export.keys())
    assert keys.index("hard_gates") < keys.index("blocks")
    assert export["hard_gates"][0]["key"] == "competition"

    # Stand up comes before guard: the export follows syllabus block order.
    assert [b["block"] for b in export["blocks"]] == ["standup", "guard"]

    guard = next(b for b in export["blocks"] if b["block"] == "guard")
    assert list(guard.keys()).index("not_yet") < list(guard.keys()).index("in_progress")
    assert list(guard.keys()).index("in_progress") < list(guard.keys()).index(
        "verified"
    )
    assert [s["id"] for s in guard["not_yet"]] == [3]
    assert [s["id"] for s in guard["in_progress"]] == [2]
    assert [s["id"] for s in guard["verified"]] == [1]


def test_a_coach_not_yet_outranks_the_log_in_the_export():
    """Slot 4 has evidence, so its rung is `drilled` — but the coach said no."""
    export = _export_fixture().get_export(user_id=1, today=TODAY)
    standup = next(b for b in export["blocks"] if b["block"] == "standup")
    assert [s["id"] for s in standup["not_yet"]] == [4]
    assert standup["in_progress"] == []
    assert standup["not_yet"][0]["status"] == STATUS_DRILLED


def test_summary_reports_raw_counts_per_block():
    summary = _export_fixture().get_summary(user_id=1, today=TODAY)
    guard = next(b for b in summary["blocks"] if b["block"] == "guard")
    assert guard["slot_count"] == 3
    assert guard["status_counts"][STATUS_COACH_VERIFIED] == 1
    assert guard["status_counts"][STATUS_DRILLED] == 1
    assert guard["status_counts"][STATUS_NOT_STARTED] == 1
    assert guard["game_tag_counts"]["a-game"] == 3
    assert summary["totals"]["slot_count"] == 4
    assert summary["hard_gates"][0]["met"] is True


# ----------------------------------------------------------- seed + integrity


def test_seed_builds_the_full_syllabus_shape():
    rows = CurriculumService.build_seed_rows()
    assert len(rows) == 90
    of_choice = [r for r in rows if r["of_choice"]]
    assert len(of_choice) == 88
    # The two cluster requirements are single, non-of-choice slots.
    clusters = {r["requirement_key"] for r in rows if not r["of_choice"]}
    assert clusters == {"mount-defences", "back-defences"}
    # Undeclared by default.
    assert all(r.get("seq_finish") is None for r in rows)


def test_draft_slate_fills_every_of_choice_slot_and_is_marked_draft():
    rows = CurriculumService.build_seed_rows(with_draft=True)
    of_choice = [r for r in rows if r["of_choice"]]
    assert len(of_choice) == 88
    assert all(r["seq_finish"] for r in of_choice)
    assert all(r["is_draft"] for r in of_choice)
    # Cluster slots stay undeclared — there is no sequence to declare.
    assert all(not r["is_draft"] for r in rows if not r["of_choice"])


def test_status_cannot_be_set_through_a_declaration_payload():
    with pytest.raises(ValidationError):
        CurriculumService._validate_declaration({"status": "coach-verified"})


def test_unknown_game_tag_is_rejected():
    with pytest.raises(ValidationError):
        CurriculumService._validate_declaration({"game_tag": "s-tier"})


# ------------------------------------------------------------------ migration


def _split_like_the_migration_runner(path):
    """Reproduce database.py::_apply_migrations exactly.

    It splits the file on the statement terminator BEFORE stripping comment
    lines, so a terminator inside a comment silently severs the next statement
    and that table never gets created. This bit migration 118 during authoring.
    """
    statements = []
    for raw in [s.strip() for s in path.read_text().split(";") if s.strip()]:
        lines = [
            ln
            for ln in raw.split("\n")
            if ln.strip() and not ln.strip().startswith("--")
        ]
        clean = "\n".join(lines).strip()
        if clean:
            statements.append(clean)
    return statements


@pytest.mark.parametrize(
    "variant", ["118_curriculum_slots.sql", "118_curriculum_slots_pg.sql"]
)
def test_migration_survives_the_runners_statement_split(variant):
    import rivaflow.db as db_pkg

    path = Path(db_pkg.__file__).parent / "migrations" / variant
    statements = _split_like_the_migration_runner(path)

    assert statements, f"{variant} produced no statements"
    for statement in statements:
        assert statement.upper().startswith(("CREATE TABLE", "CREATE INDEX")), (
            f"{variant} split into a fragment that is not valid DDL — check for a "
            f"statement terminator inside a comment:\n{statement[:120]}"
        )

    created = {s.split()[5] for s in statements if s.upper().startswith("CREATE TABLE")}
    assert created == {
        "curriculum_slot",
        "curriculum_slot_evidence",
        "curriculum_slot_signoff",
        "curriculum_meta",
    }


@pytest.mark.parametrize(
    "variant", ["118_curriculum_slots.sql", "118_curriculum_slots_pg.sql"]
)
def test_no_table_has_a_status_column(variant):
    """The integrity core is structural: there is nothing for a route to set."""
    import rivaflow.db as db_pkg

    path = Path(db_pkg.__file__).parent / "migrations" / variant
    for statement in _split_like_the_migration_runner(path):
        for line in statement.splitlines()[1:]:
            assert line.strip().split(" ")[0] != "status", f"status column in {variant}"

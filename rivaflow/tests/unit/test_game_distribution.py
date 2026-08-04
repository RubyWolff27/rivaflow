"""Unit tests for GameDistributionService (the Game Distribution radar)."""

from unittest.mock import MagicMock

import pytest

from rivaflow.core.services.game_distribution import (
    AXES,
    GameDistributionService,
    _parse_movement_ids,
)


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """Override conftest's DB init — every repo here is mocked; no DB needed."""
    yield


GLOSSARY = [
    {"id": 1, "name": "Armbar", "category": "submission"},
    {"id": 2, "name": "Triangle", "category": "submission"},
    {"id": 3, "name": "Knee Cut", "category": "pass"},
    {"id": 4, "name": "Scissor Sweep", "category": "sweep"},
    {"id": 5, "name": "Closed Guard", "category": "position"},  # not an axis
]


def _service_with(sessions, techs_by_session, rolls_by_session):
    svc = GameDistributionService()
    svc.session_repo = MagicMock()
    svc.session_repo.get_by_date_range.return_value = sessions
    svc.glossary_repo = MagicMock()
    svc.glossary_repo.list_all.return_value = GLOSSARY
    svc.technique_repo = MagicMock()
    svc.technique_repo.batch_get_by_session_ids.return_value = techs_by_session
    svc.roll_repo = MagicMock()
    svc.roll_repo.get_by_session_ids.return_value = rolls_by_session
    return svc


def test_axes_fixed_order_and_metrics():
    sessions = [
        {"id": 10, "duration_mins": 60, "garmin_training_load": 100.0},
        {"id": 11, "duration_mins": 60, "garmin_training_load": None},
    ]
    techs = {10: [{"movement_id": 1}, {"movement_id": 1}, {"movement_id": 3}]}
    rolls = {11: [{"submissions_for": "[2]"}]}
    out = _service_with(sessions, techs, rolls).get_game_distribution(user_id=4)

    assert [a["key"] for a in out["axes"]] == [k for k, _ in AXES]
    by_key = {a["key"]: a for a in out["axes"]}
    # submission: armbar x2 (techs) + triangle x1 (roll) = 3 touches, 2 distinct
    assert by_key["submission"]["frequency"]["value"] == 3
    assert by_key["submission"]["coverage"]["value"] == 2
    assert by_key["pass"]["frequency"]["value"] == 1
    assert by_key["sweep"]["frequency"]["value"] == 0
    # axis_max is shared across axes for the metric (distribution semantics)
    assert by_key["sweep"]["frequency"]["axis_max"] == 3
    assert out["totals"]["touches"] == 4
    assert out["totals"]["mat_hours"] == 2.0


def test_load_attribution_and_unattributed_gap():
    sessions = [
        # techniques logged + HR: attributed 2/3 submission, 1/3 pass
        {"id": 10, "duration_mins": 60, "garmin_training_load": 90.0},
        # HR but NO techniques: must stay unattributed, never guessed
        {"id": 11, "duration_mins": 60, "garmin_training_load": 60.0},
    ]
    techs = {10: [{"movement_id": 1}, {"movement_id": 2}, {"movement_id": 3}]}
    out = _service_with(sessions, techs, {}).get_game_distribution(user_id=4)

    by_key = {a["key"]: a for a in out["axes"]}
    assert by_key["submission"]["load"]["value"] == 60.0
    assert by_key["pass"]["load"]["value"] == 30.0
    # 60 of 150 TRIMP unattributed -> 40%
    assert out["gaps"]["load_unattributed_pct"] == 40.0
    assert out["gaps"]["load_sessions_with_hr"] == 2
    assert out["gaps"]["sessions_with_techniques"] == 1


def test_non_axis_categories_counted_as_other_not_axes():
    sessions = [{"id": 10, "duration_mins": 60, "garmin_training_load": None}]
    techs = {10: [{"movement_id": 5}]}  # position category
    out = _service_with(sessions, techs, {}).get_game_distribution(user_id=4)

    assert all(a["frequency"]["value"] == 0 for a in out["axes"])
    assert out["gaps"]["other_category_touches"] == 1
    # a session whose only touches are non-axis still counts as technique-logged? No:
    # per_axis stays empty so it must NOT count toward sessions_with_techniques.
    assert out["gaps"]["sessions_with_techniques"] == 0


def test_windowed_mode_supplies_prev_and_dates():
    svc = _service_with([], {}, {})
    out = svc.get_game_distribution(user_id=4, window="8w")
    assert out["window"]["mode"] == "8w"
    assert out["window"]["start"] is not None
    assert out["window"]["prev_start"] is not None
    # two windows queried
    assert svc.session_repo.get_by_date_range.call_count == 2
    for axis in out["axes"]:
        assert axis["coverage"]["prev"] is not None or axis["coverage"]["prev"] == 0


def test_all_time_mode_no_prev():
    out = _service_with([], {}, {}).get_game_distribution(user_id=4, window="all")
    assert out["window"]["start"] is None
    assert out["window"]["prev_start"] is None
    assert all(a["coverage"]["prev"] is None for a in out["axes"])
    assert out["gaps"]["load_unattributed_pct"] is None  # no TRIMP at all


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, []),
        ("", []),
        ("[1, 2]", [1, 2]),
        ('["3"]', [3]),
        ([4, "5"], [4, 5]),
        ("not json", []),
        ("[null]", []),
    ],
)
def test_parse_movement_ids(raw, expected):
    assert _parse_movement_ids(raw) == expected

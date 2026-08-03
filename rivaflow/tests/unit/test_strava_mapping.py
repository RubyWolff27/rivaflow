"""Pure-logic tests for the Strava activity→session mapping.

No database and no network — these cover the decisions that determine what a
July backfill actually produces.
"""

from datetime import UTC, datetime

import pytest

from rivaflow.core.services.strava_service import (
    StravaService,
    classify_activity,
    derive_intensity,
    is_importable,
)


class TestClassifyActivity:
    """Name heuristics beat sport_type, because BJJ has no Strava sport type."""

    @pytest.mark.parametrize(
        "name,expected",
        [
            ("No-Gi + rolls", "no-gi"),
            ("nogi class", "no-gi"),
            ("no gi open mat", "no-gi"),  # most specific rule wins
            ("Open Mat Saturday", "open-mat"),
            ("IBJJF comp prep", "competition"),
            ("Wrestling takedowns", "wrestling"),
            ("Judo throws", "judo"),
            ("Drilling guard passes", "drilling"),
            ("Gi class 6:30am", "gi"),
            ("Yoga flow", "yoga"),
            ("Physio rehab shoulder", "physio"),
            ("Mobility + stretching", "mobility"),
        ],
    )
    def test_name_rules(self, name, expected):
        assert classify_activity({"name": name, "sport_type": "Workout"}) == expected

    def test_generic_grappling_uses_user_default(self):
        """Unlabelled mat time defers to the user's usual class type."""
        activity = {"name": "BJJ", "sport_type": "Workout"}
        assert classify_activity(activity, "gi") == "gi"
        assert classify_activity(activity, "no-gi") == "no-gi"

    def test_gi_word_boundary_does_not_false_positive(self):
        """A bare 'gi' rule must not fire inside unrelated words."""
        # "begin" and "Gippsland" both contain the letters g-i.
        assert classify_activity({"name": "Begin easy ride", "sport_type": "Ride"}) == (
            "cardio"
        )
        assert (
            classify_activity({"name": "Gippsland loop", "sport_type": "Ride"})
            == "cardio"
        )

    @pytest.mark.parametrize(
        "sport_type,expected",
        [
            ("WeightTraining", "s&c"),
            ("Crossfit", "s&c"),
            ("HighIntensityIntervalTraining", "s&c"),
            ("Run", "cardio"),
            ("Ride", "cardio"),
            ("Swim", "cardio"),
            ("Rowing", "cardio"),
            ("Yoga", "yoga"),
            ("Pilates", "mobility"),
        ],
    )
    def test_sport_type_fallback(self, sport_type, expected):
        assert classify_activity(
            {"name": "Afternoon session", "sport_type": sport_type}
        ) == (expected)

    def test_unknown_sport_type_defaults_to_cardio(self):
        assert (
            classify_activity({"name": "Kitesurf", "sport_type": "Kitesurf"})
            == "cardio"
        )

    def test_produces_only_valid_class_types(self):
        """Every mapping output must satisfy the sessions.class_type CHECK constraint."""
        allowed = {
            "gi",
            "no-gi",
            "open-mat",
            "competition",
            "s&c",
            "cardio",
            "mobility",
            "wrestling",
            "judo",
            "yoga",
            "rehab",
            "physio",
            "drilling",
        }
        names = [
            "No-Gi",
            "Open Mat",
            "comp prep",
            "wrestling",
            "judo",
            "drilling",
            "gi",
            "yoga",
            "rehab",
            "mobility",
            "BJJ",
            "strength",
            "Morning Ride",
        ]
        for name in names:
            assert classify_activity({"name": name, "sport_type": "Workout"}) in allowed


class TestIsImportable:
    def test_short_activity_is_not_a_session(self):
        assert not is_importable({"sport_type": "Workout", "elapsed_time_sec": 600})

    def test_long_enough_activity_is_importable(self):
        assert is_importable({"sport_type": "Workout", "elapsed_time_sec": 3600})

    def test_walks_are_excluded(self):
        assert not is_importable({"sport_type": "Walk", "elapsed_time_sec": 3600})

    def test_already_linked_is_excluded(self):
        assert not is_importable(
            {"sport_type": "Workout", "elapsed_time_sec": 3600, "session_id": 7}
        )

    def test_dismissed_is_excluded(self):
        assert not is_importable(
            {"sport_type": "Workout", "elapsed_time_sec": 3600, "dismissed": True}
        )

    def test_falls_back_to_moving_time(self):
        assert is_importable({"sport_type": "Workout", "moving_time_sec": 3600})


class TestDeriveIntensity:
    @pytest.mark.parametrize("suffer,expected", [(5, 2), (30, 3), (60, 4), (120, 5)])
    def test_from_suffer_score(self, suffer, expected):
        assert derive_intensity({"suffer_score": suffer}) == expected

    def test_suffer_score_zero_is_used_not_skipped(self):
        """0 is a real value — a falsy check here would silently fall through to HR."""
        assert (
            derive_intensity(
                {"suffer_score": 0, "avg_heart_rate": 180, "max_heart_rate": 190}
            )
            == 2
        )

    @pytest.mark.parametrize(
        "avg,mx,expected", [(100, 190, 2), (130, 190, 3), (150, 190, 4), (175, 190, 5)]
    )
    def test_from_heart_rate_ratio(self, avg, mx, expected):
        assert (
            derive_intensity({"avg_heart_rate": avg, "max_heart_rate": mx}) == expected
        )

    def test_defaults_to_middle_without_signals(self):
        assert derive_intensity({}) == 3

    def test_always_in_valid_range(self):
        for suffer in (0, 1, 19, 20, 39, 40, 74, 75, 500):
            assert 1 <= derive_intensity({"suffer_score": suffer}) <= 5


class TestMapActivityFields:
    def test_detail_overrides_summary_for_heart_rate(self):
        """HR and calories are absent on the list payload — detail must win."""
        summary = {
            "id": 1,
            "name": "BJJ",
            "type": "Workout",
            "start_date": "2026-07-14T20:30:00Z",
            "elapsed_time": 3600,
        }
        detail = {"average_heartrate": 148.0, "max_heartrate": 181.0, "calories": 620}

        fields = StravaService.map_activity_fields(summary, detail)

        assert fields["avg_heart_rate"] == 148
        assert fields["max_heart_rate"] == 181
        assert fields["calories"] == 620
        assert fields["detail_fetched"] is True

    def test_summary_only_marks_detail_not_fetched(self):
        fields = StravaService.map_activity_fields(
            {"id": 1, "name": "Ride", "start_date": "2026-07-14T06:00:00Z"}
        )
        assert fields["detail_fetched"] is False
        assert fields["avg_heart_rate"] is None

    def test_parses_utc_timestamps(self):
        fields = StravaService.map_activity_fields(
            {"id": 1, "start_date": "2026-07-14T20:30:00Z"}
        )
        assert fields["start_time"] == datetime(2026, 7, 14, 20, 30, tzinfo=UTC)

    def test_float_heart_rate_rounds_to_int(self):
        """Strava returns HR as a float — the column is INTEGER."""
        fields = StravaService.map_activity_fields(
            {"id": 1, "start_date": "2026-07-14T20:30:00Z"},
            {"average_heartrate": 147.6},
        )
        assert fields["avg_heart_rate"] == 148

    def test_missing_start_date_yields_none(self):
        assert StravaService.map_activity_fields({"id": 1})["start_time"] is None

    def test_sport_type_falls_back_to_type(self):
        fields = StravaService.map_activity_fields(
            {"id": 1, "type": "Workout", "start_date": "2026-07-14T20:30:00Z"}
        )
        assert fields["sport_type"] == "Workout"

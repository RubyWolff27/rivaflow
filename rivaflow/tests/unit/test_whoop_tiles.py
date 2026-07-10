"""Wave 2.4 (B4/B3) — server-composed cockpit tiles + hero, and the tag vocabulary
endpoint. Pure unit tests: `_compose_tiles`/`_compose_hero` take an already-built
whoop_summary()-shaped dict (no DB), and the route/repo layers are exercised with
mocks, mirroring tests/unit/test_summary_snapshot.py's asyncio.run(route(...))
pattern for the `@route_error_handler`-wrapped endpoint.
"""

from __future__ import annotations

import asyncio

from rivaflow.api.routes import whoop as whoop_route
from rivaflow.core import whoop_analytics
from rivaflow.core.whoop_tiles import _compose_hero, _compose_tiles
from rivaflow.db.repositories.whoop_repo import BUILTIN_TAGS, WhoopRepository


def _contributor(signal: str, effect: float) -> dict:
    return {
        "signal": signal,
        "label": signal,
        "z": effect,
        "weight": 0.25,
        "effect": effect,
        "direction": "supports recovery" if effect >= 0 else "drags recovery",
    }


def _full_summary(*, state: str = "Prime", prevention_tier: str = "green") -> dict:
    return {
        "readiness": {
            "state": state,
            "headline": "Above your baseline — green light to train hard.",
            "score": 87,
            "contributors": [
                _contributor("hrv", 0.6),
                _contributor("rhr", 0.2),
                _contributor("sleep", -0.045),
                _contributor("resp", 0.01),
            ],
        },
        "prevention": {
            "available": True,
            "tier": prevention_tier,
            "headline": "SAFETY: sustained deviation across two signal families.",
        },
        "hrv_today": {"day": "2026-07-10", "rmssd": 55.2, "ln_rmssd": 4.0},
        "resting_hr_today": {"day": "2026-07-10", "resting_hr": 48},
        "sleep": {
            "available": True,
            "quality_score": 88,
            "quality_version": "sleep-quality-v1",
            "duration_hours": 7.8,
        },
        "strain_target": {
            "available": True,
            "state": state,
            "target_load": 14.5,
            "capped": False,
            "headline": "Recovered — you can push. Target strain 14.5.",
        },
        "respiratory_rate": {"available": True, "respiratory_rate": 14.2},
        "stress": {"available": True, "stress": 20},
    }


# ── _compose_tiles — full fixture ───────────────────────────────────────────


def test_full_fixture_tile_ids_order_and_accents():
    tiles = _compose_tiles(_full_summary())

    assert [t["id"] for t in tiles] == [
        "readiness",
        "hrv",
        "resting_hr",
        "sleep",
        "strain",
        "respiratory",
        "stress",
    ]
    assert [t["order"] for t in tiles] == [0, 1, 2, 3, 4, 5, 6]

    by_id = {t["id"]: t for t in tiles}
    assert by_id["readiness"]["value"] == "Prime"
    assert by_id["readiness"]["accent"] == "green"
    assert by_id["hrv"] == {
        "id": "hrv",
        "label": "HRV",
        "value": 55.2,
        "unit": "ms",
        "accent": "green",  # hrv contributor effect 0.6 >= 0
        "order": 1,
    }
    assert by_id["resting_hr"]["accent"] == "green"  # rhr contributor effect 0.2 >= 0
    assert by_id["sleep"]["accent"] == "amber"  # sleep contributor effect -0.045 < 0
    assert by_id["sleep"]["value"] == 88
    assert by_id["strain"]["accent"] == "green"  # Prime, not capped
    assert by_id["strain"]["value"] == 14.5
    assert (
        by_id["respiratory"]["accent"] == "green"
    )  # resp contributor effect 0.01 >= 0
    assert by_id["stress"]["accent"] == "green"  # 20 <= 33


# ── _compose_tiles — sparse fixture (missing metrics contribute no tile) ───


def test_sparse_fixture_omits_unavailable_tiles_without_blanks():
    summary = {
        "readiness": {"state": "Building", "headline": "Building…", "contributors": []},
        "prevention": {"available": False},
        "hrv_today": None,
        "resting_hr_today": None,
        "sleep": {"available": False, "reason": "no overnight data"},
        "strain_target": {"available": False, "state": "Building", "reason": "…"},
        "respiratory_rate": {"available": False},
        "stress": {"available": False},
    }

    tiles = _compose_tiles(summary)

    assert tiles == [
        {
            "id": "readiness",
            "label": "Readiness",
            "value": "Building",
            "unit": None,
            "accent": "neutral",
            "order": 0,
        }
    ]


# ── _compose_tiles — sabbath fixture ────────────────────────────────────────


def test_sabbath_fixture_has_no_strain_tile_and_readiness_reads_rest():
    summary = {
        "readiness": {
            "state": "Rest",
            "headline": "Sabbath — rest is prescribed. No score today.",
            "driver": "sabbath",
            "score": None,
            "caveat": None,
        },
        "prevention": {"available": False},
        "hrv_today": {"day": "2026-07-13", "rmssd": 50.0},
        "resting_hr_today": {"day": "2026-07-13", "resting_hr": 49},
        "sleep": {"available": True, "quality_score": 80},
        # prescribe_strain returns exactly this shape for state == "Rest".
        "strain_target": {
            "available": False,
            "state": "Rest",
            "reason": "Sabbath — rest is prescribed.",
        },
        "respiratory_rate": {"available": False},
        "stress": {"available": False},
    }

    tiles = _compose_tiles(summary)
    ids = [t["id"] for t in tiles]

    assert "strain" not in ids
    by_id = {t["id"]: t for t in tiles}
    assert by_id["readiness"]["value"] == "Rest"
    assert (
        by_id["readiness"]["accent"] == "neutral"
    )  # no baseline z, no prevention firing


def test_sabbath_prevention_still_recolors_readiness_tile_safety_fires_on_sabbath():
    summary = {
        "readiness": {
            "state": "Rest",
            "headline": "Sabbath — rest is prescribed. No score today.",
            "driver": "sabbath",
            "score": None,
            "caveat": None,
        },
        "prevention": {"available": True, "tier": "amber", "headline": "SAFETY"},
        "hrv_today": None,
        "resting_hr_today": None,
        "sleep": {"available": False},
        "strain_target": {"available": False, "state": "Rest", "reason": "…"},
        "respiratory_rate": {"available": False},
        "stress": {"available": False},
    }

    tiles = _compose_tiles(summary)

    assert tiles[0]["id"] == "readiness"
    assert tiles[0]["value"] == "Rest"
    assert (
        tiles[0]["accent"] == "amber"
    )  # prevention fires (safety) even on the Sabbath


# ── prevention override — readiness tile accent ─────────────────────────────


def test_prevention_red_overrides_green_readiness_tile_accent():
    tiles = _compose_tiles(_full_summary(state="Balanced", prevention_tier="red"))
    readiness_tile = next(t for t in tiles if t["id"] == "readiness")
    assert readiness_tile["accent"] == "red"


def test_prevention_amber_does_not_downgrade_already_red_readiness_tile():
    tiles = _compose_tiles(_full_summary(state="Rundown", prevention_tier="amber"))
    readiness_tile = next(t for t in tiles if t["id"] == "readiness")
    assert (
        readiness_tile["accent"] == "red"
    )  # Rundown is already red; amber can't downgrade it


def test_prevention_green_tier_does_not_touch_readiness_accent():
    tiles = _compose_tiles(_full_summary(state="Balanced", prevention_tier="green"))
    readiness_tile = next(t for t in tiles if t["id"] == "readiness")
    assert readiness_tile["accent"] == "green"


# ── _compose_hero ────────────────────────────────────────────────────────────


def test_hero_severity_mapping_without_prevention_firing():
    expected = {
        "Prime": ("green", "info"),
        "Balanced": ("green", "info"),
        "Strained": ("amber", "caution"),
        "Rundown": ("red", "alert"),
        "Rest": ("neutral", "info"),
        "Building": ("neutral", "info"),
    }
    for state, (color, severity) in expected.items():
        summary = _full_summary(state=state, prevention_tier="green")
        hero = _compose_hero(summary)
        assert hero["state"] == state
        assert hero["state_color"] == color
        assert hero["severity"] == severity


def test_hero_prevention_red_overrides_green_readiness():
    summary = _full_summary(state="Balanced", prevention_tier="red")
    hero = _compose_hero(summary)
    assert hero["state_color"] == "red"
    assert hero["severity"] == "alert"
    assert hero["headline"] == summary["prevention"]["headline"]


def test_hero_prevention_amber_lifts_severity_and_recolors():
    summary = _full_summary(state="Balanced", prevention_tier="amber")
    hero = _compose_hero(summary)
    assert hero["state_color"] == "amber"
    assert hero["severity"] == "caution"
    assert hero["headline"] == summary["prevention"]["headline"]


def test_hero_prevention_amber_does_not_downgrade_rundown_but_swaps_headline():
    summary = _full_summary(state="Rundown", prevention_tier="amber")
    hero = _compose_hero(summary)
    assert hero["state_color"] == "red"  # unchanged — amber can't downgrade red
    assert hero["severity"] == "alert"  # unchanged — amber can't downgrade alert
    # Safety headline still wins even when it doesn't need to escalate colour/severity.
    assert hero["headline"] == summary["prevention"]["headline"]


def test_hero_prevention_unavailable_or_green_leaves_readiness_headline():
    summary = _full_summary(state="Balanced", prevention_tier="green")
    hero = _compose_hero(summary)
    assert hero["headline"] == summary["readiness"]["headline"]

    summary["prevention"] = {"available": False}
    hero2 = _compose_hero(summary)
    assert hero2["headline"] == summary["readiness"]["headline"]


# ── whoop_summary wiring — tiles/hero ride along additively ────────────────


def test_whoop_summary_output_carries_tiles_and_hero(monkeypatch):
    class _FakeProfile:
        tz = whoop_analytics.LOCAL_TZ
        sleep_need_h = 8.0
        age = 40
        rest_weekday = 6
        max_hr_override = None

    monkeypatch.setattr(
        whoop_analytics, "get_whoop_profile", lambda uid: _FakeProfile()
    )
    monkeypatch.setattr(whoop_analytics, "user_max_hr", lambda uid: {"max_hr": 180.0})
    monkeypatch.setattr(
        whoop_analytics,
        "compute_readiness",
        lambda uid, today_is_sabbath=False: {
            "state": "Prime",
            "headline": "green light to push",
            "score": 87,
            "contributors": [_contributor("hrv", 0.6)],
        },
    )
    monkeypatch.setattr(
        whoop_analytics,
        "daily_resting_rmssd",
        lambda uid, days=14, max_hr=None: [{"day": "2026-07-10", "rmssd": 55.2}],
    )
    monkeypatch.setattr(
        whoop_analytics,
        "daily_resting_hr",
        lambda uid, days=14, max_hr=None: [{"day": "2026-07-10", "resting_hr": 48}],
    )
    monkeypatch.setattr(
        whoop_analytics,
        "daily_cardio_load",
        lambda uid, days=14, max_hr=None: [{"day": "2026-07-10", "cardio_load": 12.0}],
    )
    monkeypatch.setattr(
        whoop_analytics,
        "nightly_sleep",
        lambda uid: {
            "available": True,
            "duration_hours": 7.8,
            "coverage_pct": 95,
            "fragmented": False,
            "sleep_start": "2026-07-09T22:00:00+10:00",
            "sleep_end": "2026-07-10T06:00:00+10:00",
        },
    )
    monkeypatch.setattr(
        whoop_analytics, "nightly_sleep_history", lambda uid, nights=7, max_hr=None: []
    )
    monkeypatch.setattr(
        whoop_analytics,
        "respiratory_rate",
        lambda uid: {"available": True, "respiratory_rate": 14.2},
    )
    monkeypatch.setattr(
        whoop_analytics,
        "today_stress",
        lambda uid, max_hr=None: {"available": True, "stress": 20},
    )
    monkeypatch.setattr(whoop_analytics, "capture_coverage", lambda uid, days=21: {})
    monkeypatch.setattr(
        whoop_analytics,
        "prevention_watch",
        lambda uid: {"available": True, "tier": "green", "headline": "In range."},
    )
    monkeypatch.setattr(whoop_analytics, "_chronic_load", lambda cardio: 12.0)
    monkeypatch.setattr(
        whoop_analytics,
        "prescribe_strain",
        lambda state, chronic, acute: {
            "available": True,
            "state": state,
            "target_load": 14.5,
            "capped": False,
            "headline": "Recovered — you can push. Target strain 14.5.",
        },
    )
    monkeypatch.setattr(whoop_analytics, "acwr", lambda series: {"available": False})

    result = whoop_analytics.whoop_summary(1)

    assert "tiles" in result and "hero" in result
    assert [t["id"] for t in result["tiles"]] == [
        "readiness",
        "hrv",
        "resting_hr",
        "sleep",
        "strain",
        "respiratory",
        "stress",
    ]
    assert result["hero"]["state"] == "Prime"
    assert result["hero"]["headline"] == "green light to push"
    # Additive — every pre-existing key untouched.
    assert result["readiness"]["state"] == "Prime"
    assert result["strain_target"]["target_load"] == 14.5


def test_deriver_version_bumped_to_v2():
    assert whoop_analytics.COCKPIT_DERIVER_VERSION == "whoop-summary-v2"


# ── tag vocabulary — repo layer ─────────────────────────────────────────────


def test_tag_vocabulary_returns_builtins_when_nothing_used(monkeypatch):
    monkeypatch.setattr(WhoopRepository, "distinct_tags", staticmethod(lambda uid: []))
    assert WhoopRepository.tag_vocabulary(1) == list(BUILTIN_TAGS)


def test_tag_vocabulary_appends_custom_tags_without_duplicating_builtins(monkeypatch):
    monkeypatch.setattr(
        WhoopRepository,
        "distinct_tags",
        staticmethod(lambda uid: ["ill", "big-comp", "alcohol"]),
    )
    result = WhoopRepository.tag_vocabulary(1)
    assert result == [*BUILTIN_TAGS, "big-comp"]


# ── tag vocabulary — route layer ────────────────────────────────────────────


def test_tag_vocabulary_endpoint_returns_tags_dict(monkeypatch):
    monkeypatch.setattr(
        WhoopRepository,
        "tag_vocabulary",
        staticmethod(lambda uid: ["alcohol", "ill", "big-comp"]),
    )

    result = asyncio.run(whoop_route.tag_vocabulary_endpoint(current_user={"id": 42}))

    assert result == {"tags": ["alcohol", "ill", "big-comp"]}

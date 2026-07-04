"""P2 delivery — once-daily digest compiler + cooldown (pure, no DB)."""

from __future__ import annotations

from datetime import date

from rivaflow.core.whoop_digest import (
    DEFAULT_COOLDOWN_DAYS,
    compile_digest,
    route_items,
    should_alert,
)

AMBER = {"available": True, "tier": "amber", "headline": "watch"}
GREEN = {"available": True, "tier": "green", "headline": "in range"}
PRIME = {"state": "Prime", "headline": "push", "caveat": "green != healthy"}
STRAIN_OK = {"available": True, "headline": "target 12"}


def test_amber_is_safety_and_fires_even_on_sabbath():
    items = route_items(PRIME, STRAIN_OK, AMBER, today_is_sabbath=True)
    safety = [i for i in items if i["channel"] == "safety"]
    assert safety and safety[0]["fires"] is True and safety[0]["tier"] == "amber"


def test_readiness_and_strain_are_sabbath_silenced():
    items = route_items(PRIME, STRAIN_OK, GREEN, today_is_sabbath=True)
    perf = [i for i in items if i["channel"] == "performance"]
    assert perf and all(i["fires"] is False for i in perf)


def test_performance_fires_on_a_normal_day():
    items = route_items(PRIME, STRAIN_OK, GREEN, today_is_sabbath=False)
    perf = [i for i in items if i["channel"] == "performance"]
    assert perf and all(i["fires"] is True for i in perf)


def test_green_prevention_has_no_safety_item():
    items = route_items(PRIME, STRAIN_OK, GREEN, today_is_sabbath=False)
    assert not [i for i in items if i["channel"] == "safety"]


def test_building_readiness_not_surfaced():
    items = route_items({"state": "Building"}, {"available": False}, GREEN, False)
    assert not [i for i in items if i["kind"] == "readiness"]


# --- cooldown -------------------------------------------------------------


def test_should_alert_no_history():
    assert should_alert(None, date(2026, 6, 10)) is True


def test_should_alert_within_cooldown():
    assert should_alert("2026-06-09", date(2026, 6, 10)) is False  # 1 day < 3


def test_should_alert_after_cooldown():
    assert should_alert("2026-06-05", date(2026, 6, 10)) is True  # 5 days >= 3


# --- compile_digest -------------------------------------------------------


def test_compile_surfaces_safety_alert():
    d = compile_digest(PRIME, STRAIN_OK, AMBER)
    assert d["safety_alert"] is not None
    assert d["safety_alert"]["key"] == "prevention:amber"
    assert "no live-refresh" in d["delivery"]


def test_compile_respects_cooldown():
    today = date(2026, 6, 10)
    recent = compile_digest(
        PRIME,
        STRAIN_OK,
        AMBER,
        today=today,
        last_alerts={"prevention:amber": "2026-06-09"},
    )
    assert recent["safety_alert"] is None  # in cooldown
    old = compile_digest(
        PRIME,
        STRAIN_OK,
        AMBER,
        today=today,
        last_alerts={"prevention:amber": "2026-06-01"},
    )
    assert old["safety_alert"] is not None  # cooldown elapsed


def test_compile_green_no_alert():
    assert compile_digest(PRIME, STRAIN_OK, GREEN)["safety_alert"] is None


def test_cooldown_default():
    assert DEFAULT_COOLDOWN_DAYS == 3

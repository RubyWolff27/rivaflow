"""Cockpit Tier-1 prevention visibility + the hourly stale-snapshot escalation guard.

Two safety surfaces, both pure (no Postgres, no network):

1. render_today_story / _hero_html surface an amber/red prevention override in Tier-1 (banner + accent
   shift), on every day including the Sabbath, reusing whoop_tiles._compose_hero's override rule — the
   same rule the phone's server-driven hero rides on. Green/neutral prevention → no visual change.

2. scheduler._prevention_escalation_job rebuilds a user's snapshot ONLY when their live prevention tier
   has escalated above the tier baked into their stored snapshot — never on de-escalation or no change.
"""

from __future__ import annotations

import asyncio
import json

from rivaflow.core import scheduler
from rivaflow.core.scheduler import _prevention_escalation_job, _prevention_rank
from rivaflow.core.whoop_cockpit import render_today_story

# --- Prevention headlines (the real safety copy the phone surfaces via _compose_hero) ---------------
RED_HEADLINE = (
    "Strong multi-signal deviation from your baseline — rest and recover. This is not a "
    "diagnosis; if you feel unwell, see a clinician."
)
AMBER_HEADLINE = (
    "Your autonomics are working harder than your baseline — could be illness, training, "
    "alcohol, heat, or poor sleep. Ease today and watch."
)

READY = {
    "state": "Balanced",
    "headline": "Train as planned",
    "caveat": None,
    "contributors": [],
}
STRAIN_OK = {"available": True, "target_load": 10.0, "chronic_load": 11.0}


def _story(
    prevention: dict | None, *, is_sabbath: bool = False, readiness: dict | None = None
) -> str:
    return render_today_story(
        readiness or READY,
        "narrative line",
        {"available": False},
        {"available": False},
        9,
        None,
        (
            {"available": False, "reason": "Sabbath — rest is prescribed."}
            if is_sabbath
            else STRAIN_OK
        ),
        is_sabbath=is_sabbath,
        prevention=prevention,
    )


# ---------------------------------------------------------------------------
# 1. Tier-1 hero override rendering
# ---------------------------------------------------------------------------


def test_hero_red_override_renders_alert_banner_and_red_accent():
    out = _story({"available": True, "tier": "red", "headline": RED_HEADLINE})
    assert "prevention-banner alert" in out  # red = alert styling
    assert "🛑 Rest &amp; recover" in out
    assert (
        "Strong multi-signal deviation" in out
    )  # message sourced from the prevention dict, not re-copied
    assert "#f87171" in out  # red accent shift (verdict colour + hero border)


def test_hero_amber_override_renders_caution_banner_and_amber_accent():
    out = _story({"available": True, "tier": "amber", "headline": AMBER_HEADLINE})
    assert "prevention-banner caution" in out  # amber = caution styling
    assert "⚠️ Ease &amp; watch" in out
    assert "working harder than your baseline" in out
    assert "#fbbf24" in out  # amber accent shift


def test_hero_green_prevention_renders_no_banner_and_no_accent_shift():
    out = _story({"available": True, "tier": "green", "headline": "In range."})
    assert "prevention-banner" not in out
    # No override colour bleeds in and the hero section keeps its default (unstyled) border.
    assert "#f87171" not in out and "#fbbf24" not in out
    assert (
        'class="panel hero"><div class="ico">' in out
    )  # no inline border-color style injected


def test_hero_unavailable_prevention_renders_no_banner():
    out = _story({"available": False, "reason": "Building baselines."})
    assert "prevention-banner" not in out


def test_hero_no_prevention_arg_is_byte_compatible_default():
    # Omitting prevention entirely (older callers) must not paint a banner or shift the accent.
    out = render_today_story(
        READY,
        "n",
        {"available": False},
        {"available": False},
        9,
        None,
        STRAIN_OK,
        is_sabbath=False,
    )
    assert "prevention-banner" not in out
    assert 'class="panel hero"' in out


def test_readiness_only_rundown_shows_no_false_positive_banner():
    # Rundown's OWN severity is "alert" in whoop_tiles._compose_hero — with no prevention firing at all,
    # that must NOT be mistaken for a prevention override (the banner is a prevention-specific signal).
    rundown = {"state": "Rundown", "headline": "well below baseline", "caveat": None}
    out = _story(
        {"available": False, "reason": "Building baselines."}, readiness=rundown
    )
    assert "prevention-banner" not in out
    out2 = _story(None, readiness=rundown)
    assert "prevention-banner" not in out2


def test_rundown_plus_amber_prevention_still_shows_banner_despite_no_colour_change():
    # _compose_hero never downgrades colour/severity (Rundown is already red/alert, and amber can't pull it
    # down to caution), but it DOES swap the headline to prevention's own copy whenever prevention fires —
    # the banner must track that FIRE, not a visible colour change, or a real amber signal riding on top of
    # an already-bad readiness day goes unseen. Banner styling follows the unchanged (alert) severity.
    rundown = {"state": "Rundown", "headline": "well below baseline", "caveat": None}
    out = _story(
        {"available": True, "tier": "amber", "headline": AMBER_HEADLINE},
        readiness=rundown,
    )
    assert (
        "prevention-banner alert" in out
    )  # severity stays "alert" — Rundown's own floor, not downgraded
    assert (
        "working harder than your baseline" in out
    )  # but the AMBER headline text still won through


def test_sabbath_red_shows_both_rest_prescribed_and_alert_banner():
    # Safety outranks Sabbath silencing: the 'rest is prescribed' guidance STAYS and the banner is ADDITIONAL.
    out = _story(
        {"available": True, "tier": "red", "headline": RED_HEADLINE},
        is_sabbath=True,
    )
    assert "Sabbath — rest is prescribed" in out  # rest copy preserved
    assert "prevention-banner alert" in out  # AND the red safety banner
    assert "Strong multi-signal deviation" in out


# ---------------------------------------------------------------------------
# 2. Escalation guard job
# ---------------------------------------------------------------------------


class _FakeCursor:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def execute(self, *a, **k):
        return None

    def fetchall(self):
        return self._rows


class _FakeConn:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def cursor(self):
        return _FakeCursor(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _run_job(
    monkeypatch,
    *,
    stored_prevention: dict | None,
    current_prevention: dict,
    has_snapshot: bool = True,
) -> list[int]:
    """Drive _prevention_escalation_job for a single user; return the uids that got rebuilt+stored."""
    rebuilt: list[int] = []

    monkeypatch.setattr(scheduler, "_try_advisory_lock", lambda name: True)
    monkeypatch.setattr(scheduler, "_release_advisory_lock", lambda name: None)
    monkeypatch.setattr(
        "rivaflow.db.database.get_connection", lambda: _FakeConn([{"user_id": 7}])
    )
    monkeypatch.setattr("rivaflow.db.database.convert_query", lambda q: q)

    def _get_metrics(uid: int):
        if not has_snapshot:
            return None
        return {"metrics_json": json.dumps({"prevention": stored_prevention})}

    monkeypatch.setattr(
        "rivaflow.db.repositories.whoop_repo.WhoopRepository.get_cockpit_metrics",
        staticmethod(_get_metrics),
    )
    monkeypatch.setattr(
        "rivaflow.core.whoop_analytics.prevention_watch",
        lambda uid: current_prevention,
    )
    monkeypatch.setattr(
        "rivaflow.core.whoop_analytics.build_cockpit_snapshot",
        lambda uid: ("<html>", "{}", "v1"),
    )
    monkeypatch.setattr(
        "rivaflow.db.repositories.whoop_repo.WhoopRepository.upsert_cockpit_snapshot",
        staticmethod(lambda uid, html, mj, dv: rebuilt.append(uid)),
    )

    asyncio.run(_prevention_escalation_job())
    return rebuilt


def test_prevention_rank_orders_tiers():
    assert _prevention_rank(None) == 0
    assert _prevention_rank({"available": False}) == 0
    assert _prevention_rank({"available": True, "tier": "green"}) == 0
    assert _prevention_rank({"available": True, "tier": "amber"}) == 1
    assert _prevention_rank({"available": True, "tier": "red"}) == 2


def test_escalation_green_to_red_rebuilds(monkeypatch):
    rebuilt = _run_job(
        monkeypatch,
        stored_prevention={"available": True, "tier": "green"},
        current_prevention={"available": True, "tier": "red", "headline": RED_HEADLINE},
    )
    assert rebuilt == [7]  # escalated → immediate rebuild+store


def test_escalation_amber_to_red_rebuilds(monkeypatch):
    rebuilt = _run_job(
        monkeypatch,
        stored_prevention={"available": True, "tier": "amber"},
        current_prevention={"available": True, "tier": "red", "headline": RED_HEADLINE},
    )
    assert rebuilt == [7]


def test_deescalation_red_to_amber_does_not_rebuild(monkeypatch):
    rebuilt = _run_job(
        monkeypatch,
        stored_prevention={"available": True, "tier": "red"},
        current_prevention={
            "available": True,
            "tier": "amber",
            "headline": AMBER_HEADLINE,
        },
    )
    assert (
        rebuilt == []
    )  # de-escalation is deliberately slow-pathed to the 4x/day cadence


def test_unchanged_tier_does_not_rebuild(monkeypatch):
    rebuilt = _run_job(
        monkeypatch,
        stored_prevention={"available": True, "tier": "amber"},
        current_prevention={
            "available": True,
            "tier": "amber",
            "headline": AMBER_HEADLINE,
        },
    )
    assert rebuilt == []


def test_no_stored_snapshot_skips_without_crash(monkeypatch):
    rebuilt = _run_job(
        monkeypatch,
        stored_prevention=None,
        current_prevention={"available": True, "tier": "red", "headline": RED_HEADLINE},
        has_snapshot=False,
    )
    assert (
        rebuilt == []
    )  # no snapshot yet → cadence job creates the first; nothing to escalate against

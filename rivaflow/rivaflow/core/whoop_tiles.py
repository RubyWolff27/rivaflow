"""B4/B3 — server-composed cockpit tiles + hero block (Wave 2.4).

The phone currently hardcodes which whoop_summary fields become tiles, so a new VPS
metric needs an app release before it's visible. This module composes a `tiles` list
and a `hero` block FROM an already-computed whoop_summary() dict (no new DB reads,
no side effects) so a thin display client can render generically: iterate `tiles` in
`order`, colour each by `accent`, and headline the screen from `hero`.

Two ranked scales back the accent/severity logic, both "worse wins":
  - COLOR_RANK: neutral/green (0) < amber (1) < red (2)
  - SEVERITY_RANK: info (0) < caution (1) < alert (2)

`prevention_watch` is the SAFETY channel (fires every day, incl. the Sabbath, and
outranks readiness for urgency — see whoop_analytics.prevention_watch's docstring).
Both the readiness tile's accent and the hero block apply the same override: an
amber/red prevention tier can only escalate colour/severity, never downgrade what
readiness itself already earned (e.g. a Rundown/red day stays red under an amber
prevention tier). The hero's headline is replaced by prevention's own headline
whenever prevention fires amber/red — the safety message must reach the user even
when the performance readiness verdict alone wouldn't have said anything alarming.
"""

from __future__ import annotations

COLOR_RANK: dict[str, int] = {"neutral": 0, "green": 0, "blue": 0, "amber": 1, "red": 2}
SEVERITY_RANK: dict[str, int] = {"info": 0, "caution": 1, "alert": 2}

# Stable tile ids in their fixed display order — readiness always leads.
TILE_ORDER: dict[str, int] = {
    "readiness": 0,
    "hrv": 1,
    "resting_hr": 2,
    "sleep": 3,
    "strain": 4,
    "respiratory": 5,
    "stress": 6,
}

_READINESS_COLOR = {
    "Prime": "green",
    "Balanced": "green",
    "Strained": "amber",
    "Rundown": "red",
    "Rest": "neutral",
    "Building": "neutral",
}
_READINESS_SEVERITY = {
    "Prime": "info",
    "Balanced": "info",
    "Strained": "caution",
    "Rundown": "alert",
    "Rest": "info",
    "Building": "info",
}

# readiness.contributors[*]['signal'] name for each tile that rides the same
# deviation-from-baseline blend (see readiness.py) — reused so a tile's colour
# agrees with whether that signal is currently helping or hurting recovery.
_CONTRIBUTOR_SIGNAL = {
    "hrv": "hrv",
    "resting_hr": "rhr",
    "sleep": "sleep",
    "respiratory": "resp",
}


def _prevention_forced_color(tier: str | None) -> str | None:
    return {"amber": "amber", "red": "red"}.get(tier or "")


def _prevention_forced_severity(tier: str | None) -> str | None:
    return {"amber": "caution", "red": "alert"}.get(tier or "")


def _apply_prevention_color(base: str, tier: str | None) -> str:
    """Prevention can only push a colour UP the COLOR_RANK scale, never down."""
    forced = _prevention_forced_color(tier)
    if forced is None:
        return base
    return forced if COLOR_RANK[forced] > COLOR_RANK.get(base, 0) else base


def _apply_prevention_severity(base: str, tier: str | None) -> str:
    """Prevention can only push severity UP the SEVERITY_RANK scale, never down."""
    forced = _prevention_forced_severity(tier)
    if forced is None:
        return base
    return forced if SEVERITY_RANK[forced] > SEVERITY_RANK.get(base, 0) else base


def _contributor_accent(readiness: dict, signal: str) -> str:
    """green if `signal` currently supports recovery, amber if it drags it, else
    neutral (no baseline yet — Building/Rest/thin data)."""
    for c in readiness.get("contributors") or []:
        if c.get("signal") == signal:
            return "green" if c.get("effect", 0) >= 0 else "amber"
    return "neutral"


def _stress_accent(value: float) -> str:
    if value <= 33:
        return "green"
    if value <= 66:
        return "amber"
    return "red"


def _readiness_tile(summary: dict) -> dict:
    readiness = summary.get("readiness") or {}
    prevention = summary.get("prevention") or {}
    state = readiness.get("state")
    accent = _READINESS_COLOR.get(state or "", "neutral")
    if prevention.get("available"):
        accent = _apply_prevention_color(accent, prevention.get("tier"))
    return {
        "id": "readiness",
        "label": "Readiness",
        "value": state,
        "unit": None,
        "accent": accent,
        "order": TILE_ORDER["readiness"],
    }


def _hrv_tile(summary: dict) -> dict | None:
    hrv = summary.get("hrv_today")
    if not hrv or hrv.get("rmssd") is None:
        return None
    readiness = summary.get("readiness") or {}
    return {
        "id": "hrv",
        "label": "HRV",
        "value": hrv["rmssd"],
        "unit": "ms",
        "accent": _contributor_accent(readiness, _CONTRIBUTOR_SIGNAL["hrv"]),
        "order": TILE_ORDER["hrv"],
    }


def _resting_hr_tile(summary: dict) -> dict | None:
    rhr = summary.get("resting_hr_today")
    if not rhr or rhr.get("resting_hr") is None:
        return None
    readiness = summary.get("readiness") or {}
    return {
        "id": "resting_hr",
        "label": "Resting HR",
        "value": rhr["resting_hr"],
        "unit": "bpm",
        "accent": _contributor_accent(readiness, _CONTRIBUTOR_SIGNAL["resting_hr"]),
        "order": TILE_ORDER["resting_hr"],
    }


def _sleep_tile(summary: dict) -> dict | None:
    sleep = summary.get("sleep")
    if not sleep or not sleep.get("available") or sleep.get("quality_score") is None:
        return None
    readiness = summary.get("readiness") or {}
    return {
        "id": "sleep",
        "label": "Sleep",
        "value": sleep["quality_score"],
        "unit": "pts",
        "accent": _contributor_accent(readiness, _CONTRIBUTOR_SIGNAL["sleep"]),
        "order": TILE_ORDER["sleep"],
    }


def _strain_tile(summary: dict) -> dict | None:
    """No tile on the Sabbath (or Building) — prescribe_strain already returns
    available=False for those states ("rest is prescribed"), so gating on
    `available` alone mirrors the phone's current hiding without a separate
    sabbath check here."""
    strain = summary.get("strain_target")
    if not strain or not strain.get("available"):
        return None
    accent = (
        "amber"
        if strain.get("capped")
        else ("green" if strain.get("state") == "Prime" else "neutral")
    )
    return {
        "id": "strain",
        "label": "Strain Target",
        "value": strain["target_load"],
        "unit": "load",
        "accent": accent,
        "order": TILE_ORDER["strain"],
    }


def _respiratory_tile(summary: dict) -> dict | None:
    resp = summary.get("respiratory_rate")
    if not resp or not resp.get("available") or resp.get("respiratory_rate") is None:
        return None
    readiness = summary.get("readiness") or {}
    return {
        "id": "respiratory",
        "label": "Respiratory Rate",
        "value": resp["respiratory_rate"],
        "unit": "rpm",
        "accent": _contributor_accent(readiness, _CONTRIBUTOR_SIGNAL["respiratory"]),
        "order": TILE_ORDER["respiratory"],
    }


def _stress_tile(summary: dict) -> dict | None:
    stress = summary.get("stress")
    if not stress or not stress.get("available") or stress.get("stress") is None:
        return None
    value = stress["stress"]
    return {
        "id": "stress",
        "label": "Stress",
        "value": value,
        "unit": "pts",
        "accent": _stress_accent(float(value)),
        "order": TILE_ORDER["stress"],
    }


def _compose_tiles(summary: dict) -> list[dict]:
    """Build the ordered tile list from an already-computed whoop_summary() dict.
    Readiness always contributes a tile (its state is never None); every other
    tile is omitted outright when its underlying metric is unavailable/None —
    never emitted with a blank value."""
    builders = (
        _readiness_tile,
        _hrv_tile,
        _resting_hr_tile,
        _sleep_tile,
        _strain_tile,
        _respiratory_tile,
        _stress_tile,
    )
    tiles = [t for t in (b(summary) for b in builders) if t is not None]
    tiles.sort(key=lambda t: t["order"])
    return tiles


def _compose_hero(summary: dict) -> dict:
    """The single headline block a thin client renders at the top of the screen:
    readiness state/headline, prevention-overridden colour + severity (safety
    outranks performance — see module docstring), in
    {state, state_color, headline, severity}."""
    readiness = summary.get("readiness") or {}
    prevention = summary.get("prevention") or {}
    state = readiness.get("state")
    color = _READINESS_COLOR.get(state or "", "neutral")
    severity = _READINESS_SEVERITY.get(state or "", "info")
    headline = readiness.get("headline", "")

    tier = prevention.get("tier") if prevention.get("available") else None
    if tier in ("amber", "red"):
        color = _apply_prevention_color(color, tier)
        severity = _apply_prevention_severity(severity, tier)
        headline = prevention.get("headline", headline)

    return {
        "state": state,
        "state_color": color,
        "headline": headline,
        "severity": severity,
    }

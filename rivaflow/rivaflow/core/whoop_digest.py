"""P2 — Prevention & readiness delivery: the once-daily digest compiler + alert-cooldown (pure core).

Anti-anxiety by design (WHOOP_FUTURE_STATE_PLAN.md B6 delivery): health/anomaly findings are a **once-daily
morning digest with a cooldown**, never a live-refreshing red light. Tier → channel routing is explicit:
  - prevention **amber/red** = the SAFETY channel → fires even on the Sabbath (early-warning, not a nudge);
  - **readiness / strain** = performance nudges → Sabbath-silenced.
A safety alert is rate-limited: the same tier won't re-alert within the cooldown window.

Pure and DB-free — the wiring passes today's date + the last-alert history (from notification records).
"""

from __future__ import annotations

from datetime import date

DEFAULT_COOLDOWN_DAYS = 3
SAFETY_TIERS = {"amber", "red"}
_SILENT_READINESS = {None, "Rest", "Building"}


def route_items(
    readiness: dict, strain: dict, prevention: dict, today_is_sabbath: bool
) -> list[dict]:
    """Decide what the digest surfaces and which channel each item is on. Amber/red prevention is safety
    (fires Sunday); readiness + strain are performance nudges (Sabbath-silenced)."""
    items: list[dict] = []

    tier = prevention.get("tier") if prevention.get("available") else None
    if tier in SAFETY_TIERS:
        items.append(
            {
                "kind": "prevention",
                "channel": "safety",
                "tier": tier,
                "headline": prevention.get("headline", ""),
                "fires": True,  # safety fires regardless of Sabbath
            }
        )

    if readiness.get("state") not in _SILENT_READINESS:
        items.append(
            {
                "kind": "readiness",
                "channel": "performance",
                "state": readiness.get("state"),
                "headline": readiness.get("headline", ""),
                "caveat": readiness.get("caveat"),
                "fires": not today_is_sabbath,
            }
        )

    if strain.get("available"):
        items.append(
            {
                "kind": "strain",
                "channel": "performance",
                "headline": strain.get("headline", ""),
                "fires": not today_is_sabbath,
            }
        )

    return items


def should_alert(
    last_alert_day: str | None,
    today: date,
    cooldown_days: int = DEFAULT_COOLDOWN_DAYS,
) -> bool:
    """Cooldown gate: don't re-fire the same safety signal within `cooldown_days`."""
    if last_alert_day is None:
        return True
    return (
        today.toordinal() - date.fromisoformat(last_alert_day).toordinal()
    ) >= cooldown_days


def compile_digest(
    readiness: dict,
    strain: dict,
    prevention: dict,
    today_is_sabbath: bool = False,
    today: date | None = None,
    last_alerts: dict[str, str] | None = None,
    cooldown_days: int = DEFAULT_COOLDOWN_DAYS,
) -> dict:
    """The once-daily digest. Surfaces the day's items and, if a prevention amber/red is present AND not in
    cooldown, the single `safety_alert` to actually push. `last_alerts` maps a safety key ('prevention:amber')
    to the 'YYYY-MM-DD' it last fired; pass `today` to apply the cooldown (omit for a pure compile/preview).
    """
    last_alerts = last_alerts or {}
    items = route_items(readiness, strain, prevention, today_is_sabbath)

    safety_alert = None
    for it in items:
        if it["channel"] == "safety" and it["fires"]:
            key = f"prevention:{it['tier']}"
            if today is None or should_alert(
                last_alerts.get(key), today, cooldown_days
            ):
                safety_alert = {**it, "key": key}
            break

    return {
        "items": items,
        "safety_alert": safety_alert,  # None → nothing to push (green, or in cooldown)
        "delivery": "once-daily digest — no live-refresh health flags",
    }

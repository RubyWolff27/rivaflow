"""Raw-derived biometrics seam — empty since the WHOOP raw feed retired (Wave 1c).

This seam (Wave 1b) replaced the cancelled WHOOP-cloud recovery cache with
records derived from the raw HR+RR the phone streamed to `/whoop/ingest`. That
BLE capture retired with the self-hosted WHOOP backend (2026-08-07): the band is
cold standby since the Fitbit Air switch and the whoop_hr/whoop_rr tables stopped
filling, so any series served from them would be stale — the exact "reasoning
over dead data" failure the v2 council flagged.

Consumers (Grapple coaching, suggestions, insights, readiness analytics) were
built to treat an empty series exactly like an empty cache, so returning empty
here degrades them honestly. Wave 2 repoints this seam to the Fitbit Air →
Google Health data already arriving on the sessions' garmin_* fields.
"""

from __future__ import annotations


def recovery_series(user_id: int, days: int = 7) -> list[dict]:
    """Recent per-day recovery records — always empty until the Wave 2 repoint."""
    return []


def latest_recovery(user_id: int) -> dict | None:
    """The most recent recovery record — always None until the Wave 2 repoint."""
    return None

"""The whoop_biometrics seam is an honest-empty stub since v2 Wave 1c.

The raw BLE feed retired with the self-hosted WHOOP backend, so the seam must
return empty — never stale records — until Wave 2 repoints it to the Fitbit
Air / Google Health data. Consumers (Grapple, suggestions, insights, readiness
analytics) treat an empty series exactly like the empty cache it replaced; the
consumer-side behaviour stays covered by test_grapple_context_whoop.py and
test_overtraining_whoop.py, which patch this seam.
"""

from rivaflow.core.services import whoop_biometrics


def test_recovery_series_is_empty():
    assert whoop_biometrics.recovery_series(1) == []
    assert whoop_biometrics.recovery_series(1, days=30) == []


def test_latest_recovery_is_none():
    assert whoop_biometrics.latest_recovery(1) is None

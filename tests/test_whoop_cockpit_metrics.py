"""Wave 2.2 — structured cockpit snapshot (metrics JSON beside the HTML).

build_cockpit_snapshot is stubbed off its two DB-backed dependencies, so this
verifies the (html, metrics_json, deriver_version) contract without a DB.
"""

import json

from rivaflow.core import whoop_analytics


def test_build_cockpit_snapshot_returns_html_and_metrics_json(monkeypatch):
    monkeypatch.setattr(
        whoop_analytics, "_build_cockpit_page", lambda uid: "<html>ok</html>"
    )
    monkeypatch.setattr(
        whoop_analytics,
        "whoop_summary",
        lambda uid, today_is_sabbath=False: {
            "readiness": {"state": "Prime", "score": 87},
            "hrv_today": {"rmssd": 50.1},
        },
    )

    html, metrics_json, version = whoop_analytics.build_cockpit_snapshot(1)

    assert html == "<html>ok</html>"
    assert version == whoop_analytics.COCKPIT_DERIVER_VERSION == "whoop-summary-v2"
    # metrics_json is a valid JSON string carrying the structured summary contract
    parsed = json.loads(metrics_json)
    assert parsed["readiness"]["score"] == 87
    assert parsed["hrv_today"]["rmssd"] == 50.1

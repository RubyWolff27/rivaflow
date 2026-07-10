"""Wave 2.1 — WHOOP coach service (pure; no DB, no network).

Verifies the coach reasons over the raw-derived `whoop_summary` (so it cites the
numbers the phone shows), is provider-agnostic via GrappleLLMClient, keeps its
honesty rails, and reads NONE of the dead WHOOP-cloud caches.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import rivaflow.core.services.whoop_coach as wc

SUMMARY = {
    "readiness": {"state": "Prime", "score": 87, "headline": "green light to push"},
    "strain_target": {
        "available": True,
        "target_load": 12.0,
        "headline": "push to ~12",
    },
    "acwr": 1.15,
    "hrv_today": {"rmssd": 57},
    "hrv_trend": [{"rmssd": 48}, {"rmssd": 52}, {"rmssd": 57}],
    "resting_hr_today": {"resting_hr": 50},
    "resting_hr_trend": [{"resting_hr": 52}, {"resting_hr": 51}, {"resting_hr": 50}],
    "sleep": {"available": True, "duration_hours": 7.6, "quality_score": 84},
    "respiratory_rate": {"available": True, "respiratory_rate": 10.2},
    "cardio_load_today": {"cardio_load": 8.5},
    "stress": {"available": True, "stress": 12},
    "prevention": {"tier": "amber", "headline": "resting HR drifting above baseline"},
}


def test_build_coach_context_cites_real_numbers(monkeypatch):
    monkeypatch.setattr(
        wc.whoop_analytics, "whoop_summary", lambda uid, today_is_sabbath=False: SUMMARY
    )
    ctx = wc.build_coach_context(1)
    # The exact figures the phone's /summary shows must be present.
    assert "Prime" in ctx and "87" in ctx
    assert "57 ms" in ctx  # HRV today
    assert "50 bpm" in ctx  # resting HR today
    assert "7.6h" in ctx and "84" in ctx  # sleep
    assert "10.2 rpm" in ctx  # respiratory
    assert "12.0/21" in ctx  # strain target_load
    assert "1.15" in ctx  # acwr
    # Prevention amber surfaced, framed as deviation not diagnosis.
    assert "AMBER" in ctx and "NEVER diagnoses" in ctx


def test_context_marks_missing_data_honestly(monkeypatch):
    thin = {
        "readiness": {"state": "Building", "score": None, "headline": ""},
        "sleep": {"available": False, "reason": "strap silent"},
    }
    monkeypatch.setattr(
        wc.whoop_analytics, "whoop_summary", lambda uid, today_is_sabbath=False: thin
    )
    ctx = wc.build_coach_context(1)
    assert "no data" in ctx and "strap silent" in ctx
    assert "Building" in ctx


def test_sabbath_line_present(monkeypatch):
    monkeypatch.setattr(
        wc.whoop_analytics, "whoop_summary", lambda uid, today_is_sabbath=False: SUMMARY
    )
    ctx = wc.build_coach_context(1, today_is_sabbath=True)
    assert "Sabbath" in ctx and "rest is prescribed" in ctx


def test_sanitize_history_filters_and_trims():
    history = (
        [{"role": "system", "content": "junk"}]
        + [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"}
            for i in range(12)
        ]
        + [{"role": "user", "content": ""}, {"role": "bogus", "content": "x"}]
    )
    clean = wc._sanitize_history(history)
    assert len(clean) == wc._MAX_HISTORY_TURNS
    assert all(t["role"] in ("user", "assistant") and t["content"] for t in clean)
    assert clean[-1]["content"] == "m11"  # trailing turns kept


def test_answer_returns_reply_and_provider(monkeypatch):
    monkeypatch.setattr(
        wc, "build_coach_context", lambda uid, today_is_sabbath=False: "CTX"
    )

    class _FakeClient:
        async def chat(self, messages, user_id, **kwargs):
            # System persona + biometric context + the user turn are all present.
            roles = [m["role"] for m in messages]
            assert roles[0] == "system" and messages[1]["content"] == "CTX"
            assert messages[-1] == {
                "role": "user",
                "content": "Should I roll hard today?",
            }
            return {
                "content": "Your HRV's up — green light.",
                "provider": "groq",
                "model": "llama-3.3-70b-versatile",
                "total_tokens": 210,
            }

    monkeypatch.setattr(wc, "GrappleLLMClient", lambda *a, **k: _FakeClient())

    out = asyncio.run(wc.answer(1, "Should I roll hard today?"))
    assert out["reply"] == "Your HRV's up — green light."
    assert out["provider"] == "groq" and out["model"].startswith("llama")
    assert out["tokens"] == 210


def test_no_dead_cloud_cache_reads():
    """ISC-A2 anti-criterion: the coach must not touch the retired WHOOP-cloud stack."""
    src = Path(wc.__file__).read_text()
    for dead in (
        "WhoopConnectionRepository",
        "recovery_cache",
        "whoop_recovery_cache",
        "GooseRustBridge",
        "FeatureScoreSummary",
    ):
        assert (
            dead not in src
        ), f"coach must not read the dead cloud/Extract path: {dead}"

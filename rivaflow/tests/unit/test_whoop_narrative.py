"""Wave 2.3 — NarrativeProvider seam (pure; no DB, no network).

Verifies the seam contract: rule-based by default (byte-identical), LLM adapter
only when enabled + honest + non-Sabbath, and a hard fallback to the rule-based
line on any failure or honesty-check violation — the cockpit can never break or
over-claim because of this seam.
"""

from __future__ import annotations

import rivaflow.core.services.whoop_narrative as wn

READY = {"state": "Prime", "score": 87, "headline": "push"}
NIGHT = {"available": True, "duration_hours": 7.5}
CROSS = {
    "hrv_ln_trend": [3.9, 4.0, 4.1],
    "rhr_trend": [50, 51, 53],
    "acwr": 1.4,
    "cardio_today": 9.0,
    "strain_target": 12.0,
    "prevention": {"tier": "amber", "headline": "resting HR drifting up"},
}

RULE_SENTINEL = "RULE_BASED_NARRATIVE_LINE"


def _stub_rule_based(monkeypatch, sentinel=RULE_SENTINEL):
    monkeypatch.setattr(
        wn.whoop_analytics, "daily_narrative", lambda *a, **k: sentinel
    )
    return sentinel


def _stub_client(monkeypatch, *, content=None, raises=None):
    class _FakeClient:
        def chat_sync(self, *a, **k):
            if raises is not None:
                raise raises
            return {"content": content, "provider": "groq", "model": "x"}

    monkeypatch.setattr(
        "rivaflow.core.services.grapple.llm_client.GrappleLLMClient",
        lambda *a, **k: _FakeClient(),
    )


# ── ISC-B2: LLM off (default) → exactly the rule-based line ──────────────────


def test_llm_disabled_returns_rule_based(monkeypatch):
    monkeypatch.delenv("WHOOP_NARRATIVE_LLM", raising=False)
    sentinel = _stub_rule_based(monkeypatch)
    # Even if a client were reachable, it must not be consulted when disabled.
    _stub_client(monkeypatch, raises=AssertionError("client must not be called"))
    assert wn.compose_narrative(1, readiness=READY, night=NIGHT) == sentinel


# ── ISC-B3/B5: LLM on + honest + non-Sabbath → the model's cross-signal story ─


def test_llm_enabled_uses_honest_output(monkeypatch):
    monkeypatch.setenv("WHOOP_NARRATIVE_LLM", "1")
    _stub_rule_based(monkeypatch)
    monkeypatch.setattr(wn, "_is_sabbath", lambda: False)
    story = "Your resting HR has crept up three days running while HRV held — ease into technical work."
    _stub_client(monkeypatch, content=story)
    assert wn.compose_narrative(1, readiness=READY, night=NIGHT, cross_signals=CROSS) == story


# ── ISC-B4: honesty post-checks reject over-claiming output → fallback ───────


def test_diagnosis_output_falls_back(monkeypatch):
    monkeypatch.setenv("WHOOP_NARRATIVE_LLM", "1")
    sentinel = _stub_rule_based(monkeypatch)
    monkeypatch.setattr(wn, "_is_sabbath", lambda: False)
    _stub_client(monkeypatch, content="Your numbers suggest you have the flu — rest up.")
    assert wn.compose_narrative(1, readiness=READY, night=NIGHT, cross_signals=CROSS) == sentinel


def test_false_health_allclear_falls_back(monkeypatch):
    monkeypatch.setenv("WHOOP_NARRATIVE_LLM", "1")
    sentinel = _stub_rule_based(monkeypatch)
    monkeypatch.setattr(wn, "_is_sabbath", lambda: False)
    _stub_client(monkeypatch, content="Everything's green — you're healthy, push hard today.")
    assert wn.compose_narrative(1, readiness=READY, night=NIGHT, cross_signals=CROSS) == sentinel


# ── ISC-B6: any adapter failure → rule-based, never raises ───────────────────


def test_client_exception_falls_back(monkeypatch):
    monkeypatch.setenv("WHOOP_NARRATIVE_LLM", "1")
    sentinel = _stub_rule_based(monkeypatch)
    monkeypatch.setattr(wn, "_is_sabbath", lambda: False)
    _stub_client(monkeypatch, raises=RuntimeError("all providers down"))
    assert wn.compose_narrative(1, readiness=READY, night=NIGHT, cross_signals=CROSS) == sentinel


def test_empty_output_falls_back(monkeypatch):
    monkeypatch.setenv("WHOOP_NARRATIVE_LLM", "1")
    sentinel = _stub_rule_based(monkeypatch)
    monkeypatch.setattr(wn, "_is_sabbath", lambda: False)
    _stub_client(monkeypatch, content="   ")
    assert wn.compose_narrative(1, readiness=READY, night=NIGHT, cross_signals=CROSS) == sentinel


# ── Sabbath rule: LLM on but Sunday → prescriptive rest line, model untouched ─


def test_sabbath_always_rule_based(monkeypatch):
    monkeypatch.setenv("WHOOP_NARRATIVE_LLM", "1")
    sentinel = _stub_rule_based(monkeypatch)
    monkeypatch.setattr(wn, "_is_sabbath", lambda: True)
    _stub_client(monkeypatch, raises=AssertionError("model must not be called on the Sabbath"))
    assert wn.compose_narrative(1, readiness=READY, night=NIGHT, cross_signals=CROSS) == sentinel


# ── pure helpers ─────────────────────────────────────────────────────────────


def test_passes_honesty_checks():
    assert wn._passes_honesty_checks("HRV's up — green light to push.") is True
    assert wn._passes_honesty_checks("") is False
    assert wn._passes_honesty_checks("   ") is False
    assert wn._passes_honesty_checks("x" * 500) is False
    assert wn._passes_honesty_checks("You likely have a viral infection.") is False
    assert wn._passes_honesty_checks("You're healthy, no worries.") is False


def test_llm_enabled_env_variants(monkeypatch):
    for v in ("1", "true", "on", "YES"):
        monkeypatch.setenv("WHOOP_NARRATIVE_LLM", v)
        assert wn._llm_enabled() is True
    for v in ("", "0", "off", "no"):
        monkeypatch.setenv("WHOOP_NARRATIVE_LLM", v)
        assert wn._llm_enabled() is False


def test_cross_signal_brief_includes_trends():
    brief = wn._build_cross_signal_brief(READY, NIGHT, None, CROSS)
    assert "Resting HR" in brief and "ACWR 1.4" in brief
    assert "amber" in brief  # prevention deviation surfaced, framed as deviation
    assert "Prime" in brief

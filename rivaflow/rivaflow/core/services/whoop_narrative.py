"""NarrativeProvider seam for the WHOOP cockpit's daily data-story (Wave 2.3).

The Bitter-Lesson audit (E1) found the cockpit narrative is a hand-written prose
state machine — it can only combine four readiness states × a sleep shortfall × a
hard workout, and can NEVER notice a three-day resting-HR climb or an ACWR spike
even though those are computed in the same call. The violation isn't the text; it's
that a template is the *only possible* implementation.

This adds the seam. The rule-based composer (`whoop_analytics.daily_narrative`)
stays the deterministic default — with the LLM adapter OFF, `compose_narrative`
returns EXACTLY what it did before. With `WHOOP_NARRATIVE_LLM` on, an LLM adapter
composes the story from the full cross-signal context at snapshot time (a handful
of calls/day, cached in the snapshot), honesty-post-checked. ANY failure or a
failed check falls straight back to the rule-based line — the cockpit can never
break or over-claim because of this.

Honesty rails (audit §6 red-team): the Sabbath always uses the rule-based line
(rest is prescribed — never an LLM push); no medical diagnosis; green ≠ healthy;
one or two sentences only.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from rivaflow.core import whoop_analytics
from rivaflow.core.whoop_analytics import LOCAL_TZ

logger = logging.getLogger(__name__)

_NARRATIVE_SYSTEM_PROMPT = """You write ONE honest, one-to-two-sentence recovery \
data-story for a masters BJJ athlete's dashboard, from his own WHOOP-derived \
numbers. Voice: calm, direct, second person ("you"), no hype, no emoji.

RULES:
- Ground it in the actual numbers you're given. When a cross-signal is notable — \
a multi-day resting-HR climb, an HRV trend, an ACWR spike, a respiratory-rate \
rise — reference it; that's the point of you existing over a template.
- End with a brief training steer that matches the readiness state (push / train \
as planned / ease into technical work / prioritise recovery).
- NEVER diagnose illness or any medical condition. If signals look off, say the \
autonomics look strained and it could be many things — never name a disease.
- A good readiness score means HRV is above his baseline; it does NOT mean \
"healthy" — never say he's healthy.
- Output ONLY the sentence(s). No preamble, no label, no quotes, no markdown."""

# If the model emits any of these it has over-claimed (diagnosis / false health
# reassurance) — reject and fall back to the deterministic line.
_FORBIDDEN_SUBSTRINGS = (
    "diagnos",
    "infection",
    "infected",
    "covid",
    "influenza",
    " flu",
    "virus",
    "disease",
    "arrhythmia",
    "afib",
    "a-fib",
    "atrial fib",
    "you're healthy",
    "you are healthy",
    "perfectly healthy",
    "you're fine",  # false all-clear
)

_MAX_NARRATIVE_CHARS = 400


def _llm_enabled() -> bool:
    return os.getenv("WHOOP_NARRATIVE_LLM", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _is_sabbath() -> bool:
    """Sunday is Ruby's rest day — the Sabbath narrative is prescriptive rest and
    must never be reframed by the model."""
    return datetime.now(LOCAL_TZ).weekday() == 6


def _passes_honesty_checks(text: str) -> bool:
    """Post-generation guard: length-bounded, no diagnosis, no false health all-clear."""
    if not text or not text.strip():
        return False
    if len(text) > _MAX_NARRATIVE_CHARS:
        return False
    low = text.lower()
    return not any(bad in low for bad in _FORBIDDEN_SUBSTRINGS)


def _build_cross_signal_brief(
    readiness: dict, night: dict, last_workout: dict | None, cross: dict
) -> str:
    """Compact, model-readable brief of the signals the template bank can't combine."""
    hrv = cross.get("hrv_ln_trend") or []
    rhr = cross.get("rhr_trend") or []
    prevention = cross.get("prevention") or {}

    parts = [
        f"Readiness: {readiness.get('state')} (score {readiness.get('score')}).",
        (
            f"lnRMSSD last {len(hrv)}d: {[round(v, 2) for v in hrv]}"
            if hrv
            else "HRV baseline still building."
        ),
        f"Resting HR last {len(rhr)}d: {rhr}" if rhr else "Resting-HR trend building.",
    ]
    if night.get("available") and night.get("duration_hours") is not None:
        parts.append(f"Slept {night['duration_hours']}h (need >9h).")
    if cross.get("acwr") is not None:
        parts.append(f"ACWR {cross['acwr']} (acute:chronic load).")
    if cross.get("cardio_today") is not None:
        parts.append(f"Cardio load today {cross['cardio_today']}/21.")
    if cross.get("strain_target") is not None:
        parts.append(f"Strain target {cross['strain_target']}/21.")
    if last_workout:
        parts.append(f"Last session: {last_workout.get('label', 'workout')}.")
    tier = prevention.get("tier")
    if tier in ("amber", "red"):
        parts.append(
            f"Baseline-deviation watch: {tier} — a signal has drifted from baseline "
            "(deviation, NOT a diagnosis)."
        )
    return " ".join(parts)


def compose_narrative(
    user_id: int,
    *,
    readiness: dict,
    night: dict,
    last_workout: dict | None = None,
    cross_signals: dict[str, Any] | None = None,
) -> str:
    """The cockpit narrative seam.

    Returns the deterministic rule-based line (identical to before) unless the LLM
    adapter is enabled AND it produces an honest, in-bounds story from the
    cross-signal context. On the Sabbath, or on any error / failed honesty check,
    the rule-based line is returned — this NEVER raises and NEVER over-claims.
    """
    rule_based = whoop_analytics.daily_narrative(
        user_id, readiness=readiness, night=night, last_workout=last_workout
    )

    if not _llm_enabled():
        return rule_based

    # The Sabbath line is prescriptive rest — never let the model reframe it.
    if _is_sabbath():
        return rule_based

    try:
        from rivaflow.core.services.grapple.llm_client import GrappleLLMClient

        brief = _build_cross_signal_brief(
            readiness, night, last_workout, cross_signals or {}
        )
        messages = [
            {"role": "system", "content": _NARRATIVE_SYSTEM_PROMPT},
            {"role": "user", "content": brief},
        ]
        result = GrappleLLMClient().chat_sync(
            messages, user_id=user_id, temperature=0.5, max_tokens=160
        )
        text = (result.get("content") or "").strip().strip('"')
        if _passes_honesty_checks(text):
            return text
        logger.warning(
            "WHOOP narrative LLM output failed honesty check for user %s; using rule-based",
            user_id,
        )
    except (
        Exception
    ):  # noqa: BLE001 — any adapter failure must degrade, never break the cockpit
        logger.warning(
            "WHOOP narrative LLM adapter failed for user %s; using rule-based",
            user_id,
            exc_info=True,
        )

    return rule_based

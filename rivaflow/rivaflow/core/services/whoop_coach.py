"""WHOOP recovery & readiness coach — server-side, provider-agnostic (Wave 2.1).

The Bitter-Lesson audit (H1/H2) found the phone's coach triple-hardwired to an
*unofficial* OpenAI backend, reasoning over the DEAD on-device Extract scores —
so it could contradict the home screen and never benefited from VPS improvements.

This moves the coach's judgment to the VPS, where it belongs: context is built
from the SAME `whoop_summary` rollup the phone renders (so the coach cites the
numbers Ruby sees), and generation goes through `GrappleLLMClient` — provider and
model are a server config row, so swapping the model is an env edit, no app
rebuild. The phone becomes a dumb chat renderer.

Honesty rails (audit §6 red-team): recovery/readiness guidance only, never a
medical diagnosis, defer to professionals, green ≠ healthy, Sabbath rest is
prescribed. The biometric ceiling is stated (no SpO₂/skin-temp/sleep-staging).
"""

from __future__ import annotations

import logging
from typing import Any

from rivaflow.core import whoop_analytics
from rivaflow.core.services.grapple.llm_client import GrappleLLMClient

logger = logging.getLogger(__name__)

# Recent turns to keep for context (the phone sends the trailing conversation).
_MAX_HISTORY_TURNS = 8

COACH_SYSTEM_PROMPT = """You are Sage's recovery & readiness coach inside RivaFlow \
— the same brain that renders Ruby's WHOOP screen. Ruby is a masters BJJ athlete \
(blue belt, purple-belt goal) who also lifts and does conditioning. You reason \
ONLY over the biometric context you're given, which is derived from his own \
WHOOP 5.0 heart-rate and RR data (self-hosted — no WHOOP subscription).

YOUR JOB:
- Answer readiness / recovery / training-load questions: should I roll hard \
today, is this a deload day, why is my HRV down, how did I sleep, am I \
overreaching. Ground every answer in the specific numbers below.
- Cite his ACTUAL figures (readiness state + score, HRV, resting HR, sleep, \
respiratory rate, cardio load, strain target, ACWR) — never generic advice \
when you have his data. If a number is missing or still building a baseline, \
say so plainly rather than inventing it.
- Read across signals: a resting-HR climb + HRV drop + respiratory-rate rise \
together mean more than any one alone. Point at trends, not just today.
- Be concise and direct (1-3 short paragraphs). Honest, supportive, calm.

HONESTY RAILS (do not break these):
- You are NOT a medical device and NOT a doctor. Never diagnose illness, \
infection, heart conditions, or any disease. If a signal looks off, say the \
autonomics look strained and it could be many things (sleep, stress, alcohol, \
oncoming bug) — and to see a professional for anything concerning. Defer to \
qualified medical professionals for any medical, injury, or safety question.
- "Green / Prime" means his HRV is above his own baseline — it does NOT mean \
"healthy." Don't equate a good readiness score with health.
- On the Sabbath (Sunday, his rest day) rest is prescribed — don't push a \
training target; frame the day as recovery.
- Be honest about the ceiling: this platform computes HRV, resting HR, \
readiness, sleep duration/timing, respiratory rate, cardio load and stress \
from HR+RR. It does NOT measure SpO₂, skin temperature, blood pressure, or \
sleep stages — never claim those.
- Stay in the recovery/readiness/training-load lane. If asked something \
outside it (coding, general knowledge), politely redirect to what you can help \
with: his readiness, recovery, sleep, and training load."""


def _fmt(value: Any, unit: str = "") -> str:
    if value is None:
        return "—"
    return f"{value}{unit}"


def build_coach_context(user_id: int, *, today_is_sabbath: bool = False) -> str:
    """Render the `whoop_summary` rollup — the exact data the phone shows — into a
    compact, model-readable brief. Same source as `/whoop/summary`, so the coach's
    numbers match SlimHomeView to the minute (the Wave 2.1 sunset test)."""
    s = whoop_analytics.whoop_summary(user_id, today_is_sabbath=today_is_sabbath)

    r = s.get("readiness") or {}
    hrv = s.get("hrv_today") or {}
    rhr = s.get("resting_hr_today") or {}
    sleep = s.get("sleep") or {}
    resp = s.get("respiratory_rate") or {}
    cardio = s.get("cardio_load_today") or {}
    strain = s.get("strain_target") or {}
    stress = s.get("stress") or {}
    prevention = s.get("prevention") or {}

    hrv_trend = s.get("hrv_trend") or []
    rhr_trend = s.get("resting_hr_trend") or []
    hrv_pts = " → ".join(str(p.get("rmssd")) for p in hrv_trend[-7:]) or "building"
    rhr_pts = " → ".join(str(p.get("resting_hr")) for p in rhr_trend[-7:]) or "building"

    sleep_line = (
        f"{_fmt(sleep.get('duration_hours'), 'h')} "
        f"(quality {_fmt(sleep.get('quality_score'))}/100)"
        if sleep.get("available")
        else f"no data ({sleep.get('reason', 'not captured')})"
    )

    lines = [
        f"Readiness: {_fmt(r.get('state'))} "
        f"(score {_fmt(r.get('score'))}/100) — {r.get('headline', '')}".strip(),
        f"HRV today: {_fmt(hrv.get('rmssd'), ' ms')} (resting RMSSD); "
        f"last 7 days: {hrv_pts}",
        f"Resting HR today: {_fmt(rhr.get('resting_hr'), ' bpm')}; "
        f"last 7 days: {rhr_pts}",
        f"Sleep last night: {sleep_line} (his need is >9h)",
        f"Respiratory rate: {_fmt(resp.get('respiratory_rate') if resp.get('available') else None, ' rpm')}",
        f"Cardio load today: {_fmt(cardio.get('cardio_load'))}/21",
        f"Strain target today: {_fmt(strain.get('target_load'))}/21 "
        f"({strain.get('headline', '')})".strip(),
        f"ACWR (acute:chronic load): {_fmt(s.get('acwr'))}",
        f"Stress now: {_fmt(stress.get('stress') if stress.get('available') else None)}/100",
    ]

    tier = prevention.get("tier")
    if tier in ("amber", "red"):
        lines.append(
            f"Baseline-deviation watch: {tier.upper()} — "
            f"{prevention.get('headline', 'a signal has drifted from his baseline')} "
            "(a personal safety net; it detects deviation, NEVER diagnoses)"
        )

    if today_is_sabbath:
        lines.append(
            "Today is the Sabbath (Sunday) — his rest day; rest is prescribed."
        )

    return (
        "TODAY'S BIOMETRIC CONTEXT (self-hosted WHOOP, all from HR+RR):\n"
        + "\n".join(f"- {ln}" for ln in lines)
    )


def _sanitize_history(history: list[dict] | None) -> list[dict[str, str]]:
    """Keep only well-formed user/assistant turns, trailing `_MAX_HISTORY_TURNS`."""
    if not history:
        return []
    clean: list[dict[str, str]] = []
    for turn in history:
        role = turn.get("role")
        content = turn.get("content")
        if (
            role in ("user", "assistant")
            and isinstance(content, str)
            and content.strip()
        ):
            clean.append({"role": role, "content": content})
    return clean[-_MAX_HISTORY_TURNS:]


async def answer(
    user_id: int,
    message: str,
    *,
    history: list[dict] | None = None,
    today_is_sabbath: bool = False,
) -> dict[str, Any]:
    """Answer one coach turn over the VPS biometrics. Returns the reply plus the
    provider/model actually used (so the phone can show provenance and so a config
    swap is observable). Raises RuntimeError only when no LLM provider is configured
    or all fail — the route maps that to a graceful message."""
    context = build_coach_context(user_id, today_is_sabbath=today_is_sabbath)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": COACH_SYSTEM_PROMPT},
        {"role": "system", "content": context},
        *_sanitize_history(history),
        {"role": "user", "content": message},
    ]

    client = GrappleLLMClient()
    result = await client.chat(messages, user_id=user_id, max_tokens=700)
    return {
        "reply": result["content"],
        "provider": result.get("provider"),
        "model": result.get("model"),
        "tokens": result.get("total_tokens"),
    }

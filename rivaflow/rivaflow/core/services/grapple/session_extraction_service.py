"""Service for extracting structured session data from text."""

import json
import logging
import re

from rivaflow.core.services.grapple.llm_client import (
    GrappleLLMClient,
)

logger = logging.getLogger(__name__)

# MA-F4: a voice "nogi" stored verbatim was silently excluded from Game
# Distribution and every class-type filter (canonical enum says "no-gi").
# Normalize every historical LLM spelling onto the ClassType enum; "private"
# doesn't exist in the enum — a private is a gi lesson unless stated otherwise.
_CLASS_TYPE_ALIASES = {
    "gi": "gi",
    "no-gi": "no-gi",
    "nogi": "no-gi",
    "no gi": "no-gi",
    "no_gi": "no-gi",
    "open-mat": "open-mat",
    "open_mat": "open-mat",
    "open mat": "open-mat",
    "openmat": "open-mat",
    "drilling": "drilling",
    "competition": "competition",
    "comp": "competition",
    "private": "gi",
    "s&c": "s&c",
    "cardio": "cardio",
    "mobility": "mobility",
}


def normalize_class_type(raw: str | None) -> str:
    """Canonical ClassType value for any extraction spelling; unknown → 'gi'."""
    if not raw:
        return "gi"
    return _CLASS_TYPE_ALIASES.get(raw.strip().lower(), "gi")


def _fold(name: str) -> str:
    """Case/punctuation-insensitive key for movement matching."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def resolve_movements(names: list[str]) -> tuple[list[dict], list[str]]:
    """Resolve technique names to glossary movements (MA-F4).

    Matching order per name: exact folded name, then folded alias. Returns
    (resolved [{movement_id, name, matched}], unresolved [original strings]).
    Never guesses: an unmatched name stays a free string, it does not get the
    closest ID.
    """
    from rivaflow.db.repositories import GlossaryRepository

    movements = GlossaryRepository.list_all()
    by_name: dict[str, dict] = {}
    by_alias: dict[str, dict] = {}
    for m in movements:
        by_name[_fold(m["name"])] = m
        raw_aliases = m.get("aliases")
        if isinstance(raw_aliases, str):
            try:
                raw_aliases = json.loads(raw_aliases)
            except (ValueError, TypeError):
                raw_aliases = []
        for alias in raw_aliases or []:
            by_alias.setdefault(_fold(str(alias)), m)

    resolved: list[dict] = []
    unresolved: list[str] = []
    seen_ids: set[int] = set()
    for name in names:
        key = _fold(name)
        if not key:
            continue
        match = by_name.get(key) or by_alias.get(key)
        if match is None:
            unresolved.append(name)
        elif match["id"] not in seen_ids:
            seen_ids.add(match["id"])
            resolved.append(
                {"movement_id": match["id"], "name": match["name"], "matched": name}
            )
    return resolved, unresolved


EXTRACTION_SYSTEM_PROMPT = """\
You are a BJJ training session parser. \
Extract structured data from the user's natural language \
description of their training session.

Return a JSON object with these fields:
{
  "session_date": "YYYY-MM-DD or null",
  "class_type": "gi|no-gi|open-mat|drilling|competition",
  "gym_name": "string or null",
  "duration_mins": number or 60,
  "intensity": 1-5 or 3,
  "rolls": number or 0,
  "submissions_for": number or 0,
  "submissions_against": number or 0,
  "partners": ["name1", "name2"] or [],
  "techniques": ["technique1", "technique2"] or [],
  "notes": "string summary",
  "events": [
    {
      "event_type": "technique|submission|sweep|pass|escape|takedown",
      "technique_name": "string",
      "position": "string or null",
      "outcome": "success|fail|attempted",
      "partner_name": "string or null"
    }
  ]
}

Only return valid JSON. Do not include markdown code fences."""


async def extract_session_from_text(text: str, user_id: int) -> dict:
    """Parse natural language into structured session data.

    Args:
        text: Natural language session description
        user_id: User ID for LLM call

    Returns:
        Parsed session data dict
    """
    try:
        client = GrappleLLMClient(environment="production")
    except RuntimeError:
        logger.error("No LLM providers available")
        raise

    messages = [
        {
            "role": "system",
            "content": EXTRACTION_SYSTEM_PROMPT,
        },
        {"role": "user", "content": text},
    ]

    result = await client.chat(
        messages=messages,
        user_id=user_id,
        temperature=0.1,
        max_tokens=1024,
    )

    content = result["content"].strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        content = "\n".join(lines)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM extraction response")
        parsed = {
            "notes": text,
            "events": [],
            "parse_error": True,
        }

    parsed["_llm_tokens"] = result.get("total_tokens", 0)
    parsed["_llm_cost"] = result.get("cost_usd", 0.0)
    return parsed  # type: ignore[no-any-return]

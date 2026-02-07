"""Service for extracting structured session data from text."""

import json
import logging

from rivaflow.core.services.grapple.llm_client import (
    GrappleLLMClient,
)

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """\
You are a BJJ training session parser. \
Extract structured data from the user's natural language \
description of their training session.

Return a JSON object with these fields:
{
  "session_date": "YYYY-MM-DD or null",
  "class_type": "gi|nogi|open_mat|drilling|private|competition",
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
    return parsed

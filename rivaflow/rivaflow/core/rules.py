"""Transparent suggestion rules (not AI)."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Rule:
    """A suggestion rule with condition and recommendation."""

    name: str
    condition: Callable  # Returns bool
    recommendation: str
    explanation: str
    priority: int  # Lower = higher priority


# Context object structure expected by rules:
# - readiness: dict with sleep, stress, soreness, energy, hotspot_note, composite_score
# - session_context: dict with consecutive_gi_sessions, consecutive_nogi_sessions,
#                    stale_techniques (list of dicts)


RULES = [
    Rule(
        name="high_stress_low_energy",
        condition=lambda r, s: r and r["stress"] >= 4 and r["energy"] <= 2,
        recommendation="Flow roll or drill-only",
        explanation="High stress ({stress}/5) + low energy ({energy}/5) → protect recovery",
        priority=1,
    ),
    Rule(
        name="high_soreness",
        condition=lambda r, s: r and r["soreness"] >= 4,
        recommendation="Recovery day: mobility or drilling only",
        explanation="Soreness elevated ({soreness}/5) → avoid intensity",
        priority=1,
    ),
    Rule(
        name="hotspot_active",
        condition=lambda r, s: r and r.get("hotspot_note") is not None,
        recommendation="Protect {hotspot} — avoid positions that stress it",
        explanation="Active hotspot: {hotspot}",
        priority=2,
    ),
    Rule(
        name="consecutive_gi",
        condition=lambda r, s: s["consecutive_gi_sessions"] >= 3,
        recommendation="Train No-Gi today",
        explanation="{consecutive_gi} consecutive Gi sessions → unload grips",
        priority=3,
    ),
    Rule(
        name="consecutive_nogi",
        condition=lambda r, s: s["consecutive_nogi_sessions"] >= 3,
        recommendation="Train Gi today",
        explanation="{consecutive_nogi} consecutive No-Gi sessions → vary stimulus",
        priority=3,
    ),
    Rule(
        name="green_light",
        condition=lambda r, s: r and r["composite_score"] >= 16 and r["soreness"] <= 2,
        recommendation="Go hard — you're recovered",
        explanation="Readiness {score}/20, low soreness → full intensity available",
        priority=4,
    ),
    Rule(
        name="stale_technique",
        condition=lambda r, s: len(s.get("stale_techniques", [])) > 0,
        recommendation="Revisit: {techniques}",
        explanation="Not trained in 7+ days: {techniques}",
        priority=5,
    ),
]


def format_explanation(explanation: str, readiness: dict, session_context: dict) -> str:
    """Format explanation string with context values."""
    # Build replacement dict
    replacements = {}

    if readiness:
        replacements.update(
            {
                "stress": readiness["stress"],
                "energy": readiness["energy"],
                "soreness": readiness["soreness"],
                "score": readiness["composite_score"],
                "hotspot": readiness.get("hotspot_note", ""),
            }
        )

    replacements.update(
        {
            "consecutive_gi": session_context.get("consecutive_gi_sessions", 0),
            "consecutive_nogi": session_context.get("consecutive_nogi_sessions", 0),
        }
    )

    # Format stale techniques
    stale = session_context.get("stale_techniques", [])
    if stale:
        tech_names = [t["name"] for t in stale[:3]]  # Limit to 3
        replacements["techniques"] = ", ".join(tech_names)

    # Replace placeholders
    result = explanation
    for key, value in replacements.items():
        result = result.replace(f"{{{key}}}", str(value))

    return result

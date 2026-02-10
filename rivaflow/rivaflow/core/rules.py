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
        condition=lambda r, s: r and bool(r.get("hotspot_note")),
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
        name="whoop_low_recovery",
        condition=lambda r, s: (
            r
            and r.get("whoop_recovery_score") is not None
            and r["whoop_recovery_score"] < 34
        ),
        recommendation="WHOOP shows low recovery ({whoop_recovery}%). Consider a light session.",
        explanation="WHOOP recovery score is {whoop_recovery}% — body needs rest",
        priority=2,
    ),
    Rule(
        name="whoop_hrv_drop",
        condition=lambda r, s: (
            s.get("hrv_drop_pct") is not None and s["hrv_drop_pct"] > 20
        ),
        recommendation="Your HRV has dropped significantly. Listen to your body today.",
        explanation="HRV is {hrv_drop_pct}% below your 7-day average",
        priority=3,
    ),
    Rule(
        name="whoop_hrv_sustained_decline",
        condition=lambda r, s: (
            s.get("hrv_slope_5d") is not None and s["hrv_slope_5d"] < -0.5
        ),
        recommendation=(
            "Your HRV has been declining for 5+ days." " Prioritize sleep and recovery."
        ),
        explanation=(
            "HRV slope over last 5+ days is {hrv_slope_5d}"
            " — sustained decline detected"
        ),
        priority=2,
    ),
    Rule(
        name="stale_technique",
        condition=lambda r, s: len(s.get("stale_techniques", [])) > 0,
        recommendation="Revisit: {techniques}",
        explanation="Not trained in 7+ days: {techniques}",
        priority=5,
    ),
    Rule(
        name="whoop_green_recovery",
        condition=lambda r, s: (
            r
            and r.get("whoop_recovery_score") is not None
            and r["whoop_recovery_score"] >= 90
        ),
        recommendation="WHOOP shows peak recovery ({whoop_recovery}%). Great day to push hard!",
        explanation="WHOOP recovery at {whoop_recovery}% — fully recovered",
        priority=8,
    ),
    # ── Mode-aware rules ──
    Rule(
        name="comp_fight_week",
        condition=lambda r, s: (
            s.get("training_mode") == "competition_prep"
            and s.get("days_until_comp") is not None
            and s["days_until_comp"] <= 7
            and s["days_until_comp"] >= 0
        ),
        recommendation="Fight week — light technical work and visualization only",
        explanation="Competition in {days_until_comp} days. Preserve energy.",
        priority=0,
    ),
    Rule(
        name="comp_taper_warning",
        condition=lambda r, s: (
            s.get("training_mode") == "competition_prep"
            and s.get("days_until_comp") is not None
            and 7 < s["days_until_comp"] <= 14
        ),
        recommendation=(
            "Begin tapering intensity — {days_until_comp} days to competition"
        ),
        explanation=(
            "Competition approaching. Start reducing volume while "
            "maintaining sharpness."
        ),
        priority=1,
    ),
    Rule(
        name="recovery_mode_active",
        condition=lambda r, s: s.get("training_mode") == "recovery",
        recommendation="Recovery mode active — keep intensity low, focus on mobility",
        explanation="You're in recovery mode. All sessions should be light.",
        priority=1,
    ),
    Rule(
        name="persistent_injuries",
        condition=lambda r, s: len(s.get("persistent_injuries", [])) > 0,
        recommendation="Protect injuries: {injury_areas}",
        explanation="Active injuries: {injury_areas} — avoid aggravating positions",
        priority=2,
    ),
    # ── Load management rules ──
    Rule(
        name="rest_after_high_intensity",
        condition=lambda r, s: (
            s.get("last_session_intensity") is not None
            and s["last_session_intensity"] >= 5
            and s.get("days_since_last_session") is not None
            and s["days_since_last_session"] == 0
        ),
        recommendation="Back-to-back after a max-intensity session — consider a lighter day",
        explanation=(
            "Yesterday's session was intensity {last_intensity}/5. "
            "A recovery or technical session today protects gains."
        ),
        priority=2,
    ),
    Rule(
        name="deload_week",
        condition=lambda r, s: (
            s.get("sessions_this_week") is not None and s["sessions_this_week"] >= 6
        ),
        recommendation="High volume this week ({sessions_week} sessions) — consider a deload",
        explanation=(
            "{sessions_week} sessions this week. Deload weeks "
            "prevent overuse injuries and allow supercompensation."
        ),
        priority=1,
    ),
    Rule(
        name="session_frequency_low",
        condition=lambda r, s: (
            s.get("days_since_last_session") is not None
            and s["days_since_last_session"] >= 5
        ),
        recommendation="It's been {days_off} days — ease back in with drilling or flow rolls",
        explanation=(
            "{days_off} days since your last session. "
            "Warm up carefully and avoid jumping straight to hard sparring."
        ),
        priority=3,
    ),
    Rule(
        name="sleep_debt_high",
        condition=lambda r, s: (
            s.get("sleep_debt_min") is not None and s["sleep_debt_min"] >= 120
        ),
        recommendation=(
            "Sleep debt is high ({sleep_debt}h). "
            "Prioritize sleep over training today."
        ),
        explanation=(
            "Accumulated sleep debt of {sleep_debt}h. "
            "Training on poor sleep increases injury risk and impairs learning."
        ),
        priority=2,
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
                "hotspot": readiness.get("hotspot_note") or "the affected area",
                "whoop_recovery": readiness.get("whoop_recovery_score", ""),
            }
        )

    hrv_slope = session_context.get("hrv_slope_5d")
    replacements.update(
        {
            "consecutive_gi": session_context.get("consecutive_gi_sessions", 0),
            "consecutive_nogi": session_context.get("consecutive_nogi_sessions", 0),
            "hrv_drop_pct": session_context.get("hrv_drop_pct", ""),
            "hrv_slope_5d": (f"{hrv_slope:+.2f}" if hrv_slope is not None else ""),
            "days_until_comp": session_context.get("days_until_comp", ""),
        }
    )

    # Format stale techniques
    stale = session_context.get("stale_techniques", [])
    if stale:
        tech_names = [t["name"] for t in stale[:3]]  # Limit to 3
        replacements["techniques"] = ", ".join(tech_names)

    # Format persistent injuries
    injuries = session_context.get("persistent_injuries", [])
    if injuries:
        areas = [inj.get("area", "unknown") for inj in injuries[:3]]
        replacements["injury_areas"] = ", ".join(areas)

    # Load management replacements
    replacements["last_intensity"] = session_context.get("last_session_intensity", "")
    replacements["sessions_week"] = session_context.get("sessions_this_week", "")
    replacements["days_off"] = session_context.get("days_since_last_session", "")
    sleep_debt_min = session_context.get("sleep_debt_min")
    replacements["sleep_debt"] = (
        f"{sleep_debt_min / 60:.1f}" if sleep_debt_min is not None else ""
    )

    # Replace placeholders
    result = explanation
    for key, value in replacements.items():
        result = result.replace(f"{{{key}}}", str(value))

    return result

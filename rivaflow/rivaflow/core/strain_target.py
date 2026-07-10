"""B5 — Strain Target / Load Coach (the pure core).

WHOOP's signature loop: turn today's readiness into a prescribed daily strain (0–21) and CAP it when the
body is strained, so load never outruns recovery (WHOOP_FUTURE_STATE_PLAN.md B5). Tuned conservative for a
masters, NSAID-sensitive, low-endurance grappler — a Strained/Rundown day prescribes a target BELOW his usual
chronic load, not just "a bit less."

Depends on B1: the 0–21 strain scale is only meaningful once HR zones use the calibrated max-HR, not the old
190. Pure and DB-free; the wiring feeds it today's readiness state + recent cardio-load history.
"""

from __future__ import annotations

from dataclasses import dataclass

STRAIN_CAP = 21.0
DEFAULT_CHRONIC = (
    10.0  # neutral base when there's no load history yet (mid of the 0–21 scale)
)
BAND_WIDTH = 2.0  # target band half-width either side of target_load

# Readiness state → fraction of the chronic (usual) daily load to prescribe. <1.0 = an explicit cap.
# This is the DEFAULT policy's multiplier table — see StrainPolicy below.
STATE_MULTIPLIER = {
    "Prime": 1.15,  # recovered — a little above usual is safe
    "Balanced": 1.0,  # train as planned
    "Strained": 0.6,  # ease off — technical work
    "Rundown": 0.4,  # recovery day
}

# States that don't get a target at all.
NO_TARGET_STATES = {"Rest", "Building", None}

# ── Strain prescription policy — the swappable seam ────────────────────────
# The per-state multipliers, cap and band width are bundled into one versioned
# model rather than frozen as bare constants welded into prescribe_strain(),
# mirroring readiness.py's ReadinessModel / set_readiness_model() seam. The
# default is the hand-tuned STATE_MULTIPLIER heuristic; a measured
# dose-response fit (rivaflow.core.strain_fit) can replace it at runtime via
# set_strain_policy() with NO change to prescribe_strain, and every
# prescription carries `policy_version` so it's attributable to (and
# re-derivable from) the policy that produced it.


@dataclass(frozen=True)
class StrainPolicy:
    """A swappable strain-prescription policy: per-state load multipliers, the
    strain cap and target-band half-width, plus a version stamp. Defaults to
    the hand-tuned heuristic; ``set_strain_policy`` is the seam a fitted
    dose-response policy plugs into without touching ``prescribe_strain``.
    """

    version: str
    multipliers: dict[str, float]
    cap: float = STRAIN_CAP
    band_width: float = BAND_WIDTH


_DEFAULT_POLICY = StrainPolicy(
    version="strain-heuristic-v1", multipliers=dict(STATE_MULTIPLIER)
)
_active_policy = _DEFAULT_POLICY


def get_strain_policy() -> StrainPolicy:
    """The policy ``prescribe_strain`` currently prescribes with."""
    return _active_policy


def set_strain_policy(policy: StrainPolicy | None) -> None:
    """Swap the active strain policy (``None`` restores the default heuristic).

    The seam for a fitted dose-response policy (see ``rivaflow.core.strain_fit``)
    — no edit to ``prescribe_strain`` needed. Also the reset-for-tests hook:
    call with no argument (or ``None``) to snap back to the heuristic.
    """
    global _active_policy
    _active_policy = policy or _DEFAULT_POLICY


def prescribe_strain(
    state: str | None, chronic_load: float | None, acute_load: float | None = None
) -> dict:
    """Prescribe today's strain target from readiness `state` and the athlete's `chronic_load` (usual daily
    strain). `acute_load` = today's strain so far, if known, to report headroom. Returns available=False for
    Rest/Building/unknown states."""
    if state in NO_TARGET_STATES:
        reason = (
            "Sabbath — rest is prescribed."
            if state == "Rest"
            else "Building your baseline — no strain target yet."
        )
        return {"available": False, "state": state, "reason": reason}

    assert state is not None  # narrowed by the NO_TARGET_STATES guard above
    policy = get_strain_policy()
    mult = policy.multipliers.get(state)
    if mult is None:
        return {
            "available": False,
            "state": state,
            "reason": f"No strain policy for state '{state}'.",
        }

    base = chronic_load if (chronic_load and chronic_load > 0) else DEFAULT_CHRONIC
    target = round(min(policy.cap, base * mult), 1)
    band = [
        round(max(0.0, target - policy.band_width), 1),
        round(min(policy.cap, target + policy.band_width), 1),
    ]
    capped = mult < 1.0

    headlines = {
        "Prime": f"Recovered — you can push. Target strain {target}.",
        "Balanced": f"Train as planned. Target strain {target}.",
        "Strained": f"Ease off — capped at {target}, below your usual {round(base, 1)}.",
        "Rundown": f"Recovery day — keep it light, max {target}.",
    }

    out = {
        "available": True,
        "state": state,
        "target_load": target,
        "band": band,
        "capped": capped,
        "chronic_load": round(base, 1),
        "headline": headlines[state],
        "policy_version": policy.version,
    }
    if acute_load is not None:
        out["acute_load"] = round(acute_load, 1)
        out["remaining"] = round(max(0.0, target - acute_load), 1)
        if acute_load >= target:
            out["headline"] = f"You've hit today's target ({target}) — " + (
                "recover now." if capped else "more only if you feel good."
            )
    return out

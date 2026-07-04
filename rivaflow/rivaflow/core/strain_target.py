"""B5 — Strain Target / Load Coach (the pure core).

WHOOP's signature loop: turn today's readiness into a prescribed daily strain (0–21) and CAP it when the
body is strained, so load never outruns recovery (WHOOP_FUTURE_STATE_PLAN.md B5). Tuned conservative for a
masters, NSAID-sensitive, low-endurance grappler — a Strained/Rundown day prescribes a target BELOW his usual
chronic load, not just "a bit less."

Depends on B1: the 0–21 strain scale is only meaningful once HR zones use the calibrated max-HR, not the old
190. Pure and DB-free; the wiring feeds it today's readiness state + recent cardio-load history.
"""

from __future__ import annotations

STRAIN_CAP = 21.0
DEFAULT_CHRONIC = 10.0   # neutral base when there's no load history yet (mid of the 0–21 scale)

# Readiness state → fraction of the chronic (usual) daily load to prescribe. <1.0 = an explicit cap.
STATE_MULTIPLIER = {
    "Prime": 1.15,       # recovered — a little above usual is safe
    "Balanced": 1.0,     # train as planned
    "Strained": 0.6,     # ease off — technical work
    "Rundown": 0.4,      # recovery day
}

# States that don't get a target at all.
NO_TARGET_STATES = {"Rest", "Building", None}


def prescribe_strain(state: str | None, chronic_load: float | None, acute_load: float | None = None) -> dict:
    """Prescribe today's strain target from readiness `state` and the athlete's `chronic_load` (usual daily
    strain). `acute_load` = today's strain so far, if known, to report headroom. Returns available=False for
    Rest/Building/unknown states."""
    if state in NO_TARGET_STATES:
        reason = ("Sabbath — rest is prescribed." if state == "Rest"
                  else "Building your baseline — no strain target yet.")
        return {"available": False, "state": state, "reason": reason}

    mult = STATE_MULTIPLIER.get(state)
    if mult is None:
        return {"available": False, "state": state, "reason": f"No strain policy for state '{state}'."}

    base = chronic_load if (chronic_load and chronic_load > 0) else DEFAULT_CHRONIC
    target = round(min(STRAIN_CAP, base * mult), 1)
    band = [round(max(0.0, target - 2.0), 1), round(min(STRAIN_CAP, target + 2.0), 1)]
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
    }
    if acute_load is not None:
        out["acute_load"] = round(acute_load, 1)
        out["remaining"] = round(max(0.0, target - acute_load), 1)
        if acute_load >= target:
            out["headline"] = (f"You've hit today's target ({target}) — "
                               + ("recover now." if capped else "more only if you feel good."))
    return out

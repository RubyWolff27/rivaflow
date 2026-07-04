"""B17 — Circadian / chronotype rhythm (pure core).

Cosinor fit of time-of-day HR/HRV (WHOOP_FUTURE_STATE_PLAN.md B17): mesor, amplitude, acrophase + the
nocturnal HR dip — reproducible from HR timing, relevant to Ruby's fixed >9h need and Sabbath rhythm.
"""

from __future__ import annotations

from math import atan2, cos, pi, sin
from statistics import mean

OMEGA = 2 * pi / 24.0  # one cycle per 24h


def cosinor(hours: list[float], values: list[float]) -> dict:
    """Least-squares cosinor: value ≈ M + A·cos(ω(t − φ)). Returns mesor M, amplitude A, and acrophase φ
    (hour of peak). Needs points spread across the day."""
    n = len(hours)
    if n < 8 or len(values) != n:
        return {
            "available": False,
            "reason": "Need ≥8 time-stamped points across the day.",
        }
    # Regress y = M + b·cos(ωt) + c·sin(ωt) via normal equations (closed form).
    cs = [cos(OMEGA * h) for h in hours]
    sn = [sin(OMEGA * h) for h in hours]
    m_y = mean(values)
    m_c = mean(cs)
    m_s = mean(sn)
    # centred sums
    scc = sum((c - m_c) ** 2 for c in cs)
    sss = sum((s - m_s) ** 2 for s in sn)
    scs = sum((c - m_c) * (s - m_s) for c, s in zip(cs, sn))
    scy = sum((c - m_c) * (y - m_y) for c, y in zip(cs, values))
    ssy = sum((s - m_s) * (y - m_y) for s, y in zip(sn, values))
    det = scc * sss - scs * scs
    if det == 0:
        return {
            "available": False,
            "reason": "Time points too clustered to fit a rhythm.",
        }
    b = (scy * sss - ssy * scs) / det
    c = (ssy * scc - scy * scs) / det
    mesor = m_y - b * m_c - c * m_s
    amplitude = (b * b + c * c) ** 0.5
    acrophase_hour = (atan2(c, b) / OMEGA) % 24.0
    return {
        "available": True,
        "mesor": round(mesor, 1),
        "amplitude": round(amplitude, 1),
        "acrophase_hour": round(acrophase_hour, 1),
        "n": n,
        "headline": f"Daily HR rhythm peaks around {round(acrophase_hour, 1)}h, amplitude {round(amplitude, 1)} bpm.",
    }

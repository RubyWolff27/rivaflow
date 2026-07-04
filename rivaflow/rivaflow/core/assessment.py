"""B19 — Weekly + Monthly Assessment (pure core).

A narrative of what's improving/declining (WHOOP_FUTURE_STATE_PLAN.md B19), from the metric trends. Each
metric declares whether "up" is good, so the narrative reads correctly (rising RHR is bad; rising HRV is good).
"""

from __future__ import annotations

from statistics import mean

# metric key → (label, is_up_good)
METRIC_SENSE = {
    "lnrmssd": ("HRV (lnRMSSD)", True),
    "rhr": ("Resting HR", False),
    "cardio_load": ("Training load", True),   # neutral-ish, framed as trend
    "sleep_hours": ("Sleep duration", True),
}


def _direction(values: list[float]) -> float:
    """Slope sign of a simple first-vs-second-half comparison — robust to noise, no regression needed."""
    if len(values) < 4:
        return 0.0
    half = len(values) // 2
    return mean(values[half:]) - mean(values[:half])


def period_assessment(label: str, series: dict[str, list[float]]) -> dict:
    """Summarise a period (e.g. 'week', 'month'). `series` maps metric key → chronological values."""
    lines: list[dict] = []
    for key, values in series.items():
        if key not in METRIC_SENSE or len(values) < 4:
            continue
        name, up_good = METRIC_SENSE[key]
        delta = _direction(values)
        if abs(delta) < 1e-9:
            trend, good = "steady", None
        else:
            rising = delta > 0
            trend = "rising" if rising else "falling"
            good = (rising == up_good)
        lines.append({"metric": key, "label": name, "trend": trend, "delta": round(delta, 2),
                      "improving": good})
    improving = [line["label"] for line in lines if line["improving"] is True]
    declining = [line["label"] for line in lines if line["improving"] is False]
    if not lines:
        headline = f"Not enough data for a {label} assessment yet."
    else:
        parts = []
        if improving:
            parts.append("improving: " + ", ".join(improving))
        if declining:
            parts.append("watch: " + ", ".join(declining))
        headline = f"Your {label}: " + ("; ".join(parts) if parts else "steady across the board.")
    return {"available": bool(lines), "period": label, "lines": lines,
            "improving": improving, "declining": declining, "headline": headline}

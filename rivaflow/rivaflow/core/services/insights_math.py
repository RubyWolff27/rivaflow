"""Pure-Python math helpers for insights analytics.

Pearson r, EWMA, Shannon entropy, linear slope.
No external dependencies (no numpy).
"""

import math
import statistics


def _pearson_r(xs: list[float], ys: list[float]) -> float:
    """Compute Pearson correlation coefficient. Returns 0 if insufficient data."""
    n = len(xs)
    if n < 3 or len(ys) != n:
        return 0.0
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return round(num / (denom_x * denom_y), 3)


def _ewma(values: list[float], span: int) -> list[float]:
    """Exponentially weighted moving average."""
    if not values:
        return []
    alpha = 2.0 / (span + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return [round(r, 2) for r in result]


def _shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy normalized to 0-100 scale."""
    total = sum(counts)
    if total == 0 or len(counts) <= 1:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    raw = -sum(p * math.log2(p) for p in probs)
    max_entropy = math.log2(len(probs))
    if max_entropy == 0:
        return 0.0
    return round((raw / max_entropy) * 100, 1)


def _linear_slope(ys: list[float]) -> float:
    """Simple linear regression slope over index 0..n-1."""
    n = len(ys)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2.0
    mean_y = statistics.mean(ys)
    num = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(ys))
    denom = sum((i - mean_x) ** 2 for i in range(n))
    if denom == 0:
        return 0.0
    return round(num / denom, 4)

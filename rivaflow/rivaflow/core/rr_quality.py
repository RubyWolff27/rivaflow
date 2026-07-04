"""B0 — RR/HR signal characterisation & quality gate.

The foundation build every RR-derived metric consumes (WHOOP_FUTURE_STATE_PLAN.md B0).

Our RR series is *optical pulse-to-pulse intervals* emitted by WHOOP's firmware over the standard 0x2A37
field — NOT ECG RR — and the raw optical waveform needed for an independent signal-quality index is the
locked R22 stream (WHOOP_CURRENT_STATE.md §2). So we inherit WHOOP's beat-detection artifact (pulse-transit
jitter, missed/extra beats, benign ectopy) with no waveform to gate on. This module is the best defence we
can build from the interval series alone:

  1. Physiological band filter — widened for a bradycardic athlete (36–133 bpm; the old 40–90 band clipped
     genuine slow nocturnal beats and biased RMSSD downward).
  2. Malik-style *relative* successive filter — flag an interval differing >20% from the preceding valid
     one (the old absolute <400 ms drop let single-ectopic jumps through, inflating RMSSD).
  3. Ectopy correction by linear interpolation of isolated flagged beats.
  4. Per-series artifact-% + a usability gate, reported alongside every downstream value so trust is visible.

RMSSD is exquisitely sensitive to a single mis-detected beat, so this gate is not optional polish — it is
what makes the readiness / prevention signals trustworthy. lnRMSSD and the baseline math live in B2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import log, sqrt

# --- Quality-gate constants (WHOOP_CURRENT_STATE.md §3 limitations + WHOOP_FUTURE_STATE_PLAN.md B0) ---
RR_MIN_MS = 450                 # 133 bpm — upper HR bound of a plausible resting/nocturnal beat
RR_MAX_MS = 1667                # ~36 bpm — widened for nocturnal bradycardia (was 1500 ms / 40 bpm, too tight)
MALIK_REL_THRESHOLD = 0.20      # flag RR differing >20% from the preceding valid interval (relative, not absolute)
MAX_ARTIFACT_FRACTION = 0.30    # a series with >30% flagged intervals is not trustworthy for HRV
MIN_CLEAN_INTERVALS = 20        # minimum corrected intervals for a valid HRV window
MIN_CLEAN_SEGMENT = 30          # minimum contiguous clean run to count as a usable segment


@dataclass
class RRQuality:
    """Result of the QC gate over one RR series. `cleaned` is the artifact-corrected series that downstream
    metrics consume; `artifact_pct` travels with every value they emit."""

    cleaned: list[float] = field(default_factory=list)   # band-valid + interpolated intervals (ms)
    artifact_pct: float = 100.0                           # % of raw intervals flagged (band + relative)
    n_raw: int = 0
    n_flagged: int = 0
    corrected_idx: list[int] = field(default_factory=list)  # indices in `cleaned` replaced by interpolation
    usable: bool = False                                  # enough clean data AND artifact_pct within budget

    def as_meta(self) -> dict:
        """Compact provenance dict to attach to any metric computed from this series."""
        return {
            "artifact_pct": round(self.artifact_pct, 1),
            "intervals_used": len(self.cleaned),
            "corrected": len(self.corrected_idx),
            "usable": self.usable,
        }


def assess_rr(intervals: list[int | float]) -> RRQuality:
    """Characterise and clean an RR series: physiological-band + Malik relative filtering, then linear
    interpolation of isolated flagged beats. Returns the corrected series, the artifact fraction, and a
    usability verdict. Deterministic and side-effect free — safe to call anywhere upstream of an HRV metric."""
    raw = [float(x) for x in intervals if x is not None]
    n_raw = len(raw)
    if n_raw == 0:
        return RRQuality(cleaned=[], artifact_pct=100.0, n_raw=0, n_flagged=0, usable=False)

    # Pass 1 — band filter, then Malik relative filter against the last accepted interval.
    # flagged[i] is True when raw[i] is out-of-band or a >20% jump from the last valid beat.
    flagged = [False] * n_raw
    last_valid: float | None = None
    for i, rr in enumerate(raw):
        if not (RR_MIN_MS <= rr <= RR_MAX_MS):
            flagged[i] = True
            continue
        if last_valid is not None and abs(rr - last_valid) / last_valid > MALIK_REL_THRESHOLD:
            flagged[i] = True
            continue
        last_valid = rr

    n_flagged = sum(flagged)
    artifact_pct = 100.0 * n_flagged / n_raw

    # Pass 2 — build the corrected series by interpolating isolated flagged beats between valid neighbours.
    # A flagged run with no valid neighbour on a side (series edge, or a long dropout) is discarded, which
    # naturally breaks the series at true gaps rather than fabricating beats across them.
    cleaned: list[float] = []
    corrected_idx: list[int] = []
    i = 0
    while i < n_raw:
        if not flagged[i]:
            cleaned.append(raw[i])
            i += 1
            continue
        # start of a flagged run [i, j)
        j = i
        while j < n_raw and flagged[j]:
            j += 1
        prev_valid = cleaned[-1] if cleaned else None
        next_valid = raw[j] if j < n_raw else None
        if prev_valid is not None and next_valid is not None:
            gap = j - i
            step = (next_valid - prev_valid) / (gap + 1)
            for k in range(1, gap + 1):
                corrected_idx.append(len(cleaned))
                cleaned.append(prev_valid + step * k)
        # else: edge/long-dropout flagged run — drop it (segment boundary)
        i = j

    usable = len(cleaned) >= MIN_CLEAN_INTERVALS and artifact_pct <= MAX_ARTIFACT_FRACTION * 100.0
    return RRQuality(
        cleaned=cleaned,
        artifact_pct=artifact_pct,
        n_raw=n_raw,
        n_flagged=n_flagged,
        corrected_idx=corrected_idx,
        usable=usable,
    )


def clean_segments(intervals: list[int | float], min_len: int = MIN_CLEAN_SEGMENT) -> list[list[float]]:
    """Split an RR series into contiguous in-band, low-jump segments of at least `min_len` intervals —
    the windows a frequency-domain or non-linear metric (B4) may run on. Unlike `assess_rr` this does NOT
    interpolate; it returns only genuinely contiguous clean runs so no fabricated beat enters a spectral window."""
    raw = [float(x) for x in intervals if x is not None]
    segments: list[list[float]] = []
    cur: list[float] = []
    last_valid: float | None = None
    for rr in raw:
        in_band = RR_MIN_MS <= rr <= RR_MAX_MS
        small_jump = last_valid is None or abs(rr - last_valid) / last_valid <= MALIK_REL_THRESHOLD
        if in_band and small_jump:
            cur.append(rr)
            last_valid = rr
        else:
            if len(cur) >= min_len:
                segments.append(cur)
            cur = []
            last_valid = None
    if len(cur) >= min_len:
        segments.append(cur)
    return segments


def rmssd(intervals: list[int | float]) -> float | None:
    """RMSSD (ms) = sqrt(mean of squared successive differences). Expects an already-cleaned series
    (call `assess_rr` first). Returns None if there are too few intervals to form a difference set."""
    vals = [float(x) for x in intervals if x is not None]
    if len(vals) < 2:
        return None
    diffs = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    return sqrt(sum(d * d for d in diffs) / len(diffs))


def ln_rmssd(intervals: list[int | float]) -> float | None:
    """lnRMSSD — the log-transformed RMSSD that B2's baseline z-scores run on (RMSSD is right-skewed, so
    Gaussian stats belong on the log scale; Plews/Buchheit). Returns None if RMSSD is undefined or <=0."""
    r = rmssd(intervals)
    if r is None or r <= 0:
        return None
    return log(r)

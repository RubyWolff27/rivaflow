"""B4 — Frequency-domain + non-linear HRV (the pure core, the "HRV Lab").

Unlocks the richest HRV signal from the RR tachogram (WHOOP_FUTURE_STATE_PLAN.md B4), with the physiology
review's guardrails baked in so the numbers are honest:

  - **≥5-min stationary windows only.** LF needs ≥~2 min, VLF/total-power ≥5 min; short snippets give
    spectral numbers with no defensible meaning. We refuse to compute on shorter windows.
  - **Lomb-Scargle, not FFT.** RR intervals are unevenly sampled in time; Lomb-Scargle handles that directly
    without the resampling artifact an FFT would need. Pure-Python (no numpy dependency).
  - **LF:HF is a DESCRIPTIVE ratio, not "sympatho-vagal balance"** (Billman 2013): LF is mixed baroreflex/
    autonomic, not a clean sympathetic index. We report it as a trend, labelled, never as a balance measure.
  - **Poincaré SD1 ≡ RMSSD/√2** and SD2 maps to SDNN — SD1 carries no information beyond RMSSD, so it is a
    visualisation, and the genuinely additive non-linear signal is the SD2/SD1 ratio.

Consumes B0-cleaned, contiguous segments (clean_segments) so beat-detection artifact doesn't leak into the
spectrum. HF band carries beat-detection jitter, so an artifact-% caveat should always travel with these.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, pi, sin, sqrt

# Standard HRV frequency bands (Hz) — Task Force 1996.
VLF_BAND = (0.0033, 0.04)
LF_BAND = (0.04, 0.15)
HF_BAND = (0.15, 0.40)

MIN_WINDOW_SEC = 300.0   # ≥5 min — below this, spectral HRV is not validly interpretable
MIN_BEATS = 150          # and enough beats to resolve the bands
FREQ_STEP = 0.002        # spectral grid resolution (Hz)


def sdnn(intervals: list[float]) -> float | None:
    """Standard deviation of RR intervals (ms)."""
    n = len(intervals)
    if n < 2:
        return None
    m = sum(intervals) / n
    return sqrt(sum((x - m) ** 2 for x in intervals) / n)


@dataclass
class Poincare:
    sd1: float   # short-term variability ≡ RMSSD/√2 (visualisation, not independent of RMSSD)
    sd2: float   # long-term variability (maps to SDNN)
    ratio: float  # SD2/SD1 — the genuinely additive non-linear signal

    def as_dict(self) -> dict:
        return {"sd1": round(self.sd1, 1), "sd2": round(self.sd2, 1),
                "sd2_sd1_ratio": round(self.ratio, 2),
                "note": "SD1 ≡ RMSSD/√2 (visualisation); SD2/SD1 is the additive non-linear signal."}


def poincare(intervals: list[float]) -> Poincare | None:
    """Poincaré SD1/SD2 from successive-difference geometry. SD1 = SD(diffs)/√2, SD2 = √(2·SDNN² − SD1²)."""
    if len(intervals) < 3:
        return None
    diffs = [intervals[i + 1] - intervals[i] for i in range(len(intervals) - 1)]
    n = len(diffs)
    dmean = sum(diffs) / n
    sdsd = sqrt(sum((d - dmean) ** 2 for d in diffs) / n)
    sd1 = sdsd / sqrt(2)
    sd = sdnn(intervals) or 0.0
    sd2_sq = 2 * sd * sd - sd1 * sd1
    sd2 = sqrt(sd2_sq) if sd2_sq > 0 else 0.0
    ratio = sd2 / sd1 if sd1 > 0 else 0.0
    return Poincare(sd1=sd1, sd2=sd2, ratio=ratio)


def _lomb_scargle_power(times: list[float], values: list[float], freq: float) -> float:
    """Lomb-Scargle spectral power at one frequency for unevenly-sampled (times, values). Press & Rybicki
    normalisation. `values` should be mean-subtracted by the caller."""
    w = 2.0 * pi * freq
    s2 = sum(sin(2 * w * t) for t in times)
    c2 = sum(cos(2 * w * t) for t in times)
    tau = atan2(s2, c2) / (2 * w) if w != 0 else 0.0
    cos_sum = sin_sum = cc = ss = 0.0
    for t, x in zip(times, values):
        c = cos(w * (t - tau))
        s = sin(w * (t - tau))
        cos_sum += x * c
        sin_sum += x * s
        cc += c * c
        ss += s * s
    p_c = (cos_sum * cos_sum / cc) if cc > 0 else 0.0
    p_s = (sin_sum * sin_sum / ss) if ss > 0 else 0.0
    return 0.5 * (p_c + p_s)


@dataclass
class SpectralHRV:
    vlf: float
    lf: float
    hf: float
    total_power: float
    lf_hf: float          # DESCRIPTIVE ratio — NOT sympatho-vagal balance
    lf_nu: float          # LF in normalised units: LF/(LF+HF)*100
    hf_nu: float
    window_sec: float
    beats: int

    def as_dict(self) -> dict:
        return {
            "vlf": round(self.vlf, 1), "lf": round(self.lf, 1), "hf": round(self.hf, 1),
            "total_power": round(self.total_power, 1),
            "lf_hf": round(self.lf_hf, 2), "lf_nu": round(self.lf_nu, 1), "hf_nu": round(self.hf_nu, 1),
            "window_sec": round(self.window_sec), "beats": self.beats,
            "note": ("LF:HF is a descriptive ratio, NOT a sympatho-vagal balance measure. "
                     "HF ≈ vagal/respiratory; LF is mixed baroreflex/autonomic."),
        }


def frequency_domain(intervals: list[float]) -> SpectralHRV | None:
    """Lomb-Scargle frequency-domain HRV over a single contiguous RR segment. Returns None unless the window
    is ≥5 min and ≥150 beats (short-window spectra are not validly interpretable)."""
    if len(intervals) < MIN_BEATS:
        return None
    # Time axis = cumulative beat times (seconds); RR in ms.
    times: list[float] = []
    t = 0.0
    for rr in intervals:
        t += rr / 1000.0
        times.append(t)
    if times[-1] < MIN_WINDOW_SEC:
        return None

    mean_rr = sum(intervals) / len(intervals)
    values = [x - mean_rr for x in intervals]   # detrend (remove DC)

    def band_power(lo: float, hi: float) -> float:
        f = lo
        p = 0.0
        while f < hi:
            p += _lomb_scargle_power(times, values, f) * FREQ_STEP
            f += FREQ_STEP
        return p

    vlf = band_power(*VLF_BAND)
    lf = band_power(*LF_BAND)
    hf = band_power(*HF_BAND)
    total = vlf + lf + hf
    lf_hf = lf / hf if hf > 0 else 0.0
    denom = lf + hf
    lf_nu = 100.0 * lf / denom if denom > 0 else 0.0
    hf_nu = 100.0 * hf / denom if denom > 0 else 0.0
    return SpectralHRV(vlf=vlf, lf=lf, hf=hf, total_power=total, lf_hf=lf_hf,
                       lf_nu=lf_nu, hf_nu=hf_nu, window_sec=times[-1], beats=len(intervals))

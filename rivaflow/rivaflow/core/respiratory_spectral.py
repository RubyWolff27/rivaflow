"""Wave 3.5 — spectral (band-pass) respiratory-rate estimate: an honest, stdlib-only alternative to
whoop_analytics._resp_rpm's up-crossing count, cross-checked against it rather than trusted blind (see
whoop_analytics.respiratory_rate).

Respiration modulates heart rate via the respiratory sinus arrhythmia (RSA): the RR tachogram oscillates at
the breathing frequency, which sits within 0.1-0.5 Hz (6-30 breaths/min — the same plausible band
_resp_rpm already enforces). RR beats are unevenly sampled in time (beat-to-beat, not clock-tick), so this
module resamples ONE contiguous, QC-clean RR segment (rr_quality.clean_segments — never across a real
dropout, which would fabricate continuity the beats never had) onto a uniform time grid, demeans it, then
scans a direct-form DFT over the band only to find the dominant frequency.

Cost bound: resampling a window of `window_sec` seconds at RESAMPLE_HZ gives n = window_sec * RESAMPLE_HZ
uniform samples. The DFT below evaluates only the discrete bins inside [BAND_LO_HZ, BAND_HI_HZ] (not a full
spectrum) — k = (BAND_HI_HZ - BAND_LO_HZ) / FREQ_STEP_HZ bins, each an O(n) sum — so total cost is O(n*k).
`window_sec` is itself capped at MAX_WINDOW_SEC (see _bounded_window), which bounds n and therefore the
whole scan to a fixed, small cost regardless of how much RR history the caller has: at the cap,
n = 300s * 4Hz = 1200 samples and k = (0.5-0.1)/0.005 = 80 bins, so <=96,000 multiply-adds — comfortably
sub-second in pure Python.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin

VERSION = "resp-bandpass-v1"

RESAMPLE_HZ = 4.0  # uniform-grid resample rate
BAND_LO_HZ = 0.1  # 6 breaths/min — matches _resp_rpm's plausible floor
BAND_HI_HZ = 0.5  # 30 breaths/min — matches _resp_rpm's plausible ceiling
FREQ_STEP_HZ = 0.005  # ~80 bins across the band — resolves better than +/-1rpm
MIN_WINDOW_SEC = 60.0  # below this, RSA has too few oscillation cycles to trust a peak
MAX_WINDOW_SEC = (
    300.0  # bound n fed to the DFT scan (see module docstring's cost bound)
)
AGREEMENT_TOLERANCE_RPM = 2.0  # how close the spectral + counting estimates must land to trust the spectral one


@dataclass
class SpectralRespiration:
    rpm: float
    window_sec: float
    n_samples: int
    dominant_hz: float


def _beat_times(intervals: list[float]) -> list[float]:
    """Cumulative beat time (sec) from RR intervals (ms) — beat i occurs at the sum of intervals[0..i]."""
    times: list[float] = []
    t = 0.0
    for rr in intervals:
        t += rr / 1000.0
        times.append(t)
    return times


def _bounded_window(
    times: list[float], intervals: list[float]
) -> tuple[list[float], list[float]] | None:
    """The most recent <=MAX_WINDOW_SEC slice of (times, intervals) — bounds the DFT's cost (see module
    docstring). None when the available segment (or its bounded tail) is under MIN_WINDOW_SEC.
    """
    if not times or times[-1] < MIN_WINDOW_SEC:
        return None
    cutoff = max(0.0, times[-1] - MAX_WINDOW_SEC)
    start = next((i for i, t in enumerate(times) if t >= cutoff), 0)
    win_times, win_vals = times[start:], intervals[start:]
    if win_times[-1] - win_times[0] < MIN_WINDOW_SEC:
        return None
    return win_times, win_vals


def _resample_uniform(
    times: list[float], values: list[float], hz: float
) -> tuple[list[float], list[float]]:
    """Linear-interpolate unevenly-sampled (times, values) onto a uniform `hz` grid spanning
    [times[0], times[-1]]. Two-pointer walk — O(n) in the combined length of `times` and the output grid.
    """
    t0, t1 = times[0], times[-1]
    n = max(2, int((t1 - t0) * hz) + 1)
    grid = [t0 + i / hz for i in range(n)]
    m = len(times)
    out: list[float] = []
    j = 0
    for gt in grid:
        while j < m - 2 and times[j + 1] < gt:
            j += 1
        j_hi = min(j + 1, m - 1)
        t_a, t_b = times[j], times[j_hi]
        v_a, v_b = values[j], values[j_hi]
        if t_b == t_a:
            out.append(v_a)
        else:
            frac = (gt - t_a) / (t_b - t_a)
            out.append(v_a + frac * (v_b - v_a))
    return grid, out


def _dominant_band_frequency(times: list[float], values: list[float]) -> float | None:
    """Scan BAND_LO_HZ..BAND_HI_HZ in FREQ_STEP_HZ steps for the frequency with peak DFT power (direct-form
    single-frequency DFT, not a full FFT — see module docstring's cost bound). None on a degenerate input.
    """
    if len(values) < 2:
        return None
    best_power = -1.0
    best_freq: float | None = None
    f = BAND_LO_HZ
    while f <= BAND_HI_HZ:
        w = 2.0 * pi * f
        re = sum(v * cos(w * t) for t, v in zip(times, values))
        im = sum(v * sin(w * t) for t, v in zip(times, values))
        power = re * re + im * im
        if power > best_power:
            best_power = power
            best_freq = f
        f += FREQ_STEP_HZ
    return best_freq


def estimate_respiratory_rate(segment: list[float]) -> SpectralRespiration | None:
    """Spectral (band-pass) RSA respiratory-rate estimate from ONE contiguous, QC-cleaned RR segment (ms) —
    see rr_quality.clean_segments. Resamples the (bounded) window onto a uniform grid, demeans, then finds
    the dominant frequency in the respiratory band. None when the segment is too short to resolve any
    oscillation cycles (< MIN_WINDOW_SEC) or the band scan is degenerate.
    """
    times = _beat_times(segment)
    windowed = _bounded_window(times, segment)
    if windowed is None:
        return None
    win_times, win_vals = windowed

    grid_t, resampled = _resample_uniform(win_times, win_vals, RESAMPLE_HZ)
    mean_v = sum(resampled) / len(resampled)
    demeaned = [v - mean_v for v in resampled]

    freq = _dominant_band_frequency(grid_t, demeaned)
    if freq is None:
        return None
    return SpectralRespiration(
        rpm=60.0 * freq,
        window_sec=win_times[-1] - win_times[0],
        n_samples=len(resampled),
        dominant_hz=freq,
    )

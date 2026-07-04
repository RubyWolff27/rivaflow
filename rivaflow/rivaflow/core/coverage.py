"""B3 — Capture-coverage / RR-coverage guard (the pure core).

Makes every baseline trustworthy by excluding under-covered nights (WHOOP_FUTURE_STATE_PLAN.md B3).

The load-bearing insight (feasibility lens, WHOOP_CURRENT_STATE.md §2): RR only exists while the phone
holds a LIVE BLE connection to the strap. The 48 h device-store backfill recovers HR only — no RR. So on a
charging-away night the HR view looks fully covered while the beat-to-beat tachogram every HRV/readiness/
prevention signal depends on is missing. Coverage therefore MUST be measured on RR separately from HR, or a
silent RR gap poisons the baselines behind an HR view that reads "fine."

This module quantifies, per day: usable RR-minutes, the longest contiguous RR segment, and (for contrast)
HR-minutes — then gives a single `sufficient` verdict the daily builders gate on. Quality (artifact-%) is
B0's job; this is quantity + contiguity. A day must clear BOTH to anchor a baseline.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rivaflow.core.rr_quality import RR_MAX_MS, RR_MIN_MS, clean_segments

# Tunable thresholds — a night below these can't anchor a baseline.
MIN_RR_MINUTES = 5.0  # total usable (in-band) RR captured across the day
MIN_CONTIGUOUS_MINUTES = (
    2.0  # longest unbroken RR run — a short-term HRV window needs a contiguous block
)
HR_SAMPLE_HZ = 1.0  # standard 0x2A37 HR stream is ~1 sample/second


@dataclass
class CoverageReport:
    rr_minutes: float  # usable in-band RR captured (live-connection signal)
    longest_segment_minutes: float
    hr_minutes: float  # HR captured — includes backfill, so ≫ rr_minutes on charging-away nights
    rr_intervals: int
    sufficient: bool
    reason: str

    def as_dict(self) -> dict:
        return {
            "rr_minutes": round(self.rr_minutes, 1),
            "longest_segment_minutes": round(self.longest_segment_minutes, 1),
            "hr_minutes": round(self.hr_minutes, 1),
            "rr_intervals": self.rr_intervals,
            "sufficient": self.sufficient,
            "reason": self.reason,
        }


def assess_coverage(
    rr_intervals: Sequence[float], hr_samples: int = 0
) -> CoverageReport:
    """Coverage verdict for one day. `rr_intervals` = that day's raw RR (any band); `hr_samples` = that day's
    HR sample count (for the RR-vs-HR gap). Deterministic and DB-free."""
    inband = [
        float(x) for x in rr_intervals if x is not None and RR_MIN_MS <= x <= RR_MAX_MS
    ]
    rr_minutes = sum(inband) / 60000.0
    segments = clean_segments(rr_intervals, min_len=1)  # all contiguous in-spec runs
    longest_minutes = max((sum(s) / 60000.0 for s in segments), default=0.0)
    hr_minutes = hr_samples / (HR_SAMPLE_HZ * 60.0)

    if rr_minutes < MIN_RR_MINUTES:
        # Name the masking case explicitly: plenty of HR, but the tachogram is missing.
        if hr_minutes >= MIN_RR_MINUTES:
            reason = (
                f"RR-starved night — only {rr_minutes:.1f} min of RR despite {hr_minutes:.0f} min of HR "
                f"(phone likely charging away from the strap); excluded from baselines."
            )
        else:
            reason = f"Low capture — {rr_minutes:.1f} min RR (need {MIN_RR_MINUTES:.0f}); excluded from baselines."
        sufficient = False
    elif longest_minutes < MIN_CONTIGUOUS_MINUTES:
        reason = (
            f"Fragmented — longest RR run {longest_minutes:.1f} min "
            f"(need {MIN_CONTIGUOUS_MINUTES:.0f}); excluded from baselines."
        )
        sufficient = False
    else:
        reason = "sufficient"
        sufficient = True

    return CoverageReport(
        rr_minutes=rr_minutes,
        longest_segment_minutes=longest_minutes,
        hr_minutes=hr_minutes,
        rr_intervals=len(inband),
        sufficient=sufficient,
        reason=reason,
    )


def coverage_in_days(reports: list[CoverageReport]) -> dict:
    """Roll a set of per-day reports into a coverage summary: how many days actually clear the RR bar (the
    number that governs whether time-baseline builds can trust their baseline)."""
    total = len(reports)
    good = sum(1 for r in reports if r.sufficient)
    return {
        "days_total": total,
        "days_sufficient": good,
        "days_excluded": total - good,
        "rr_coverage_pct": round(100.0 * good / total, 1) if total else 0.0,
    }

"""P3 — Web deep-dive cockpit renderer (pure, dependency-free).

The analyst's cockpit (WHOOP_FUTURE_STATE_PLAN.md web deep-dive): server-rendered HTML with inline-SVG
charts computed from the existing endpoints — the web app only RENDERS, all compute stays server-side.
No JS/CDN dependency: sparklines, bars, and the ACWR ribbon are plain inline SVG built from the series here.

Sub-phased by panel group; P3.1 ships Recovery & Load. Every dynamic string is HTML-escaped.
"""

from __future__ import annotations

import html

_ACCENT = {
    "Prime": "#34d399",
    "Balanced": "#60a5fa",
    "Strained": "#fbbf24",
    "Rundown": "#f87171",
    "Building": "#94a3b8",
    "Rest": "#a78bfa",
}
_ZONE_COLOR = {
    "undertraining": "#60a5fa",
    "sweet-spot": "#34d399",
    "caution": "#fbbf24",
    "high-risk": "#f87171",
}


def esc(s: object) -> str:
    return html.escape(str(s))


def svg_sparkline(
    values: list[float | None], w: int = 240, h: int = 44, stroke: str = "#60a5fa"
) -> str:
    """A dependency-free line chart from a numeric series."""
    pts = [float(v) for v in values if v is not None]
    if len(pts) < 2:
        return f'<svg width="{w}" height="{h}" role="img" aria-label="no data"></svg>'
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1.0
    step = w / (len(pts) - 1)
    coords = " ".join(
        f"{i * step:.1f},{h - (v - lo) / rng * (h - 4) - 2:.1f}"
        for i, v in enumerate(pts)
    )
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
        f'<polyline fill="none" stroke="{stroke}" stroke-width="2" points="{coords}"/></svg>'
    )


def svg_bars(
    values: list[float | None], w: int = 240, h: int = 44, fill: str = "#34d399"
) -> str:
    """A dependency-free bar chart (e.g. daily cardio load)."""
    vals = [max(0.0, float(v)) for v in values if v is not None]
    if not vals:
        return f'<svg width="{w}" height="{h}" role="img" aria-label="no data"></svg>'
    hi = max(vals) or 1.0
    n = len(vals)
    bw = w / n
    rects = "".join(
        f'<rect x="{i * bw:.1f}" y="{h - (v / hi) * (h - 2):.1f}" width="{bw * 0.8:.1f}" '
        f'height="{(v / hi) * (h - 2):.1f}" fill="{fill}"/>'
        for i, v in enumerate(vals)
    )
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">{rects}</svg>'


def svg_acwr_ribbon(ratio: float, w: int = 240, h: int = 22) -> str:
    """ACWR gauge 0–2 with the Gabbett sweet-spot (0.8–1.3) shaded green and the danger zone (>1.5) red."""

    def x(r: float) -> float:
        return min(max(r, 0.0), 2.0) / 2.0 * w

    marker = x(ratio)
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect x="0" y="6" width="{w}" height="10" fill="#334155"/>'
        f'<rect x="{x(0.8):.1f}" y="6" width="{x(1.3) - x(0.8):.1f}" height="10" fill="#065f46"/>'
        f'<rect x="{x(1.5):.1f}" y="6" width="{w - x(1.5):.1f}" height="10" fill="#7f1d1d"/>'
        f'<line x1="{marker:.1f}" y1="2" x2="{marker:.1f}" y2="20" stroke="#f8fafc" stroke-width="2"/>'
        f"</svg>"
    )


def stat(label: str, value: str, sub: str = "", accent: str = "#e2e8f0") -> str:
    return (
        f'<div class="stat"><div class="lbl">{esc(label)}</div>'
        f'<div class="v" style="color:{accent}">{esc(value)}</div>'
        f'<div class="sub">{esc(sub)}</div></div>'
    )


def render_recovery_load(
    readiness: dict,
    strain: dict,
    acwr: dict,
    cardio_trend: list[dict],
    recovery_cost: dict,
) -> str:
    """P3.1 — the Recovery & Load panel."""
    accent = _ACCENT.get(readiness.get("state", "Building"), "#94a3b8")
    stats = [
        stat(
            "Readiness",
            str(readiness.get("state", "—")),
            readiness.get("headline", ""),
            accent,
        ),
    ]
    if strain.get("available"):
        band = strain.get("band", [])
        stats.append(
            stat(
                "Strain target",
                f'{strain.get("target_load", "—")}/21',
                f'{"capped · " if strain.get("capped") else ""}band {band}',
            )
        )
    if acwr.get("available"):
        stats.append(
            stat(
                "ACWR",
                str(acwr.get("ratio", "—")),
                str(acwr.get("zone", "")),
                _ZONE_COLOR.get(acwr.get("zone", ""), "#e2e8f0"),
            )
        )

    caveat = readiness.get("caveat")
    caveat_html = f'<div class="caveat">⚠️ {esc(caveat)}</div>' if caveat else ""

    contributors = readiness.get("contributors") or []
    contrib_html = "".join(
        f'<span class="chip">{esc(c.get("label", c.get("signal")))}: '
        f'{esc(c.get("direction", ""))}</span>'
        for c in contributors[:4]
    )

    loads = [c.get("cardio_load") for c in cardio_trend]
    ribbon = svg_acwr_ribbon(acwr["ratio"]) if acwr.get("available") else ""
    rc = (
        f'<div class="sub">{esc(recovery_cost.get("headline", ""))}</div>'
        if recovery_cost.get("available")
        else '<div class="sub">recovery-cost coupling: needs more paired days</div>'
    )

    return (
        '<section class="panel"><h2>Recovery &amp; Load</h2>'
        f'<div class="stats">{"".join(stats)}</div>'
        f"{caveat_html}"
        f'<div class="chips">{contrib_html}</div>'
        f'<div class="chart"><div class="lbl">Cardio load · recent</div>{svg_bars(loads)}</div>'
        f'<div class="chart"><div class="lbl">ACWR (7d:28d) — sweet-spot 0.8–1.3</div>{ribbon}</div>'
        f'<div class="chart"><div class="lbl">Recovery cost</div>{rc}</div>'
        "</section>"
    )


def render_cockpit_page(panels_html: str) -> str:
    """Full server-rendered cockpit page (dark, self-contained, auto-refresh)."""
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='120'><title>WHOOP Cockpit</title><style>"
        "body{font-family:system-ui,-apple-system,sans-serif;background:#0b1120;color:#e2e8f0;margin:0;padding:16px}"
        "h1{font-size:18px;margin:0 0 12px}h2{font-size:14px;color:#94a3b8;margin:0 0 10px;text-transform:uppercase;letter-spacing:.05em}"
        ".panel{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:16px;margin-bottom:14px}"
        ".stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:10px}"
        ".stat .lbl,.chart .lbl{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.05em}"
        ".stat .v{font-size:22px;font-weight:600;margin:2px 0}.sub{font-size:12px;color:#94a3b8}"
        ".caveat{background:#422006;border:1px solid #a16207;border-radius:8px;padding:8px;font-size:12px;margin:8px 0}"
        ".chips{margin:8px 0}.chip{display:inline-block;background:#1e293b;border-radius:12px;padding:2px 8px;font-size:11px;margin:2px}"
        ".chart{margin-top:10px}.foot{color:#475569;font-size:11px;margin-top:8px}"
        "</style></head><body><h1>WHOOP Cockpit · analyst deep-dive</h1>"
        f"{panels_html}"
        "<div class='foot'>RivaFlow · self-hosted · renders server-computed series · auto-refresh 2 min</div>"
        "</body></html>"
    )


def render_hrv_lab(hrv_lab: dict, dfa: dict) -> str:
    """P3.2 — HRV Lab: frequency-domain (LF:HF descriptive) + Poincaré + DFA-α1 (experimental)."""
    if not hrv_lab.get("available"):
        body = f'<div class="sub">{esc(hrv_lab.get("reason", "no clean 5-min window yet"))}</div>'
    else:
        fd = hrv_lab.get("frequency_domain", {})
        pc = hrv_lab.get("poincare", {})
        q = hrv_lab.get("quality", {})
        stats = "".join(
            [
                stat(
                    "LF:HF",
                    str(fd.get("lf_hf", "—")),
                    "descriptive ratio, NOT sympatho-vagal",
                ),
                stat("HF", str(fd.get("hf", "—")), "vagal / respiratory"),
                stat(
                    "SD2/SD1",
                    str(pc.get("sd2_sd1_ratio", "—")),
                    "Poincaré (SD1≡RMSSD/√2)",
                ),
                stat(
                    "Artifact",
                    f'{q.get("artifact_pct", "—")}%',
                    f'{q.get("intervals_used", 0)} intervals',
                ),
            ]
        )
        body = f'<div class="stats">{stats}</div><div class="sub">{esc(fd.get("note", ""))}</div>'
    dfa_html = (
        f'<div class="sub">DFA α1 {esc(dfa.get("alpha1", "—"))} · {esc(dfa.get("zone", ""))} (experimental)</div>'
        if dfa.get("available")
        else f'<div class="sub">DFA α1: {esc(dfa.get("reason", "needs low-artifact segment"))}</div>'
    )
    return f'<section class="panel"><h2>HRV Lab</h2>{body}{dfa_html}</section>'


def render_data_integrity(coverage: dict) -> str:
    """P3.2 - Data integrity: RR coverage-in-days + per-day RR minutes."""
    summ = coverage.get("summary", {})
    days = coverage.get("days", [])
    rr_mins = [d.get("rr_minutes") for d in days]
    pct = summ.get("rr_coverage_pct", "—")
    sub = (
        f'{summ.get("days_sufficient", 0)}/{summ.get("days_total", 0)} days sufficient'
    )
    return (
        '<section class="panel"><h2>Data integrity</h2>'
        f'<div class="stats">{stat("RR coverage", f"{pct}%", sub)}</div>'
        f'<div class="chart"><div class="lbl">RR minutes per day</div>{svg_bars(rr_mins)}</div>'
        '<div class="sub">RR is measured separately from HR - a charging-away night shows as a gap.</div>'
        "</section>"
    )


def render_sleep(sleep: dict) -> str:
    """P3.3 — Sleep: need/debt vs the >9h need + bedtime regularity."""
    debt = sleep.get("debt", {})
    reg = sleep.get("regularity", {})
    stats = "".join(
        [
            stat(
                "Sleep debt",
                f'{debt.get("debt_hours", "—")}h',
                debt.get("headline", "") if debt.get("available") else "building",
            ),
            stat(
                "Avg sleep",
                f'{debt.get("recent_avg_hours", "—")}h',
                f'need {debt.get("need_hours", 9)}h',
            ),
            stat(
                "Regularity",
                str(reg.get("score", "—")),
                reg.get("headline", "") if reg.get("available") else "need 3+ nights",
            ),
        ]
    )
    return f'<section class="panel"><h2>Sleep</h2><div class="stats">{stats}</div></section>'


def render_trends(
    longevity: dict, resilience: dict, circadian: dict, assessment: dict
) -> str:
    """P3.3 — Trends & Longevity: VO2max (banded), CV-age proxy (caveated), resilience, circadian, assessment."""
    vo2 = longevity.get("vo2max", {})
    cv = longevity.get("cardio_age", {})
    res = resilience.get("resilience", {})
    stats = "".join(
        [
            stat(
                "VO₂max",
                (
                    f'{vo2.get("range", ["—"])[0]}–{vo2.get("range", ["—", "—"])[-1]}'
                    if vo2.get("available")
                    else "—"
                ),
                "banded estimate",
            ),
            stat(
                "Cardio age",
                str(cv.get("cardio_age_proxy", "—")) if cv.get("available") else "—",
                "PROXY — not clinical",
            ),
            stat(
                "Resilience",
                str(res.get("level", "—")) if res.get("available") else "building",
                "",
            ),
            stat(
                "Circadian",
                (
                    f'{circadian.get("acrophase_hour", "—")}h peak'
                    if circadian.get("available")
                    else "—"
                ),
                "HR rhythm",
            ),
        ]
    )
    narr = (
        f'<div class="sub">{esc(assessment.get("headline", ""))}</div>'
        if assessment.get("available")
        else ""
    )
    return (
        f'<section class="panel"><h2>Trends &amp; Longevity</h2><div class="stats">{stats}</div>'
        f'<div class="caveat">Cardio age is a PROXY vs VO₂max norms — a gentle trend, not a health verdict.</div>'
        f"{narr}</section>"
    )


def render_prevention_log(rows: list[dict], prevention: dict) -> str:
    """P3.4 — Prevention log: today's tier + the fired-alert timeline + a neutral export note."""
    tier = prevention.get("tier", "—") if prevention.get("available") else "building"
    tier_color = {"green": "#34d399", "amber": "#fbbf24", "red": "#f87171"}.get(
        tier, "#94a3b8"
    )
    timeline = (
        "".join(
            f'<div class="row"><span class="chip">{esc(str(r.get("day"))[:10])}</span> '
            f'{esc(r.get("tier"))} — {esc(r.get("headline", ""))}</div>'
            for r in rows[:12]
        )
        or '<div class="sub">no safety alerts fired</div>'
    )
    return (
        '<section class="panel"><h2>Baseline-Deviation log</h2>'
        f'{stat("Today", str(tier), "detects deviation, never disease", tier_color)}'
        f"{timeline}"
        '<div class="sub">Export is a personal data record — context for a conversation, not clinical data.</div>'
        "</section>"
    )


def render_behaviour(effects: list[dict]) -> str:
    """P3.4 — Behaviour: effect size of each tagged behaviour on lnRMSSD."""
    if not effects:
        return (
            '<section class="panel"><h2>Behaviour correlations</h2>'
            '<div class="sub">Tag days (alcohol, late-training, ill…) to see how each moves your HRV.</div>'
            "</section>"
        )
    rows = (
        "".join(
            f'<div class="row"><span class="chip">{esc(e.get("tag"))}</span> '
            f'{esc(e.get("magnitude", ""))} {esc("↑" if e.get("delta", 0) >= 0 else "↓")} '
            f'(d={esc(e.get("cohens_d", "—"))}, n={esc(e.get("n_yes", 0))})</div>'
            for e in effects
            if e.get("available")
        )
        or '<div class="sub">not enough tagged vs untagged nights yet</div>'
    )
    return f'<section class="panel"><h2>Behaviour correlations</h2>{rows}</section>'

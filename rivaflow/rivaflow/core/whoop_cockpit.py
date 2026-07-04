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


def svg_progress_ring(
    have: float, need: float, label: str = "", size: int = 64, accent: str = "#60a5fa"
) -> str:
    """A donut 'building baseline' ring for panels that need N days of history — shown INSTEAD of an
    empty/needs-more-days card so cold-start panels still feel alive."""
    need = max(need, 1e-9)
    pct = max(0.0, min(1.0, have / need))
    r = size / 2 - 6
    circ = 2 * 3.14159265 * r
    dash = circ * pct
    cx = cy = size / 2
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img" '
        f'aria-label="{esc(label)} progress {have} of {need} days">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1e293b" stroke-width="6"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{accent}" stroke-width="6" '
        f'stroke-linecap="round" stroke-dasharray="{dash:.1f} {circ:.1f}" '
        f'transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="12" fill="#e2e8f0">'
        f"{int(min(have, need))}/{int(need)}</text></svg>"
    )


def progress_or_text(
    available: bool, progress: dict | None, fallback: str, label: str = "building"
) -> str:
    """Shared cold-start pattern: a longitudinal panel either has enough days (renders normally, caller's
    job) or shows a progress ring toward the threshold instead of bare 'needs more days' text."""
    if available or not progress:
        return fallback
    have, need = progress.get("have", 0), progress.get("need", 1)
    return (
        '<div class="ring-row">'
        f"{svg_progress_ring(have, need, label)}"
        f'<div class="sub">{esc(label)} baseline — {int(have)} of {int(need)} days</div>'
        "</div>"
    )


def svg_area_line(
    times: list[float],
    values: list[float | None],
    w: int = 560,
    h: int = 110,
    stroke: str = "#60a5fa",
    fill: str = "rgba(96,165,250,0.18)",
    bands: list[tuple[float, float, str]] | None = None,
) -> str:
    """A filled area line for dense intraday series (HR ribbon, overnight HRV, sleep HR, respiratory,
    stress). `bands` are (lo, hi, color) horizontal zone bands drawn behind the line, in data units."""
    pts = [(t, v) for t, v in zip(times, values) if v is not None]
    if len(pts) < 2:
        return f'<svg width="{w}" height="{h}" role="img" aria-label="no data"></svg>'
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x_lo, x_hi = min(xs), max(xs)
    y_lo, y_hi = min(ys), max(ys)
    if bands:
        y_lo = min([y_lo, *(b[0] for b in bands)])
        y_hi = max([y_hi, *(b[1] for b in bands)])
    x_rng = (x_hi - x_lo) or 1.0
    y_rng = (y_hi - y_lo) or 1.0
    pad = 4

    def px(x: float) -> float:
        return (x - x_lo) / x_rng * w

    def py(y: float) -> float:
        return h - pad - (y - y_lo) / y_rng * (h - 2 * pad)

    band_rects = "".join(
        f'<rect x="0" y="{py(hi):.1f}" width="{w}" height="{max(0.0, py(lo) - py(hi)):.1f}" '
        f'fill="{color}" opacity="0.25"/>'
        for lo, hi, color in (bands or [])
    )
    coords = " ".join(f"{px(t):.1f},{py(v):.1f}" for t, v in pts)
    area = (
        f"{px(pts[0][0]):.1f},{py(y_lo):.1f} {coords} {px(pts[-1][0]):.1f},{py(y_lo):.1f}"
    )
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
        f"{band_rects}"
        f'<polygon points="{area}" fill="{fill}"/>'
        f'<polyline fill="none" stroke="{stroke}" stroke-width="2" points="{coords}"/>'
        f'<text x="2" y="10" font-size="9" fill="#64748b">{esc(round(y_hi))}</text>'
        f'<text x="2" y="{h - 2}" font-size="9" fill="#64748b">{esc(round(y_lo))}</text>'
        "</svg>"
    )


def svg_poincare(
    pairs: list[tuple[float, float]],
    sd1: float,
    sd2: float,
    w: int = 220,
    h: int = 220,
) -> str:
    """Poincaré scatter (RR[n] vs RR[n+1]) with the SD1/SD2 ellipse along/across the identity line."""
    if len(pairs) < 3:
        return f'<svg width="{w}" height="{h}" role="img" aria-label="no data"></svg>'
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    lo, hi = min(xs + ys), max(xs + ys)
    rng = (hi - lo) or 1.0
    pad = 12
    scale = (min(w, h) - 2 * pad) / rng

    def sx(x: float) -> float:
        return pad + (x - lo) * scale

    def sy(y: float) -> float:
        return h - pad - (y - lo) * scale

    mean_rr = sum(xs) / len(xs)
    dots = "".join(
        f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="1.6" fill="#60a5fa" opacity="0.55"/>'
        for x, y in pairs[:600]
    )
    cx, cy = sx(mean_rr), sy(mean_rr)
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{pad}" stroke="#334155" stroke-dasharray="3 3"/>'
        f"{dots}"
        f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{sd2 * scale:.1f}" ry="{sd1 * scale:.1f}" '
        f'transform="rotate(-45 {cx:.1f} {cy:.1f})" fill="none" stroke="#34d399" stroke-width="1.5"/>'
        "</svg>"
    )


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
    *,
    acwr_progress: dict | None = None,
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
    ribbon = (
        svg_acwr_ribbon(acwr["ratio"])
        if acwr.get("available")
        else progress_or_text(False, acwr_progress, "", "ACWR (28d)")
    )
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
        ".ring-row{display:flex;align-items:center;gap:10px;margin:6px 0}"
        ".dual{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}"
        ".zbars{display:flex;gap:4px;align-items:flex-end;height:36px;margin-top:6px}"
        ".zbars .zb{flex:1;border-radius:2px 2px 0 0}"
        ".session-card{border-top:1px solid #1f2937;padding-top:10px;margin-top:10px}"
        ".session-card:first-of-type{border-top:none;padding-top:0;margin-top:0}"
        "@media (max-width:640px){.dual{grid-template-columns:1fr}}"
        "</style></head><body><h1>WHOOP Cockpit · analyst deep-dive</h1>"
        f"{panels_html}"
        "<div class='foot'>RivaFlow · self-hosted · renders server-computed series · auto-refresh 2 min</div>"
        "</body></html>"
    )


def render_hrv_lab(hrv_lab: dict, dfa: dict, *, progress: dict | None = None) -> str:
    """P3.2 — HRV Lab: frequency-domain (LF:HF descriptive) + Poincaré + DFA-α1 (experimental)."""
    if not hrv_lab.get("available"):
        body = progress_or_text(
            False,
            progress,
            f'<div class="sub">{esc(hrv_lab.get("reason", "no clean 5-min window yet"))}</div>',
            "HRV Lab",
        )
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


def render_sleep(sleep: dict, *, debt_progress: dict | None = None) -> str:
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
    ring = progress_or_text(bool(debt.get("available")), debt_progress, "", "Sleep debt (14n)")
    return (
        f'<section class="panel"><h2>Sleep</h2><div class="stats">{stats}</div>{ring}</section>'
    )


def render_trends(
    longevity: dict,
    resilience: dict,
    circadian: dict,
    assessment: dict,
    *,
    resilience_progress: dict | None = None,
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
    ring = progress_or_text(
        bool(res.get("available")), resilience_progress, "", "Resilience (14d)"
    )
    return (
        f'<section class="panel"><h2>Trends &amp; Longevity</h2><div class="stats">{stats}</div>'
        f'<div class="caveat">Cardio age is a PROXY vs VO₂max norms — a gentle trend, not a health verdict.</div>'
        f"{narr}{ring}</section>"
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


_HR_ZONE_BANDS = [
    (0.60, 0.70, "#60a5fa"),
    (0.70, 0.80, "#34d399"),
    (0.80, 0.90, "#fbbf24"),
    (0.90, 1.00, "#f87171"),
]


def render_hr_ribbon(series: dict) -> str:
    """P3.5 — Today's full-day HR ribbon with HR-zone bands shaded behind it."""
    if not series.get("available"):
        body = f'<div class="sub">{esc(series.get("reason", "no HR captured today yet"))}</div>'
    else:
        mx = series.get("max_hr", 190)
        bands = [(lo * mx, hi * mx, color) for lo, hi, color in _HR_ZONE_BANDS]
        chart = svg_area_line(
            series["times"], series["values"], bands=bands, stroke="#e2e8f0"
        )
        body = (
            f'<div class="stats">{stat("Avg HR", str(series.get("avg_hr", "—")), "today")}'
            f'{stat("Peak HR", str(series.get("max_bpm", "—")), f"of {mx} max")}</div>'
            f'<div class="chart"><div class="lbl">HR · zone-shaded (Z1–Z5)</div>{chart}</div>'
        )
    return f'<section class="panel"><h2>Today · HR ribbon</h2>{body}</section>'


def render_rr_hrv_detail(detail: dict) -> str:
    """P3.5 — MUST-HAVE HRV-nerd view: RR tachogram + Poincaré scatter with the SD1/SD2 ellipse."""
    if not detail.get("available"):
        body = f'<div class="sub">{esc(detail.get("reason", "not enough clean RR yet"))}</div>'
    else:
        tacho = svg_area_line(
            detail["times"], detail["rr_values"], stroke="#a78bfa", fill="rgba(167,139,250,0.15)"
        )
        scatter = svg_poincare(detail["pairs"], detail["sd1"], detail["sd2"])
        stats = "".join(
            [
                stat("SD1", f'{detail["sd1"]:.0f}ms', "short-term (≈RMSSD/√2)"),
                stat("SD2", f'{detail["sd2"]:.0f}ms', "long-term variability"),
                stat("Mean HR", f'{detail.get("mean_hr", "—")}', "over window"),
            ]
        )
        body = (
            f'<div class="stats">{stats}</div>'
            '<div class="dual">'
            f'<div class="chart"><div class="lbl">RR tachogram</div>{tacho}</div>'
            f'<div class="chart"><div class="lbl">Poincaré (RR[n] vs RR[n+1])</div>{scatter}</div>'
            "</div>"
        )
    return f'<section class="panel"><h2>RR &amp; HRV detail</h2>{body}</section>'


def render_overnight_hrv(curve: dict) -> str:
    """P3.5 — lnRMSSD in 5-min buckets across the detected sleep window."""
    if not curve.get("available"):
        body = f'<div class="sub">{esc(curve.get("reason", "no overnight window detected yet"))}</div>'
    else:
        chart = svg_area_line(
            curve["times"], curve["values"], stroke="#34d399", fill="rgba(52,211,153,0.18)"
        )
        body = f'<div class="chart"><div class="lbl">lnRMSSD · overnight (5-min buckets)</div>{chart}</div>'
    return f'<section class="panel"><h2>Overnight HRV curve</h2>{body}</section>'


def render_sleep_hr_dip(curve: dict) -> str:
    """P3.5 — HR across the detected sleep window, showing the nocturnal dip vs waking baseline."""
    if not curve.get("available"):
        body = f'<div class="sub">{esc(curve.get("reason", "no overnight sleep window detected yet"))}</div>'
    else:
        chart = svg_area_line(
            curve["times"], curve["values"], stroke="#818cf8", fill="rgba(129,140,248,0.15)"
        )
        stats = "".join(
            [
                stat("Sleep onset", str(curve.get("onset", "—"))),
                stat("Sleep offset", str(curve.get("offset", "—"))),
                stat("Nocturnal dip", f'{curve.get("dip_pct", "—")}%', "vs waking HR"),
            ]
        )
        body = (
            f'<div class="stats">{stats}</div>'
            f'<div class="chart"><div class="lbl">HR across sleep window</div>{chart}</div>'
        )
    return f'<section class="panel"><h2>Sleep HR &amp; nocturnal dip</h2>{body}</section>'


def render_respiratory(trace: dict) -> str:
    """P3.5 — Respiratory rate (breaths/min) across rest windows through the day."""
    if not trace.get("available"):
        body = f'<div class="sub">{esc(trace.get("reason", "not enough clean resting RR yet"))}</div>'
    else:
        chart = svg_area_line(
            trace["times"], trace["values"], stroke="#f472b6", fill="rgba(244,114,182,0.15)"
        )
        body = f'<div class="chart"><div class="lbl">Breaths/min · resting windows</div>{chart}</div>'
    return f'<section class="panel"><h2>Respiratory trace</h2>{body}</section>'


def render_stress_ribbon(ribbon: dict) -> str:
    """P3.5 — HRV-vs-baseline stress across the day as a colored band."""
    if not ribbon.get("available"):
        body = f'<div class="sub">{esc(ribbon.get("reason", "not enough HR history for a baseline yet"))}</div>'
    else:
        bands = [(0, 34, "#34d399"), (34, 67, "#fbbf24"), (67, 100, "#f87171")]
        chart = svg_area_line(
            ribbon["times"], ribbon["values"], bands=bands, stroke="#e2e8f0"
        )
        body = f'<div class="chart"><div class="lbl">Stress vs baseline (0–100)</div>{chart}</div>'
    return f'<section class="panel"><h2>Stress ribbon</h2>{body}</section>'


def _zone_bar_html(zone_secs: dict) -> str:
    total = sum(zone_secs.values()) or 1
    colors = {1: "#60a5fa", 2: "#34d399", 3: "#a3e635", 4: "#fbbf24", 5: "#f87171"}
    bars = "".join(
        f'<div class="zb" style="height:{max(4, zone_secs.get(z, 0) / total * 36):.0f}px;'
        f'background:{colors[z]}" title="Z{z}: {zone_secs.get(z, 0)}s"></div>'
        for z in range(1, 6)
    )
    return f'<div class="zbars">{bars}</div>'


def _session_card_html(s: dict) -> str:
    a = s.get("analytics", {})
    if not a.get("available"):
        return (
            '<div class="session-card">'
            f'<div class="sub">{esc(s.get("label", "Session"))} · {esc(s.get("day", ""))} — '
            f'{esc(a.get("reason", "no HR captured"))}</div></div>'
        )
    curve = svg_area_line(
        a.get("times", []), a.get("values", []), w=420, h=70, stroke="#60a5fa"
    )
    drift = a.get("hrr")
    drift_html = (
        f'<span class="chip">HRR: {esc(drift)} bpm/60s</span>' if drift is not None else ""
    )
    peak_sub = f'peak {a.get("max_hr", "—")}'
    duration_min = a.get("duration_sec", 0) // 60
    stats_html = (
        stat("Session", str(s.get("label", "Session")), str(s.get("day", "")))
        + stat("Avg HR", str(a.get("avg_hr", "—")), peak_sub)
        + stat("Duration", f"{duration_min}min", "")
    )
    return (
        '<div class="session-card">'
        f'<div class="stats">{stats_html}</div>'
        f'<div class="dual"><div class="chart"><div class="lbl">HR curve</div>{curve}</div>'
        f'<div class="chart"><div class="lbl">Time in zones</div>{_zone_bar_html(a.get("hr_zone_secs", {}))}'
        f"{drift_html}</div></div></div>"
    )


def render_session_deepdives(sessions: list[dict]) -> str:
    """P3.5 — MUST-HAVE: per-session (BJJ + CrossFit) HR curve, time-in-zones, and HR-drift/decoupling."""
    if not sessions:
        body = '<div class="sub">No recent sessions with WHOOP HR coverage yet.</div>'
    else:
        body = "".join(_session_card_html(s) for s in sessions[:5])
    return f'<section class="panel"><h2>Session deep-dives</h2>{body}</section>'

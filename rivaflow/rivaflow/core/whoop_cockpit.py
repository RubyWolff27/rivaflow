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

"""P3 — Web deep-dive cockpit renderer (pure, dependency-free).

The analyst's cockpit (WHOOP_FUTURE_STATE_PLAN.md web deep-dive): server-rendered HTML with inline-SVG
charts computed from the existing endpoints — the web app only RENDERS, all compute stays server-side.
No JS/CDN dependency: sparklines, bars, and the ACWR ribbon are plain inline SVG built from the series here.

Sub-phased by panel group; P3.1 ships Recovery & Load. Every dynamic string is HTML-escaped.
"""

from __future__ import annotations

import html
from math import log1p

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
    return f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">{rects}</svg>'


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
    job) or shows a progress ring toward the threshold instead of bare 'needs more days' text.
    """
    if available or not progress:
        return fallback
    have, need = progress.get("have", 0), progress.get("need", 1)
    return (
        '<div class="ring-row">'
        f"{svg_progress_ring(have, need, label)}"
        f'<div class="sub">{esc(label)} baseline — {int(have)} of {int(need)} days</div>'
        "</div>"
    )


def _fmt_x(value: float, xkind: str) -> str:
    """Format an x-value as an axis label by unit convention:
    'clock'      → value is minutes-since-midnight        → HH:MM (wall-clock)
    'clock_h'    → value is hours-since-midnight           → HH:MM (wall-clock, e.g. daily HR ribbon)
    'clock_hour' → value is hour-of-day (0–23)            → HH:00 (e.g. stress ribbon)
    'elapsed_h'  → value is hours since window start      → H:MM (e.g. overnight HRV / sleep)
    'elapsed_m'  → value is minutes since start           → H:MM (e.g. a workout / RR tachogram)
    """
    if xkind == "clock":
        m = int(round(value)) % (24 * 60)
        return f"{m // 60:02d}:{m % 60:02d}"
    if xkind == "clock_h":
        m = int(round(value * 60)) % (24 * 60)
        return f"{m // 60:02d}:{m % 60:02d}"
    if xkind == "clock_hour":
        return f"{int(round(value)) % 24:02d}:00"
    hours = value if xkind == "elapsed_h" else value / 60.0
    hh = int(hours)
    mm = int(round((hours - hh) * 60))
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{hh}:{mm:02d}"


def _auto_xticks(
    x_lo: float, x_hi: float, xkind: str, n: int = 5
) -> list[tuple[float, str]]:
    """Evenly spaced axis ticks labelled per the xkind unit convention (see _fmt_x)."""
    if x_hi <= x_lo:
        return []
    return [
        (
            x_lo + (x_hi - x_lo) * i / (n - 1),
            _fmt_x(x_lo + (x_hi - x_lo) * i / (n - 1), xkind),
        )
        for i in range(n)
    ]


def _segments(
    pts: list[tuple[float, float]], max_gap: float | None
) -> list[list[tuple[float, float]]]:
    """Split a series into contiguous segments, breaking wherever the x-gap exceeds max_gap so a data
    dropout renders as an honest BREAK in the line instead of a straight bridge across missing time.
    """
    if max_gap is None or len(pts) < 2:
        return [pts]
    segs: list[list[tuple[float, float]]] = [[pts[0]]]
    for prev, cur in zip(pts, pts[1:]):
        if cur[0] - prev[0] > max_gap:
            segs.append([cur])
        else:
            segs[-1].append(cur)
    return segs


def svg_area_line(
    times: list[float],
    values: list[float | None],
    w: int = 900,
    h: int = 120,
    stroke: str = "#60a5fa",
    fill: str = "rgba(96,165,250,0.18)",
    bands: list[tuple[float, float, str]] | None = None,
    *,
    max_gap: float | None = None,
    xkind: str | None = None,
    series_id: str | None = None,
    responsive: bool = True,
) -> str:
    """A filled area line for dense intraday series (HR ribbon, overnight HRV, sleep HR, respiratory,
    stress). `bands` are (lo, hi, color) horizontal zone bands drawn behind the line, in data units.

    Renders full-width (responsive) so charts fill their panel. Breaks the line across time gaps
    (`max_gap`, same units as `times`) rather than bridging them. Draws x-axis time ticks when `xkind`
    is set ('clock'=minutes-since-midnight, 'elapsed'=seconds). When `series_id` is given, embeds the raw
    series so the page's scrub script can show a value/time tooltip on hover.
    """
    pts = [(float(t), float(v)) for t, v in zip(times, values) if v is not None]
    ax = 34  # left gutter for y labels
    ab = 16  # bottom gutter for x ticks
    size_attr = (
        f'width="100%" viewBox="0 0 {w} {h}" preserveAspectRatio="none"'
        if responsive
        else f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none"'
    )
    if len(pts) < 2:
        return f'<svg {size_attr} role="img" aria-label="no data"></svg>'
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x_lo, x_hi = min(xs), max(xs)
    y_lo, y_hi = min(ys), max(ys)
    if bands:
        y_lo = min([y_lo, *(b[0] for b in bands)])
        y_hi = max([y_hi, *(b[1] for b in bands)])
    pad = 4
    plot_w = w - ax
    plot_h = h - ab
    geom = _LineGeom(x_lo, x_hi, y_lo, y_hi, ax, plot_w, plot_h, pad)
    band_rects = "".join(
        f'<rect x="{ax}" y="{geom.py(hi):.1f}" width="{plot_w}" '
        f'height="{max(0.0, geom.py(lo) - geom.py(hi)):.1f}" fill="{color}" opacity="0.25"/>'
        for lo, hi, color in (bands or [])
    )
    grid = _line_grid(geom, w)
    xaxis = _line_xaxis(geom, xkind, plot_h, h) if xkind else ""
    paths = _line_paths(_segments(pts, max_gap), geom, plot_h, pad, stroke, fill)
    data_attr, scrub = _scrub_layer(series_id, pts, geom, plot_h, pad, w, xkind, stroke)
    return (
        f"<svg {size_attr}{data_attr} role='img'>"
        f"{band_rects}{grid}{xaxis}{paths}{scrub}"
        "</svg>"
    )


class _LineGeom:
    """Data→pixel mapping for a line chart's plot area (shared by grid/axis/paths/scrub builders)."""

    def __init__(self, x_lo, x_hi, y_lo, y_hi, ax, plot_w, plot_h, pad):
        self.x_lo, self.x_hi, self.y_lo, self.y_hi = x_lo, x_hi, y_lo, y_hi
        self.ax, self.plot_w, self.plot_h, self.pad = ax, plot_w, plot_h, pad
        self._xr = (x_hi - x_lo) or 1.0
        self._yr = (y_hi - y_lo) or 1.0

    def px(self, x: float) -> float:
        return self.ax + (x - self.x_lo) / self._xr * self.plot_w

    def py(self, y: float) -> float:
        return (
            self.plot_h
            - self.pad
            - (y - self.y_lo) / self._yr * (self.plot_h - 2 * self.pad)
        )


def _line_grid(g: _LineGeom, w: int) -> str:
    out = ""
    for gy in (g.y_lo, (g.y_lo + g.y_hi) / 2, g.y_hi):
        yy = g.py(gy)
        out += (
            f'<line x1="{g.ax}" y1="{yy:.1f}" x2="{w}" y2="{yy:.1f}" stroke="#1e293b" stroke-width="1"/>'
            f'<text x="{g.ax - 4}" y="{yy + 3:.1f}" font-size="9" fill="#64748b" text-anchor="end">'
            f"{esc(round(gy))}</text>"
        )
    return out


def _line_xaxis(g: _LineGeom, xkind: str, plot_h: float, h: int) -> str:
    out = ""
    for tv, lbl in _auto_xticks(g.x_lo, g.x_hi, xkind):
        xx = g.px(tv)
        out += (
            f'<line x1="{xx:.1f}" y1="{plot_h}" x2="{xx:.1f}" y2="{plot_h - 3}" stroke="#334155"/>'
            f'<text x="{xx:.1f}" y="{h - 4}" font-size="9" fill="#64748b" text-anchor="middle">'
            f"{esc(lbl)}</text>"
        )
    return out


def _line_paths(
    segs, g: _LineGeom, plot_h: float, pad: int, stroke: str, fill: str
) -> str:
    out = ""
    for seg in segs:
        if len(seg) < 2:
            if seg:
                out += f'<circle cx="{g.px(seg[0][0]):.1f}" cy="{g.py(seg[0][1]):.1f}" r="1.6" fill="{stroke}"/>'
            continue
        coords = " ".join(f"{g.px(t):.1f},{g.py(v):.1f}" for t, v in seg)
        area = f"{g.px(seg[0][0]):.1f},{plot_h - pad:.1f} {coords} {g.px(seg[-1][0]):.1f},{plot_h - pad:.1f}"
        out += (
            f'<polygon points="{area}" fill="{fill}"/>'
            f'<polyline fill="none" stroke="{stroke}" stroke-width="2" points="{coords}"/>'
        )
    return out


def _scrub_layer(
    series_id, pts, g: _LineGeom, plot_h, pad, w, xkind, stroke
) -> tuple[str, str]:
    if not series_id:
        return "", ""
    series_json = ",".join(f"[{t:.2f},{v:.1f}]" for t, v in pts)
    data_attr = (
        f' class="scrub" data-series="[{series_json}]" data-xlo="{g.x_lo:.2f}" data-xhi="{g.x_hi:.2f}"'
        f' data-ylo="{g.y_lo:.2f}" data-yhi="{g.y_hi:.2f}" data-ax="{g.ax}" data-pw="{g.plot_w:.0f}"'
        f' data-ph="{plot_h}" data-pad="{pad}" data-w="{w}" data-xkind="{xkind or "elapsed_m"}"'
    )
    scrub = (
        f'<line class="scrub-line" x1="0" y1="0" x2="0" y2="{plot_h}" stroke="{stroke}" '
        f'stroke-width="1" opacity="0" pointer-events="none"/>'
        f'<circle class="scrub-dot" r="3" fill="{stroke}" opacity="0" pointer-events="none"/>'
    )
    return data_attr, scrub


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


def render_cockpit_page(panels_html: str, rendered_at: str = "") -> str:
    """Full server-rendered cockpit page (dark, self-contained). Serves a pre-computed snapshot, so the
    footer shows when it was rendered and the tab re-fetches every 10 min to pick up the next snapshot.
    """
    stamp = f"as of {rendered_at} · " if rendered_at else ""
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='600'><title>WHOOP Cockpit</title><style>"
        "body{font-family:system-ui,-apple-system,sans-serif;background:#0b1120;color:#e2e8f0;margin:0 auto;padding:16px;max-width:1180px}"
        "h1{font-size:18px;margin:0 0 12px}h2{font-size:14px;color:#94a3b8;margin:0 0 10px;text-transform:uppercase;letter-spacing:.05em}"
        ".panel{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:16px;margin-bottom:14px}"
        ".stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:10px}"
        ".stat .lbl,.chart .lbl{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.05em}"
        ".stat .v{font-size:22px;font-weight:600;margin:2px 0}.sub{font-size:12px;color:#94a3b8}"
        ".caveat{background:#422006;border:1px solid #a16207;border-radius:8px;padding:8px;font-size:12px;margin:8px 0}"
        ".chips{margin:8px 0}.chip{display:inline-block;background:#1e293b;border-radius:12px;padding:2px 8px;font-size:11px;margin:2px}"
        ".chart{margin-top:12px;position:relative}.foot{color:#475569;font-size:11px;margin-top:8px}"
        ".chart svg{display:block;width:100%;height:auto}"
        ".ring-row{display:flex;align-items:center;gap:10px;margin:6px 0}"
        ".dual{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}"
        # Strava-style horizontal time-in-zone distribution
        ".zbar{display:flex;height:16px;border-radius:8px;overflow:hidden;background:#0f172a;margin-top:6px}"
        ".zbar .zseg{height:100%}"
        ".zlegend{display:flex;flex-wrap:wrap;gap:14px;margin-top:8px;font-size:12px;color:#cbd5e1}"
        ".zleg{display:flex;align-items:center;gap:5px}"
        ".zleg .zdot{width:9px;height:9px;border-radius:2px;display:inline-block}"
        ".session-card{border-top:1px solid #1f2937;padding-top:10px;margin-top:10px}"
        ".session-card:first-of-type{border-top:none;padding-top:0;margin-top:0}"
        # scrub tooltip
        ".scrub-tip{position:fixed;pointer-events:none;background:#0b1120;border:1px solid #334155;"
        "border-radius:6px;padding:4px 8px;font-size:12px;color:#e2e8f0;z-index:50;opacity:0;"
        "transform:translate(-50%,-130%);white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.4)}"
        ".scrub-tip b{color:#fff}.scrub svg{cursor:crosshair}"
        # Tier-1 story layer
        ".panel.hero{border-color:#334155}"
        ".verdict{font-size:34px;font-weight:700;line-height:1.1;margin:2px 0}"
        ".verdict-sub{font-size:15px;color:#cbd5e1;margin:2px 0 4px}"
        ".narrative{font-size:15px;line-height:1.5;background:#0f172a;border-left:3px solid #60a5fa;"
        "padding:10px 12px;border-radius:6px;margin:12px 0}"
        ".cards3{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:12px}"
        # an opened workout card breaks out to span the full row so its deep-dive isn't clipped in a 1/3 cell
        ".cards3 details.card[open]{grid-column:1/-1}"
        ".cards3 details.card[open] .big{font-size:18px}"
        ".card{background:#0f172a;border:1px solid #1f2937;border-radius:10px;padding:12px}"
        ".trend{font-size:15px;font-weight:600;margin-left:8px}"
        ".trend.up{color:#34d399}.trend.down{color:#f87171}.trend.flat{color:#94a3b8}"
        ".card .ico{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em}"
        ".card .big{font-size:22px;font-weight:600;margin:3px 0}"
        ".takeaway{font-size:12.5px;color:#93c5fd;font-style:italic;margin:-2px 0 10px}"
        ".badge{display:inline-block;border-radius:6px;padding:1px 7px;font-size:11px;font-weight:600}"
        ".badge.hard{background:#7f1d1d;color:#fecaca}"
        ".badge.mod{background:#78350f;color:#fed7aa}"
        ".badge.easy{background:#064e3b;color:#a7f3d0}"
        "details.card summary,details.workout-row summary,details.lab>summary{cursor:pointer;list-style:none}"
        "summary::-webkit-details-marker{display:none}"
        "details.workout-row{border-top:1px solid #1f2937;padding:6px 0}"
        "details.workout-row:first-of-type{border-top:none}"
        "details.workout-row>summary{padding:6px 0;font-size:14px}"
        "details.lab{margin-top:4px}"
        "details.lab>summary{font-size:14px;color:#94a3b8;font-weight:600;padding:12px;background:#111827;"
        "border:1px solid #1f2937;border-radius:12px;letter-spacing:.03em}"
        "details.lab[open]>summary{margin-bottom:12px}"
        # Tier-3 tap-to-expand trend sparklines behind the verdict
        "details.trends{margin-top:10px}details.trends>summary{cursor:pointer;color:#93c5fd;font-size:13px}"
        ".sparkrow{display:flex;align-items:center;gap:12px;margin:8px 0}"
        ".sparklbl{width:120px;font-size:12px;color:#94a3b8}.sparksvg{flex:1;max-width:220px}"
        ".sparksvg svg{width:100%;height:28px;display:block}"
        "@media (max-width:640px){.dual{grid-template-columns:1fr}.sparklbl{width:90px}}"
        "</style></head><body><h1>WHOOP Cockpit · your day, then the lab</h1>"
        f"{panels_html}"
        f"<div class='foot'>RivaFlow · self-hosted · {stamp}recomputes 6am · 9am · 6pm · 9pm</div>"
        f"{_SCRUB_SCRIPT}"
        "</body></html>"
    )


# Tier-2 — inline, dependency-free scrub interaction. Any <svg class="scrub"> carries its raw series and
# viewBox mapping as data-* attributes; on pointer move we find the nearest sample, snap a vertical line +
# dot to it, and float a value/time tooltip. No CDN, no framework — works offline in the snapshot.
_SCRUB_SCRIPT = """<div class="scrub-tip" id="scrubtip"></div><script>
(function(){
 var tip=document.getElementById('scrubtip');
 function fmtx(v,k){
  function p(n){return (n<10?'0':'')+n;}
  if(k==='clock'){var m=Math.round(v)%1440;return p(m/60|0)+':'+p(m%60);}
  if(k==='clock_h'){var m2=Math.round(v*60)%1440;return p(m2/60|0)+':'+p(m2%60);}
  if(k==='clock_hour'){return p(Math.round(v)%24)+':00';}
  var h=(k==='elapsed_h')?v:v/60,hh=h|0,mm=Math.round((h-hh)*60);if(mm===60){hh++;mm=0;}
  return hh+':'+p(mm);
 }
 document.querySelectorAll('svg.scrub').forEach(function(svg){
  var s;try{s=JSON.parse(svg.getAttribute('data-series'));}catch(e){return;}
  if(!s||s.length<2)return;
  var xlo=+svg.dataset.xlo,xhi=+svg.dataset.xhi,ylo=+svg.dataset.ylo,yhi=+svg.dataset.yhi;
  var ax=+svg.dataset.ax,pw=+svg.dataset.pw,ph=+svg.dataset.ph,pad=+svg.dataset.pad,W=+svg.dataset.w;
  var k=svg.dataset.xkind;
  var line=svg.querySelector('.scrub-line'),dot=svg.querySelector('.scrub-dot');
  function px(t){return ax+(t-xlo)/((xhi-xlo)||1)*pw;}
  function py(val){return ph-pad-(val-ylo)/((yhi-ylo)||1)*(ph-2*pad);}
  function move(ev){
   var r=svg.getBoundingClientRect(),cx=(ev.touches?ev.touches[0].clientX:ev.clientX);
   var vbx=(cx-r.left)/r.width*W;                       // client px -> viewBox x
   var t=xlo+Math.min(1,Math.max(0,(vbx-ax)/(pw||1)))*(xhi-xlo);
   var best=s[0],bd=1e18;for(var i=0;i<s.length;i++){var d=Math.abs(s[i][0]-t);if(d<bd){bd=d;best=s[i];}}
   var sx=px(best[0]),sy=py(best[1]),vbh=(svg.viewBox.baseVal.height||ph);
   line.setAttribute('x1',sx);line.setAttribute('x2',sx);line.setAttribute('opacity','0.7');
   dot.setAttribute('cx',sx);dot.setAttribute('cy',sy);dot.setAttribute('opacity','1');
   tip.innerHTML='<b>'+Math.round(best[1])+'</b> · '+fmtx(best[0],k);
   tip.style.left=(r.left+sx/W*r.width)+'px';
   tip.style.top=(r.top+sy/vbh*r.height)+'px';
   tip.style.opacity='1';
  }
  function out(){line.setAttribute('opacity','0');dot.setAttribute('opacity','0');tip.style.opacity='0';}
  svg.addEventListener('mousemove',move);svg.addEventListener('touchmove',move);
  svg.addEventListener('mouseleave',out);svg.addEventListener('touchend',out);
 });
})();
</script>"""


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
    ring = progress_or_text(
        bool(debt.get("available")), debt_progress, "", "Sleep debt (14n)"
    )
    return f'<section class="panel"><h2>Sleep</h2><div class="stats">{stats}</div>{ring}</section>'


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
            series["times"],
            series["values"],
            bands=bands,
            stroke="#e2e8f0",
            max_gap=0.34,
            xkind="clock_h",
            series_id="hr-ribbon",
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
            detail["times"],
            detail["rr_values"],
            stroke="#a78bfa",
            fill="rgba(167,139,250,0.15)",
            max_gap=3.0,
            xkind="elapsed_m",
            series_id="rr-tacho",
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
            curve["times"],
            curve["values"],
            stroke="#34d399",
            fill="rgba(52,211,153,0.18)",
            max_gap=0.34,
            xkind="elapsed_h",
            series_id="overnight-hrv",
        )
        body = f'<div class="chart"><div class="lbl">lnRMSSD · overnight (5-min buckets)</div>{chart}</div>'
    return f'<section class="panel"><h2>Overnight HRV curve</h2>{body}</section>'


def render_sleep_hr_dip(curve: dict) -> str:
    """P3.5 — HR across the detected sleep window, showing the nocturnal dip vs waking baseline."""
    if not curve.get("available"):
        body = f'<div class="sub">{esc(curve.get("reason", "no overnight sleep window detected yet"))}</div>'
    else:
        chart = svg_area_line(
            curve["times"],
            curve["values"],
            stroke="#818cf8",
            fill="rgba(129,140,248,0.15)",
            max_gap=0.34,
            xkind="elapsed_h",
            series_id="sleep-hr",
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
    return (
        f'<section class="panel"><h2>Sleep HR &amp; nocturnal dip</h2>{body}</section>'
    )


def render_respiratory(trace: dict) -> str:
    """P3.5 — Respiratory rate (breaths/min) across rest windows through the day."""
    if not trace.get("available"):
        body = f'<div class="sub">{esc(trace.get("reason", "not enough clean resting RR yet"))}</div>'
    else:
        chart = svg_area_line(
            trace["times"],
            trace["values"],
            stroke="#f472b6",
            fill="rgba(244,114,182,0.15)",
            max_gap=0.5,
            xkind="elapsed_h",
            series_id="respiratory",
        )
        body = f'<div class="chart"><div class="lbl">Breaths/min · resting windows</div>{chart}</div>'
    return f'<section class="panel"><h2>Respiratory trace</h2>{body}</section>'


def render_stress_ribbon(ribbon: dict) -> str:
    """P3.5 — HRV-vs-baseline stress across the day as a colored band."""
    if not ribbon.get("available"):
        body = f'<div class="sub">{esc(ribbon.get("reason", "not enough HR history for a baseline yet"))}</div>'
    else:
        bands: list[tuple[float, float, str]] = [
            (0.0, 34.0, "#34d399"),
            (34.0, 67.0, "#fbbf24"),
            (67.0, 100.0, "#f87171"),
        ]
        chart = svg_area_line(
            ribbon["times"],
            ribbon["values"],
            bands=bands,
            stroke="#e2e8f0",
            max_gap=1.5,
            xkind="clock_hour",
            series_id="stress",
        )
        body = f'<div class="chart"><div class="lbl">Stress vs baseline (0–100)</div>{chart}</div>'
    return f'<section class="panel"><h2>Stress ribbon</h2>{body}</section>'


_ZONE_META = {
    1: ("#60a5fa", "Z1"),
    2: ("#34d399", "Z2"),
    3: ("#a3e635", "Z3"),
    4: ("#fbbf24", "Z4"),
    5: ("#f87171", "Z5"),
}


def _zone_bar_html(zone_secs: dict) -> str:
    """Strava/Garmin-style horizontal time-in-zone distribution: one full-width stacked bar (segments
    proportional to seconds in each zone) plus a legend row with per-zone minutes and percentage.
    """
    total = sum(zone_secs.values()) or 1
    segs = ""
    legend = ""
    for z in range(1, 6):
        color, name = _ZONE_META[z]
        secs = zone_secs.get(z, 0)
        pct = secs / total * 100
        if pct > 0:
            segs += (
                f'<div class="zseg" style="width:{pct:.1f}%;background:{color}" '
                f'title="{name}: {secs // 60}m {secs % 60}s ({pct:.0f}%)"></div>'
            )
        legend += (
            f'<div class="zleg"><span class="zdot" style="background:{color}"></span>'
            f'{name} <b>{secs // 60}m</b> <span class="sub">{pct:.0f}%</span></div>'
        )
    return f'<div class="zbar">{segs}</div><div class="zlegend">{legend}</div>'


def _session_card_html(s: dict, idx: int = 0) -> str:
    a = s.get("analytics", {})
    if not a.get("available"):
        return (
            '<div class="session-card">'
            f'<div class="sub">{esc(s.get("label", "Session"))} · {esc(s.get("day", ""))} — '
            f'{esc(a.get("reason", "no HR captured"))}</div></div>'
        )
    load, hardness = session_load_hardness(a)
    curve = svg_area_line(
        a.get("times", []),
        a.get("values", []),
        h=150,
        stroke="#f87171",
        fill="rgba(248,113,113,0.16)",
        max_gap=2.0,
        xkind="elapsed_m",
        series_id=f"session-{idx}",
    )
    drift = a.get("hrr")
    drift_sub = f"{drift} bpm recovery in 60s" if drift is not None else "recovery n/a"
    duration_min = a.get("duration_sec", 0) // 60
    stats_html = (
        stat("Duration", f"{duration_min}min", str(s.get("day", "")))
        + stat("Avg HR", str(a.get("avg_hr", "—")), f'peak {a.get("max_hr", "—")}')
        + stat("Load", f"{load}/21", hardness)
        + stat("HR recovery", f'{drift if drift is not None else "—"}', drift_sub)
    )
    return (
        '<div class="session-card">'
        f'<div class="stats">{stats_html}</div>'
        f'<div class="chart"><div class="lbl">Heart rate · elapsed</div>{curve}</div>'
        f'<div class="chart"><div class="lbl">Time in zones</div>{_zone_bar_html(a.get("hr_zone_secs", {}))}</div>'
        "</div>"
    )


def render_session_deepdives(sessions: list[dict]) -> str:
    """P3.5 — MUST-HAVE: per-session (BJJ + CrossFit) HR curve, time-in-zones, and HR-drift/decoupling."""
    if not sessions:
        body = '<div class="sub">No recent sessions with WHOOP HR coverage yet.</div>'
    else:
        body = "".join(_session_card_html(s, idx=i) for i, s in enumerate(sessions[:5]))
    return f'<section class="panel"><h2>Session deep-dives</h2>{body}</section>'


# ── P6 "Story over Lab" — a glanceable Tier-1 band on top of the technical Lab ──


def session_load_hardness(analytics: dict) -> tuple[float, str]:
    """Compressed 0–21 cardio-load + a HARD/MODERATE/EASY label from a session's zone-seconds (same TRIMP
    weighting daily_cardio_load uses). Lives here (not analytics) so both the renderer and narrative can
    reuse it without an import cycle. Returns (0.0, 'EASY') on empty/missing zone data.
    """
    zone_secs = analytics.get("hr_zone_secs", {}) or {}
    weights = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
    raw = sum(weights.get(int(z), 0) * (secs / 60.0) for z, secs in zone_secs.items())
    load = round(min(21.0, 6.0 * log1p(raw / 20.0)), 1)
    if load >= 12:
        return load, "HARD"
    if load >= 6:
        return load, "MODERATE"
    return load, "EASY"


def _hardness_badge(hardness: str) -> str:
    cls = {"HARD": "hard", "MODERATE": "mod", "EASY": "easy"}.get(hardness, "easy")
    return f'<span class="badge {cls}">{esc(hardness)}</span>'


def takeaway(text: str) -> str:
    """A one-line plain-English takeaway strip — the glance altitude that sits above each Lab panel's chart."""
    return f'<div class="takeaway">{esc(text)}</div>' if text else ""


def inject_takeaway(panel_html: str, text: str) -> str:
    """Slot a plain-English takeaway line right under a panel's heading, without touching the 15 renderers."""
    if not text:
        return panel_html
    marker = "</h2>"
    idx = panel_html.find(marker)
    if idx == -1:
        return panel_html
    cut = idx + len(marker)
    return panel_html[:cut] + takeaway(text) + panel_html[cut:]


def render_lab_section(panels_html: str) -> str:
    """Tier-2 — collapse the full 15-panel technical Lab behind one tap, so Tier-1 is the default view."""
    return (
        '<details class="lab"><summary>🔬 Show the full lab — 15 technical panels ▾</summary>'
        f"{panels_html}</details>"
    )


def _trend_arrow(readiness: dict) -> str:
    """A ▲/▼/→ arrow next to the verdict, driven by the HRV contributor's direction (already in the
    readiness dict — no extra query). Up HRV is good (green), down is worse (red)."""
    for c in readiness.get("contributors") or []:
        sig = str(c.get("signal", "") or c.get("label", "")).lower()
        if "hrv" in sig or "rmssd" in sig:
            d = str(c.get("direction", "")).lower()
            if any(k in d for k in ("up", "rising", "▲", "↑", "higher")):
                return '<span class="trend up" title="HRV trending up">▲</span>'
            if any(k in d for k in ("down", "falling", "▼", "↓", "lower")):
                return '<span class="trend down" title="HRV trending down">▼</span>'
            return '<span class="trend flat" title="HRV steady">→</span>'
    return ""


def _spark_row(
    label: str,
    values: list[float],
    unit: str = "",
    stroke: str = "#60a5fa",
    lower_is_better: bool = False,
) -> str:
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return ""
    delta = vals[-1] - vals[0]
    arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "→")
    # colour by GOODNESS, not raw direction: a falling resting HR is good (green), not alarming (red)
    good = (delta < 0) if lower_is_better else (delta > 0)
    cls = "flat" if delta == 0 else ("up" if good else "down")
    return (
        '<div class="sparkrow">'
        f'<span class="sparklbl">{esc(label)}</span>'
        f'<span class="sparksvg">{svg_sparkline(values, w=200, h=28, stroke=stroke)}</span>'
        f'<span class="trend {cls}">{arrow} {esc(round(vals[-1], 1))}{esc(unit)}</span>'
        "</div>"
    )


def _hero_html(readiness: dict, trends: dict | None = None) -> str:
    state = str(readiness.get("state", "Building"))
    accent = _ACCENT.get(state, "#94a3b8")
    headline = esc(readiness.get("headline", ""))
    caveat = readiness.get("caveat")
    caveat_html = f'<div class="caveat">⚠️ {esc(caveat)}</div>' if caveat else ""
    # Tier-3 — tap to reveal the last-14 history behind today's verdict (data already computed; no new query)
    trends = trends or {}
    rows = (
        _spark_row("HRV (lnRMSSD)", trends.get("hrv", []), stroke="#34d399")
        + _spark_row(
            "Resting HR",
            trends.get("rhr", []),
            " bpm",
            stroke="#f472b6",
            lower_is_better=True,
        )
        + _spark_row("Sleep", trends.get("sleep", []), " h", stroke="#818cf8")
    )
    history = (
        f'<details class="trends"><summary>▸ 14-day trend</summary>{rows}</details>'
        if rows
        else ""
    )
    return (
        f'<div class="ico">Today\'s readiness</div>'
        f'<div class="verdict" style="color:{accent}">{esc(state)}{_trend_arrow(readiness)}</div>'
        f'<div class="verdict-sub">{headline}</div>'
        f"{caveat_html}{history}"
    )


def _sleep_card(night: dict, dip: dict, need_hours: float) -> str:
    if not night.get("available"):
        return (
            '<div class="card"><div class="ico">🌙 Last night</div>'
            '<div class="big">—</div><div class="sub">building — no sleep window detected yet</div></div>'
        )
    dur = night.get("duration_hours")
    onset = dip.get("onset", "—") if dip.get("available") else "—"
    offset = dip.get("offset", "—") if dip.get("available") else "—"
    dip_pct = dip.get("dip_pct", "—") if dip.get("available") else "—"
    short = round(need_hours - dur, 1) if isinstance(dur, (int, float)) else None
    if short is not None and short >= 0.5:
        vs_need = f"{short}h under your {need_hours:g}h need"
    elif short is not None:
        vs_need = f"on your {need_hours:g}h need"
    else:
        vs_need = ""
    return (
        '<div class="card"><div class="ico">🌙 Last night</div>'
        f'<div class="big">{esc(dur)}h</div>'
        f'<div class="sub">{esc(onset)} → {esc(offset)}</div>'
        f'<div class="sub">{esc(vs_need)}</div>'
        f'<div class="sub">nocturnal dip {esc(dip_pct)}%</div></div>'
    )


def _workout_card(last_workout: dict | None) -> str:
    if not last_workout:
        return (
            '<div class="card"><div class="ico">🏋️ Last workout</div>'
            '<div class="big">—</div><div class="sub">no recent session captured</div></div>'
        )
    label = str(last_workout.get("label", "Session"))
    day = str(last_workout.get("day", ""))
    a = last_workout.get("analytics", {})
    if not a.get("available"):
        return (
            '<div class="card"><div class="ico">🏋️ Last workout</div>'
            f'<div class="big">{esc(label)}</div>'
            f'<div class="sub">{esc(day)} — {esc(a.get("reason", "no HR captured"))}</div></div>'
        )
    load, hardness = session_load_hardness(a)
    dur_min = a.get("duration_sec", 0) // 60
    return (
        '<details class="card"><summary>'
        '<div class="ico">🏋️ Last workout · tap for deep dive</div>'
        f'<div class="big">{esc(label)} {_hardness_badge(hardness)}</div>'
        f'<div class="sub">{esc(day)} · {dur_min}min · load {esc(load)}/21</div>'
        f'<div class="sub">avg {esc(a.get("avg_hr", "—"))} · peak {esc(a.get("max_hr", "—"))} bpm</div>'
        f"</summary>{_session_card_html(last_workout, idx=900)}</details>"
    )


def _guidance_card(strain: dict, readiness: dict, is_sabbath: bool) -> str:
    if is_sabbath:
        return (
            '<div class="card"><div class="ico">⚡️ Today</div>'
            '<div class="big">Rest</div><div class="sub">Sabbath — rest is prescribed</div></div>'
        )
    if not strain.get("available"):
        return (
            '<div class="card"><div class="ico">⚡️ Today</div>'
            '<div class="big">—</div>'
            f'<div class="sub">{esc(strain.get("reason", "building your baseline"))}</div></div>'
        )
    call = {
        "Prime": "Green light — you can push",
        "Balanced": "Train as planned",
        "Strained": "Ease off — technical over hard",
        "Rundown": "Recovery day — keep it light",
    }.get(str(readiness.get("state", "")), "Train as planned")
    return (
        '<div class="card"><div class="ico">⚡️ Today\'s guidance</div>'
        f'<div class="big">{esc(strain.get("target_load", "—"))}/21</div>'
        f'<div class="sub">{esc(call)}</div>'
        f'<div class="sub">usual {esc(strain.get("chronic_load", "—"))}</div></div>'
    )


def render_today_story(
    readiness: dict,
    narrative: str,
    night: dict,
    dip: dict,
    need_hours: float,
    last_workout: dict | None,
    strain: dict,
    is_sabbath: bool,
    trends: dict | None = None,
) -> str:
    """Tier-1 — the glanceable 'Today' band: hero verdict + one honest data-story + three essential cards
    (last night's sleep, last workout, today's guidance). The plain-language layer over the technical Lab.
    `trends` (optional) drives the hero's tap-to-expand 14-day history sparklines.
    """
    cards = (
        _sleep_card(night, dip, need_hours)
        + _workout_card(last_workout)
        + _guidance_card(strain, readiness, is_sabbath)
    )
    return (
        '<section class="panel hero">'
        f"{_hero_html(readiness, trends)}"
        f'<div class="narrative">{esc(narrative)}</div>'
        f'<div class="cards3">{cards}</div>'
        "</section>"
    )


def _workout_row(s: dict, idx: int = 0) -> str:
    label = str(s.get("label", "Session"))
    day = str(s.get("day", ""))
    a = s.get("analytics", {})
    if not a.get("available"):
        return (
            '<details class="workout-row"><summary>'
            f"{esc(day)} · {esc(label)} — {esc(a.get('reason', 'no HR captured'))}"
            f"</summary>{_session_card_html(s, idx=idx)}</details>"
        )
    load, hardness = session_load_hardness(a)
    dur_min = a.get("duration_sec", 0) // 60
    return (
        '<details class="workout-row"><summary>'
        f"{esc(day)} · {esc(label)} · {dur_min}min · load {esc(load)}/21 {_hardness_badge(hardness)}"
        f"</summary>{_session_card_html(s, idx=idx)}</details>"
    )


def render_workouts_list(sessions: list[dict]) -> str:
    """Ruby's 'drill into previous workouts' ask — the last ~10 sessions, each a tap-to-expand <details> row
    that opens its full deep-dive inline. Pure HTML disclosure; charts scrub via the page script.
    """
    if not sessions:
        body = '<div class="sub">No recent sessions with WHOOP HR coverage yet.</div>'
    else:
        body = "".join(
            _workout_row(s, idx=100 + i) for i, s in enumerate(sessions[:10])
        )
    return f'<section class="panel"><h2>Workouts</h2>{body}</section>'

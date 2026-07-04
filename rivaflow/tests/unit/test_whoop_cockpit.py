"""P3.1 — cockpit renderer (pure string/SVG generation, no DB)."""

from __future__ import annotations

from rivaflow.core.whoop_cockpit import (
    esc,
    render_cockpit_page,
    render_recovery_load,
    svg_acwr_ribbon,
    svg_bars,
    svg_sparkline,
)

READY = {
    "state": "Prime",
    "headline": "push",
    "caveat": "green != healthy",
    "contributors": [
        {"label": "HRV", "signal": "hrv", "direction": "supports recovery"}
    ],
}
STRAIN = {"available": True, "target_load": 12.0, "band": [10.0, 14.0], "capped": False}
ACWR = {"available": True, "ratio": 1.1, "zone": "sweet-spot"}
CARDIO = [{"cardio_load": 8.0}, {"cardio_load": 11.0}, {"cardio_load": 9.5}]
RC = {"available": True, "headline": "each unit of load costs next-day recovery"}


def test_esc_escapes_html():
    assert esc("<script>") == "&lt;script&gt;"


def test_sparkline_valid_svg():
    s = svg_sparkline([1, 2, 3, 2, 4])
    assert s.startswith("<svg") and "polyline" in s and s.endswith("</svg>")


def test_sparkline_handles_short_series():
    assert "<svg" in svg_sparkline([])
    assert "<svg" in svg_sparkline([5])


def test_bars_valid_svg():
    s = svg_bars([1, 4, 2])
    assert s.count("<rect") == 3


def test_acwr_ribbon_has_marker_and_bands():
    s = svg_acwr_ribbon(1.6)  # high-risk zone
    assert "<line" in s and s.count("<rect") >= 3  # base + sweet + danger


def test_render_recovery_load_includes_key_pieces():
    html = render_recovery_load(READY, STRAIN, ACWR, CARDIO, RC)
    assert "Recovery &amp; Load" in html
    assert "Prime" in html
    assert "12.0/21" in html  # strain target
    assert "sweet-spot" in html  # acwr zone
    assert "green != healthy" in html or "green" in html  # caveat surfaced
    assert "<svg" in html  # charts rendered


def test_caveat_only_when_present():
    no_caveat = render_recovery_load(
        {"state": "Strained", "headline": "ease"}, STRAIN, ACWR, CARDIO, RC
    )
    assert "caveat" not in no_caveat.lower() or "⚠️" not in no_caveat


def test_recovery_cost_fallback_when_unavailable():
    html = render_recovery_load(READY, STRAIN, ACWR, CARDIO, {"available": False})
    assert "needs more paired days" in html


def test_page_wraps_panels_and_refreshes():
    page = render_cockpit_page("<section>x</section>")
    assert page.startswith("<!doctype html>")
    assert "refresh" in page and "<section>x</section>" in page


def test_render_escapes_dynamic_headline():
    evil = {"state": "Prime", "headline": "<img src=x onerror=alert(1)>"}
    html = render_recovery_load(
        evil, {"available": False}, {"available": False}, [], {"available": False}
    )
    assert "<img src=x" not in html and "&lt;img" in html

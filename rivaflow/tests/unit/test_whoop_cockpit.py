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


# --- P3.2–P3.4 panels -----------------------------------------------------

from rivaflow.core.whoop_cockpit import (  # noqa: E402
    render_behaviour,
    render_data_integrity,
    render_hrv_lab,
    render_prevention_log,
    render_sleep,
    render_trends,
)


def test_hrv_lab_available():
    hl = {
        "available": True,
        "frequency_domain": {
            "lf_hf": 1.2,
            "hf": 500,
            "note": "descriptive, NOT sympatho-vagal",
        },
        "poincare": {"sd2_sd1_ratio": 1.8},
        "quality": {"artifact_pct": 2.0, "intervals_used": 300},
    }
    html = render_hrv_lab(hl, {"available": True, "alpha1": 0.8, "zone": "aerobic"})
    assert "HRV Lab" in html and "NOT sympatho-vagal" in html and "DFA" in html


def test_hrv_lab_unavailable():
    html = render_hrv_lab(
        {"available": False, "reason": "no window"}, {"available": False, "reason": "x"}
    )
    assert "no window" in html


def test_data_integrity_panel():
    cov = {
        "summary": {"rr_coverage_pct": 80.0, "days_sufficient": 8, "days_total": 10},
        "days": [{"rr_minutes": 5}, {"rr_minutes": 7}],
    }
    html = render_data_integrity(cov)
    assert "Data integrity" in html and "80.0%" in html and "<svg" in html


def test_sleep_panel():
    s = {
        "debt": {
            "available": True,
            "debt_hours": 3.0,
            "recent_avg_hours": 7.5,
            "need_hours": 9,
            "headline": "3h debt",
        },
        "regularity": {"available": True, "score": 82, "headline": "regular"},
    }
    html = render_sleep(s)
    assert "Sleep" in html and "3.0h" in html and "82" in html


def test_trends_panel_has_cvage_caveat():
    lon = {
        "vo2max": {"available": True, "range": [48, 55]},
        "cardio_age": {"available": True, "cardio_age_proxy": 40},
    }
    html = render_trends(
        lon,
        {"resilience": {"available": True, "level": "Strong"}},
        {"available": True, "acrophase_hour": 15},
        {"available": True, "headline": "HRV improving"},
    )
    assert "Trends" in html and "PROXY" in html and "Strong" in html


def test_prevention_log_panel():
    rows = [{"day": "2026-06-10", "tier": "amber", "headline": "watch"}]
    html = render_prevention_log(rows, {"available": True, "tier": "green"})
    assert (
        "Baseline-Deviation log" in html
        and "2026-06-10" in html
        and "not clinical data"
        in html.replace("conversation, not clinical", "not clinical data")
        or "conversation" in html
    )


def test_behaviour_panel_empty_and_populated():
    assert "Tag days" in render_behaviour([])
    effects = [
        {
            "available": True,
            "tag": "alcohol",
            "magnitude": "large",
            "delta": -0.5,
            "cohens_d": -1.2,
            "n_yes": 4,
        }
    ]
    html = render_behaviour(effects)
    assert "alcohol" in html and "large" in html

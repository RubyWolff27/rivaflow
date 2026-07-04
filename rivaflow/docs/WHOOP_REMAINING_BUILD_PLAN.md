# WHOOP-Alternative — Remaining Build Plan (Phased) · 2026-07-04

The compute layer is done: all 20 buildable engines (B0–B19) are implemented, tested, and on `main`,
with B6 (prevention) now complete to spec. B20 (AFib) is correctly deferred (decode-gated). What remains
is **surfaces, plumbing, and validation-with-real-data — not algorithms.** This is the phased plan to finish.

**Working rhythm (unchanged):** one PR per phase (or sub-phase) → CI green (Backend Tests + Code Quality +
Dependency Scan + Frontend) → merge. Each phase is independently shippable and leaves `main` green.

Companion docs: `WHOOP_CURRENT_STATE.md`, `WHOOP_FUTURE_STATE_PLAN.md`, `WHOOP_RESEARCH_REFERENCES.md`.

## Phase overview

| Phase | Goal | Depends on | Ships |
|---|---|---|---|
| **P1 — Capture & Labels** | The keystone tagging path (journal → tags) | — | B11 real output + B6 tunable |
| **P2 — Prevention: tune & deliver** | Tune thresholds on real tags + the anti-anxiety delivery layer | P1 | B6 armed in a channel |
| **P3 — Web deep-dive cockpit** | Render the 8 panels from existing endpoints | P1 (for prevention log) | The analyst cockpit |
| **P4 — Slim app (iOS)** | Render the new summary fields on the phone | — | The display side |
| **P5 — Verify & close out** | End-to-end acceptance checks + doc refresh | P1–P4 | Spec conformance proven |

P3 and P4 can run in parallel with each other after P1. P2 gates on P1. P5 is last.

---

## P1 — Capture & Labels (the keystone)

**Why first:** the one true dependency. A tagging path feeds *both* B11 behaviour correlation *and* B6's
validation/tuning gate (illness-onset labels). Everything downstream that needs "what happened that day"
waits on this. It's small, well-scoped plumbing.

**Build:**
- **P1.1 — Storage.** Migration `whoop_tags (user_id, day DATE, tag TEXT, created_at)` + `WhoopTagRepository`
  (add/list/remove). ⚠️ Keep the migration comments **semicolon-free** (the 107 bug).
- **P1.2 — Capture route.** `POST /whoop/tag {day, tag}` + `GET /whoop/tags?from&to` + `DELETE`. Tags are
  free-text but a small suggested vocab (alcohol, late-training, ill, poor-sleep, travel, sabbath-rest).
- **P1.3 — Wire into analytics.** `behaviour_correlation` reads `tagged_days` from the repo; a new
  `illness_dates` helper feeds `prevention_validation`. Add `GET /whoop/behaviour?tag=alcohol`.

**Acceptance:** a day can be tagged and read back; `/whoop/behaviour?tag=…` returns real effect sizes;
`prevention_validation` runs against real `ill`-tagged onsets (not a passed-in set).

---

## P2 — Prevention: tune & deliver

**Why:** B6's engine + validation gate are complete, but (a) thresholds need tuning on real labels and
(b) nothing *delivers* the tiers yet, and the spec mandates an anti-anxiety **once-daily digest**, not a
live-refreshing red light.

**Build:**
- **P2.1 — Tune.** Once P1 has accumulated ~weeks of tags, run `prevention_validation`; adjust
  AMBER_Z/RED_Z/CUSUM/drift to hit the acceptance target (≥2 onsets caught, <1 false amber/week); record the
  tuned values + the validation result in the PRD/doc. Until enough labels exist, the engine stays in
  "watch-only" (compute + log, no channel fire) — state that honestly.
- **P2.2 — Delivery layer.** A once-daily morning compile (readiness + strain target + prevention tier),
  with **alert cooldown** (no re-alert on the same signal within N days) and **tier→channel routing**:
  amber/red → safety notification (fires Sunday); performance nudges → Sabbath-silenced. Reuse the existing
  notification/scheduler infra. Health flags are a digest, never a 2-min live refresh.

**Acceptance:** validation passes on real data *or* reports an honest "insufficient labels — watch-only"
state; exactly one morning digest is produced per day; no live-refresh health flag exists.

---

## P3 — Web deep-dive cockpit (the analyst surface)

**Why:** every panel's *data* already exists as JSON endpoints; only the rendered cockpit is missing. All
compute stays server-side — the web app only renders. Extends `/whoop/view`. Sub-phase by panel group so
each is a shippable PR.

- **P3.1 — Recovery & Load.** Readiness (+ contributors + green≠healthy caveat), strain target, ACWR ribbon
  (danger band shaded), cardio-load bars, recovery-cost coupling. Endpoints: `/readiness`, `/strain-target`,
  `/acwr`, `/recovery-cost`.
- **P3.2 — HRV Lab + Data integrity.** lnRMSSD/SDNN/pNN50 envelopes, LF/HF (labelled descriptive), Poincaré,
  DFA-α1 (experimental), coverage/RR-coverage + artifact-% chart. Endpoints: `/hrv-lab`, `/dfa`, coverage
  block in `/summary`.
- **P3.3 — Sleep + Trends & Longevity.** Duration vs >9h need, debt curve, regularity, nocturnal dip; RHR/HRV/
  VO₂max arrows, CV-age *proxy* (caveated, no alarming arrows), resilience, circadian; weekly/monthly
  assessment narrative. Endpoints: `/sleep-analysis`, `/longevity`, `/resilience`, `/circadian`, `/assessment`.
- **P3.4 — Prevention log + Behaviour.** Tier timeline (`/prevention-backtest`) with driving signals +
  a **neutral, validation-stamped personal data export** (not "physician-shareable"); behaviour effect sizes
  from P1. Endpoints: `/prevention`, `/prevention-backtest`, `/behaviour`.

**Acceptance:** each panel renders from live endpoints only (zero client compute); the export carries its
validation status + blind-spot caveats.

---

## P4 — Slim app (iOS)

**Why:** `whoop_summary` now returns the new fields (strain target, coverage, max-HR, prevention tier) but
`SlimHomeView` still renders the old set. The phone stays slim — fetch `/whoop/summary`, render, no compute.

**Build:** extend `SlimHomeView` to show: readiness state + **green≠healthy caveat**, strain target + headroom,
an RR-coverage indicator (so a charging-night gap is visible), and the prevention tier (amber/red only, with
the reframed copy). Repo `RubyWolff27/goose-whoop5`.

**Acceptance:** the phone displays the new fields from `/summary`; the green readiness card shows the caveat;
no client-side compute added.

---

## P5 — Verify & close out

- **P5.1 — Acceptance harness.** For each non-deferred build, verify end-to-end against its matrix "done" bar
  on real data (e.g. B1 "zones shift for Ruby", B2 verdict shape, B3 excludes a real charging night). A small
  `scripts/verify_whoop_builds.py` that hits the endpoints for the real user and asserts each criterion.
- **P5.2 — Doc refresh.** Update `WHOOP_CURRENT_STATE.md` to list the shipped builds/endpoints; mark
  `WHOOP_FUTURE_STATE_PLAN.md` matrix rows shipped; note the standing deferrals (B20 AFib, R22/K21 decode).

**Acceptance:** every non-deferred build passes its acceptance criterion on real data; the docs match reality.

---

## Standing deferrals (not in scope — by design)
- **B20 — AFib / irregular-rhythm screen:** decode-gated on the locked R22 raw-PPG SQI. Never in the
  always-fire channel; revisit only in the R22-decode era.
- **R22 / K21 decode:** locked; a future decode retroactively unlocks SpO₂ / temperature / sleep-staging from
  banked raw history.

## Suggested order
**P1 → P2** (sequential; P2 gates on real tags) · **P3 and P4 in parallel** after P1 · **P5** last.
P1 is the highest-leverage single build — it unblocks B11's real output *and* B6's tuning at once.

*Phased plan, 2026-07-04. Owner surfaces: `rivaflow` (backend/web), `goose-whoop5` (iOS).*

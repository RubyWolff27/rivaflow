# WHOOP-Alternative — Current State (Technical) · 2026-07-04 (Fable second-pass review)

A factual record of what we have built and what our data can support. Companion docs:
`WHOOP_SERVERSIDE_ARCHITECTURE.md` (design), `WHOOP_RESEARCH_REFERENCES.md` (brand research + 146 sources),
`WHOOP_FUTURE_STATE_PLAN.md` (research-backed roadmap).

> **⚠️ Safety & Scope (applies to every metric below and every surface that renders them).**
> This is an experimental, personal **n-of-1 wellness** system. It is **not a medical device**, not diagnostic,
> and not intended to detect, prevent, or treat any disease. Nothing here is medical advice — seek care for
> symptoms regardless of what any score says. Metrics are derived from **firmware-emitted optical pulse intervals**,
> not ECG or validated clinical pipelines, and are blind to temperature and blood oxygen. The personal build is
> **firewalled** from anything shipped to other RivaFlow users: no health/illness/rhythm feature ships to third
> parties without medical-device review.

## 1. Architecture
**Self-hosted, server-side.** The phone is a thin **capture + display** client; the RivaFlow VPS is the **brain**.
```
WHOOP 5.0 ─BLE→ Goose iOS app (capture+upload ONLY) ─HTTPS→ RivaFlow VPS ─compute→ /whoop/summary + /view
```
Why (decided 2026-07-04): WHOOP/Oura run proprietary models in their cloud; reproducing that *on-device* hit
the wall of the un-cracked R22/K21 decode. Server-side lets us iterate algorithms in a ~2-min GitOps deploy
with no phone rebuild.

## 2. What we CAPTURE (the biometric surface)
Pipeline: WHOOP 5 → BLE → iOS `WhoopVpsUploader` (GooseBLEClient.swift) → `POST /api/v1/whoop/ingest`
(Bearer, Keychain token) → `WhoopRepository` → Postgres (migration `109_whoop_ingest`). Raw-first + idempotent
(ON CONFLICT DO NOTHING; dedup on `sha256(frame_hex)` / ts).

The upload batch contains **only four arrays** — that is the entire real-time biometric surface:
| Store | Source | Cadence | Notes |
|---|---|---|---|
| `whoop_raw_frames` | **every** BLE notification (proprietary `fd4b0001-0007`, `61080001-0007`, std HR `0x2A37`, battery) | as emitted | Immutable source of truth; hex + char_uuid + fractional-second ISO ts; `decoded=FALSE` for the proprietary optical/IMU streams |
| `whoop_hr` | standard `0x2A37` Heart Rate Measurement (parsed client-side) | ~1 Hz | the only decoded HR stream |
| `whoop_rr` | RR-intervals off `0x2A37` (1/1024 s → ms) | per beat | the beat-to-beat tachogram — our richest asset, **with the caveat below** |
| `whoop_battery` | `0x2A19`/`0x2BED` | on change | soc + charging (for wear-time/coverage) |

**⚠️ What the RR series actually is (load-bearing caveat).** These are **optical pulse-to-pulse intervals (PPI)**
that WHOOP's firmware already beat-detected and emitted over the standard `0x2A37` field — **not ECG RR**. They are
*decoded* (they come off the standard HR characteristic, not the locked proprietary stream), but they are still
optical-derived and **quality-bounded by WHOOP's undisclosed on-strap beat detection**. The **raw optical waveform**
needed to compute an independent Signal-Quality Index is exactly the **locked R22 stream**, so we inherit WHOOP's
beat-detection artifact (pulse-transit jitter, missed/extra beats, ectopy) with **no independent quality flag to
reject it**. Every RR-derived metric downstream (RMSSD, frequency-domain, Poincaré, resp-rate) is bounded by this.

**⚠️ Two kinds of night — do not conflate.** RR exists **only while the phone holds a live BLE connection** to the
strap. The phone HR-history uploader backfills up to 48 h of WHOOP's on-device store on connect, but that store is
**coarse HR-only** (minute-level aggregates, **no RR**). So a night is either a **live window** (1 Hz HR + per-beat RR,
usable for HRV) or a **backfilled window** (coarse HR trend only, **not** usable for HRV/resp-rate/HRR). Overnight —
the window readiness and the prevention engine depend on — is exactly when the phone is most likely charging away
from the strap, so RR may be structurally under-supplied on the nights that matter most.

Current volumes (**single-session snapshot, not steady-state coverage**): ~325k raw frames / ~19k HR (~5 h of live
signal) / ~13k RR (~3.6 h). This is roughly one partial session — **far short of the multi-week record** the future
baselines (14–21 d, 28 d ACWR, 5-day cold-start) assume. Coverage-in-days, tracked separately for HR and RR, is the
real gate on those builds — see `WHOOP_FUTURE_STATE_PLAN.md`.

## 3. What we COMPUTE today (server-side, `rivaflow/core/whoop_analytics.py`)
All bucketed + displayed in **Australia/Melbourne** local time.
| Metric | Endpoint | Method |
|---|---|---|
| Readiness | `/whoop/readiness` | at-rest **ln**RMSSD vs rolling baseline z-score (Plews/Buchheit); Sabbath-silent; 5-day cold-start |
| HRV (RMSSD) | `/whoop/hrv` | resting-band RR, successive-diff; artifact handling below |
| Resting HR | `/whoop/resting-hr` | ⚠️ currently 5th-percentile of the day's HR — **not** the nocturnal-minimum definition competitors use (see limitation) |
| Sleep | `/whoop/sleep` | HR-based window (5-min-bucket median + wake-bridging) + quality vs >9 h need |
| Respiratory rate | `/whoop/respiratory` | RR oscillation (RSA), zero-crossing over resting RR — ⚠️ **needs-validation** (crude vs a band-passed estimate; see below) |
| Cardio load / strain | `/whoop/cardio-load` | HR-zone TRIMP, ~0–21 scale |
| Stress | `/whoop/stress` | HR elevation within HR-reserve |
| BJJ session | `/whoop/session-analytics` | HR zones, avg/max, best-60 s recovery |
| One-call rollup | `/whoop/summary` | all of the above |
| Dashboard | `/whoop/view?key=…` | server-rendered HTML (6 cards, 2-min refresh — see anxiety-loop note in the plan) |
| The **slim iOS app** (`SlimHomeView`) | — | fetches `/whoop/summary` and renders it — no on-device compute |

**Known limitations (each is a P0/P1 fix in the plan):**
- **`MAX_HR = 190` is hardcoded** — this is a **~30 yo default (220−30)**, ~13 bpm above Ruby's age-predicted ~177
  (Tanaka 208−0.7·44 ≈ 177; 220−age ≈ 176). It distorts every zone/strain/stress computation.
- **HRV baseline math should run on the log scale.** RMSSD is right-skewed/log-normal; z-scores and baselines
  belong on **lnRMSSD** (as Plews/Buchheit and WHOOP do) or they over-flag low-HRV days and under-flag high ones.
- **Resting band + artifact filter are too crude for a bradycardic athlete.** The current resting band and a fixed
  absolute successive-difference drop clip genuine slow nocturnal beats and let single-ectopic jumps inflate RMSSD.
  Target: widen the bradycardic bound (~36–133 bpm / percentile-adaptive to his own nocturnal minimum) and use a
  **relative (Malik-style, >20%) filter + beat interpolation**, reporting the artifact-correction rate per value.
- **RHR is a 24 h percentile, not nocturnal.** Redefine as lowest sustained nocturnal HR (rolling 5-min minimum in
  the sleep window), optionally with the timing of the minimum (Oura Recovery-Index style).
- **No independent signal-QC gate exists yet** — the only defence is the diff-drop above. A QC/characterisation
  build is the true first step of the roadmap.

## 3b. SHIPPED roadmap — B0–B19 (2026-07-04, the reproducible core)
The full `WHOOP_FUTURE_STATE_PLAN.md` roadmap is **built, tested (CI green), and on `main`** — 16 pure
core modules + 35 `/whoop` endpoints. All compute server-side; the phone and web only render.

| Build | Module | Endpoint(s) |
|---|---|---|
| B0 signal-QC gate | `core/rr_quality.py` | (upstream of every metric) |
| B1 Max-HR calibration | `core/max_hr.py` | `/summary.max_hr` |
| B2 Multi-input Readiness | `core/readiness.py` | `/readiness` |
| B3 RR-coverage guard | `core/coverage.py` | `/summary.coverage` |
| B4 HRV Lab (freq + Poincaré) | `core/hrv_spectral.py` | `/hrv-lab`, `/dfa` |
| B5 Strain Target | `core/strain_target.py` | `/strain-target` |
| B6 Baseline-Deviation Watch | `core/prevention.py` | `/prevention`, `/prevention-backtest`, `/prevention-validate`, `/prevention-log` |
| B7 ACWR · B8 HRR · B12 recovery-cost | `core/training_load.py` | `/acwr`, `/recovery-cost` |
| B9 Sleep debt · B10 Regularity | `core/sleep_metrics.py` | `/sleep-analysis` |
| B11 Behaviour correlation | `core/behaviour.py` | `/behaviour`, `/tag`, `/tags` |
| B13 Realtime stress | (analytics) | `/realtime-stress` |
| B14 VO₂max · B15 CV-age proxy | `core/longevity.py` | `/longevity` |
| B16 Resilience | `core/resilience.py` | `/resilience` |
| B17 Circadian | `core/circadian.py` | `/circadian` |
| B18 DFA-α1 | `core/hrv_spectral.py` | `/dfa` |
| B19 Assessment | `core/assessment.py` | `/assessment` |
| **Delivery** (digest + cooldown) | `core/whoop_digest.py` | `/digest`, `/digest/deliver` |
| **Web cockpit** (7 panels) | `core/whoop_cockpit.py` | `/cockpit` |
| **Slim app** (iOS) | `goose-whoop5` SlimHomeView | renders `/summary` |

**Deferred by design:** B20 AFib (decode-gated on the locked R22 raw-PPG SQI) · R22/K21 decode (locked).
**Runtime tail:** B6 threshold *tuning* awaits real `ill` journal tags; VPS deploy lights up the phone banner.
Acceptance harness: `tests/test_whoop_acceptance.py` asserts each build's contract + safety invariants in CI.

## 4. What our data COULD support (see the roadmap — this is a pointer, not a parallel list)
All of the following — **except the decode-gated AFib screen noted below** — are reproducible from the **HR + RR we
already bank**; each is scoped, prioritised, tagged for feasibility/surface, and given acceptance criteria in
`WHOOP_FUTURE_STATE_PLAN.md` (the single source of truth for
the roadmap). Summarised so nothing reproducible silently disappears between docs:
- **Frequency-domain HRV** (LF, HF, total power, LF:HF) via Lomb-Scargle on the resting RR tachogram — note LF:HF is
  a **descriptive ratio, not a sympatho-vagal balance** measure (see plan).
- **More time-domain + non-linear HRV:** SDNN, pNN50/pNN20, Poincaré SD1/SD2 (SD1≡RMSSD/√2, so SD2/SD1 ratio and DFA
  are the genuinely additive signals).
- **DFA α1** — aerobic (≈0.75) *and* anaerobic (≈0.5) threshold markers; **research-grade and artifact-fragile**.
- **Full-resolution HR curve** (native ~1 Hz, **live windows only**).
- **HR-recovery (HRR)** as a within-person fitness trend (currently per-BJJ-session only).
- **Nocturnal HRV trajectory + sleeping-HR dip / onset**; cardiac drift / decoupling within a session.
- **Circadian/autonomic rhythm** (time-of-day HR/HRV curves, cosinor amplitude/acrophase, HR-dip at night) —
  reproducible and directly relevant to his fixed >9 h sleep-need and Sabbath rhythm; **carried into the plan** (P2).
- **Sleep consistency / regularity** (onset/offset variability) — cheap, universally shipped by competitors.
- **Training-load ACWR** (7 d : 28 d) — injury-risk; **data-gated** (needs the days of coverage).
- **Multi-signal baseline-deviation watch** (personal-baseline deviation — the prevention engine).
- **RR-irregularity screen** (AFib-class) — ⚠️ **blocked on the locked R22 raw-PPG SQI; deferred** (see plan red team).
- **Recovery-vs-load coupling**, **VO₂max estimate** (banded), **wear-time/coverage** analytics.

## 5. What is genuinely LOCKED (needs un-cracked decode)
The proprietary optical (R22/R17) + IMU (K21/K10) frames are **banked raw** (`decoded=FALSE`) but not decoded by any
subscription-free project:
- **SpO₂ / blood oxygen** — R22 optical PPG.
- **Skin / peripheral temperature** — temperature-event / NormalHistory family.
- **Steps / motion / actigraphy / posture** — K21 IMU (workaround: iPhone pedometer, deferred).
- **Sleep staging** (light/deep/REM) — needs fused motion + optical.
- **WHOOP's exact cloud scores** (recovery %, strain, sleep score) — closed models; ours are honest independents.
- **Raw-PPG signal quality** — the waveform an FDA-cleared AFib/SpO₂ pipeline gates on is inside R22, so any
  rhythm-screen is effectively **decode-gated**, not merely experimental.

**Systemic consequence — no motion channel.** Because the IMU is locked, we have **no accelerometer to motion-gate
or artifact-reject** HRV/stress/resp-rate the way every competitor does (their stress/HRV pipelines all use accel to
separate exercise from rest and drop motion epochs). Our only substitute is an **HR-stability heuristic** to detect
rest/sleep windows — a weaker proxy, not an equivalent. Daytime/live HRV metrics inherit this limitation.

Because the raw is preserved, a future R22/K21 decode retroactively unlocks all of the above from history.

*Current-state audit by the research council + Fable second-pass, 2026-07-04. Key files: `GooseSwift/GooseBLEClient.swift`, `rivaflow/rivaflow/core/whoop_analytics.py`, `api/routes/whoop.py`, migration `109_whoop_ingest`.*
